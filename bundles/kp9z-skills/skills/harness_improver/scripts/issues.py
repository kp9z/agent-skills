#!/usr/bin/env python3
"""Paginated issue reads and serialized, verified writes through authenticated gh."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlencode


class IssueError(Exception):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


class Client:
    def __init__(self, repo, hostname="github.com", run=subprocess.run):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise IssueError("input", "Use an explicit OWNER/REPO")
        if not re.fullmatch(r"[A-Za-z0-9.-]+", hostname):
            raise IssueError("input", "Invalid hostname")
        self.root, self.run, self.hostname = "repos/" + repo + "/issues", run, hostname

    def api(self, path, method="GET", body=None, pages=False):
        command = ["gh", "api", "--hostname", self.hostname, path, "--method", method]
        if pages:
            command += ["--paginate", "--slurp"]
        if body is not None:
            command += ["--input", "-"]
        try:
            result = self.run(command, input=json.dumps(body) if body is not None else None,
                              capture_output=True, text=True, timeout=45)
        except FileNotFoundError as error:
            raise IssueError("environment", "Install authenticated gh CLI") from error
        except subprocess.TimeoutExpired as error:
            raise IssueError("timeout", "Request timed out; writes may have reached GitHub") from error
        if result.returncode:
            text = result.stderr.lower()
            kind = ("authentication" if any(x in text for x in ("401", "authentication", "gh auth"))
                    else "permission" if "403" in text else "not_found" if "404" in text
                    else "rate_limit" if "429" in text or "rate limit" in text
                    else "network" if any(x in text for x in ("connect", "network", "resolve"))
                    else "github")
            raise IssueError(kind, "GitHub request failed; inspect auth/network/access without exposing credentials")
        try:
            data = json.loads(result.stdout)
        except ValueError as error:
            raise IssueError("response", "GitHub returned invalid JSON") from error
        if pages:
            if not isinstance(data, list) or any(not isinstance(page, list) for page in data):
                raise IssueError("response", "Expected paginated arrays")
            return [item for page in data for item in page]
        return data

    def issue(self, number):
        return self.api(f"{self.root}/{number}")

    def comments(self, number):
        return self.api(f"{self.root}/{number}/comments?per_page=100", pages=True)

    def dependencies(self, number):
        return self.api(f"{self.root}/{number}/dependencies/blocked_by?per_page=100", pages=True)

    def check(self, number, expected):
        current = self.issue(number)
        if current["updated_at"] != expected:
            raise IssueError("conflict", "Issue changed; refresh and reassess before writing")
        return current

    def comment(self, number, body):
        marker = "<!-- harness-improver:" + hashlib.sha256(body.encode()).hexdigest() + " -->"
        def find():
            return next((c for c in self.comments(number) if marker in c.get("body", "")), None)
        existing = find()
        if existing:
            return {"url": existing["html_url"], "duplicate": True}
        try:
            self.api(f"{self.root}/{number}/comments", "POST", {"body": body + "\n\n" + marker})
        except IssueError as error:
            try:
                delivered = find()
            except IssueError as verification:
                raise IssueError("unknown_outcome", "Comment outcome unknown; inspect live comments before retrying") from verification
            if not delivered:
                raise error
            return {"url": delivered["html_url"], "recovered": True}
        try:
            delivered = find()
        except IssueError as error:
            raise IssueError("unknown_outcome", "Comment sent but verification unavailable; inspect live comments before retrying") from error
        if not delivered:
            raise IssueError("unknown_outcome", "Comment was not observed; inspect live comments before retrying")
        return {"url": delivered["html_url"], "verified": True}

    def close(self, number, body, expected, reason):
        current = self.issue(number)
        if current["state"] == "closed":
            if current.get("state_reason") != reason:
                raise IssueError("conflict", "Already closed with a different reason")
            return {"state": "closed", "state_reason": reason, "already_closed": True}
        if current["updated_at"] != expected:
            raise IssueError("conflict", "Issue changed; refresh before closing")
        comment = self.comment(number, body)
        try:
            self.api(f"{self.root}/{number}", "PATCH", {"state": "closed", "state_reason": reason})
        except IssueError as error:
            try:
                current = self.issue(number)
            except IssueError as verification:
                raise IssueError("unknown_outcome", "Closure outcome unknown; inspect live issue before retrying") from verification
            if current["state"] != "closed" or current.get("state_reason") != reason:
                raise error
        try:
            current = self.issue(number)
        except IssueError as error:
            raise IssueError("unknown_outcome", "Closure sent but verification unavailable; inspect live issue before retrying") from error
        if current["state"] != "closed" or current.get("state_reason") != reason:
            raise IssueError("unknown_outcome", "Requested closure not verified")
        return {"state": current["state"], "state_reason": reason, "url": current["html_url"], "comment": comment}


def summary(issue):
    return {key: issue.get(key) for key in ("number", "title", "state", "state_reason", "updated_at", "html_url")}


def excerpt(value, limit):
    value = value or ""
    return {"text": value[:limit], "chars": len(value), "truncated": len(value) > limit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--hostname", default="github.com")
    commands = parser.add_subparsers(dest="action", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--state", choices=("open", "closed", "all"), default="open")
    listing.add_argument("--label", action="append", default=[])
    for action in ("read", "dependencies", "comment", "close"):
        command = commands.add_parser(action)
        command.add_argument("number", type=int)
        if action == "read":
            command.add_argument("--full", action="store_true")
        if action in ("comment", "close"):
            command.add_argument("--body-file", required=True, type=Path)
            command.add_argument("--expected-updated-at", required=True)
        if action == "close":
            command.add_argument("--reason", choices=("completed", "not_planned"), required=True)
    args = parser.parse_args()
    client = Client(args.repo, args.hostname)
    if getattr(args, "number", 1) < 1:
        raise IssueError("input", "Issue number must be positive")
    if args.action == "list":
        query = urlencode({"state": args.state, "labels": ",".join(args.label), "per_page": 100})
        result = [dict(summary(i), labels=[x["name"] for x in i.get("labels", [])])
                  for i in client.api(client.root + "?" + query, pages=True) if "pull_request" not in i]
    elif args.action == "dependencies":
        result = [summary(i) for i in client.dependencies(args.number)]
    elif args.action == "read":
        issue, comments = client.issue(args.number), client.comments(args.number)
        result = dict(summary(issue), labels=[x["name"] for x in issue.get("labels", [])],
                      blocked_by=[summary(i) for i in client.dependencies(args.number)], comment_count=len(comments))
        result["body"] = issue.get("body") if args.full else excerpt(issue.get("body"), 2000)
        selected = comments if args.full else comments[-5:]
        result["comments"] = [{"id": c["id"], "url": c["html_url"],
                               "body": c.get("body") if args.full else excerpt(c.get("body"), 500)} for c in selected]
        result["comments_omitted"] = len(comments) - len(selected)
    else:
        body = args.body_file.read_text()
        if not body.strip():
            raise IssueError("input", "Comment body must not be empty")
        if args.action == "comment":
            client.check(args.number, args.expected_updated_at)
            result = client.comment(args.number, body)
        else:
            result = client.close(args.number, body, args.expected_updated_at, args.reason)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (IssueError, OSError) as error:
        print(json.dumps({"error": getattr(error, "kind", "environment"), "message": str(error)}))
        sys.exit(1)
