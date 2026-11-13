"""Behavioral checks; GitHub writes use a fake gh process, never the network."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


issues, history, results = (module(name) for name in ("issues", "history", "test_results"))


class FakeGH:
    def __init__(self):
        self.issue = {"number": 58, "title": "Sound", "state": "open", "state_reason": None,
                      "updated_at": "t0", "html_url": "https://example.test/58"}
        self.comments, self.calls = [], []
        self.lose_post = self.lose_patch = False

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        path, method = command[4], command[command.index("--method") + 1]
        payload = json.loads(kwargs["input"]) if kwargs.get("input") else None
        if method == "POST":
            self.comments.append({"body": payload["body"], "html_url": "https://example.test/comment"})
            self.issue["updated_at"] = "t1"
            if self.lose_post:
                return SimpleNamespace(returncode=1, stdout="", stderr="connection lost")
            data = self.comments[-1]
        elif method == "PATCH":
            self.issue.update(payload)
            if self.lose_patch:
                return SimpleNamespace(returncode=1, stdout="", stderr="connection lost")
            data = self.issue
        elif "/comments?" in path:
            data = [self.comments[:1], self.comments[1:]]
        elif "/dependencies/" in path:
            data = [[{"number": 57, "state": "closed", "state_reason": "not_planned"}], []]
        else:
            data = self.issue
        return SimpleNamespace(returncode=0, stdout=json.dumps(data), stderr="")


class IssueTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeGH()
        self.client = issues.Client("owner/repo", run=self.fake)

    def writes(self):
        return [call for call in self.fake.calls if call[0][call[0].index("--method") + 1] != "GET"]

    def test_comments_fetch_all_pages(self):
        self.fake.comments = [{"body": "first"}, {"body": "second"}]
        self.assertEqual(len(self.client.comments(58)), 2)
        self.assertIn("--paginate", self.fake.calls[0][0])
        self.assertIn("--slurp", self.fake.calls[0][0])

    def test_stale_state_prevents_mutation(self):
        with self.assertRaises(issues.IssueError) as error:
            self.client.close(58, "Done", "old", "completed")
        self.assertEqual(error.exception.kind, "conflict")
        self.assertEqual(self.writes(), [])

    def test_comment_uses_stdin_and_serial_rerun_deduplicates(self):
        body = "Literal $(touch /tmp/should-not-exist) `command`\nsecond line"
        self.client.comment(58, body)
        result = self.client.comment(58, body)
        self.assertTrue(result["duplicate"])
        self.assertEqual(len(self.writes()), 1)
        command, kwargs = self.writes()[0]
        self.assertNotIn(body, command)
        self.assertTrue(json.loads(kwargs["input"])["body"].startswith(body))
        self.assertFalse(kwargs.get("shell", False))

    def test_lost_comment_response_is_verified_without_reposting(self):
        self.fake.lose_post = True
        self.assertTrue(self.client.comment(58, "Checkpoint")["recovered"])
        self.assertEqual(len(self.writes()), 1)

    def test_close_comment_then_mutation_and_reason_verification(self):
        result = self.client.close(58, "Explicit closure", "t0", "completed")
        self.assertEqual(result["state_reason"], "completed")
        self.assertEqual([c[0][c[0].index("--method") + 1] for c in self.writes()], ["POST", "PATCH"])
        self.client.close(58, "Explicit closure", "old", "completed")
        self.assertEqual(len(self.writes()), 2)

    def test_lost_close_response_is_verified_without_retry(self):
        self.fake.lose_patch = True
        self.assertEqual(self.client.close(58, "Done", "t0", "completed")["state"], "closed")
        self.assertEqual(len(self.writes()), 2)

    def test_not_planned_reason_is_preserved(self):
        self.assertEqual(self.client.dependencies(58)[0]["state_reason"], "not_planned")

    def test_unavailable_post_write_verification_is_unknown_not_retried(self):
        original = self.fake.__call__
        def interrupted(command, **kwargs):
            if self.fake.comments and "/comments?" in command[4]:
                return SimpleNamespace(returncode=1, stdout="", stderr="connection lost")
            return original(command, **kwargs)
        client = issues.Client("owner/repo", run=interrupted)
        with self.assertRaises(issues.IssueError) as error:
            client.comment(58, "Checkpoint")
        self.assertEqual(error.exception.kind, "unknown_outcome")
        self.assertEqual(len(self.writes()), 1)

    def test_failed_comment_prevents_closing(self):
        original = self.fake.__call__
        def denied(command, **kwargs):
            if command[command.index("--method") + 1] == "POST":
                return SimpleNamespace(returncode=1, stdout="", stderr="HTTP 403")
            return original(command, **kwargs)
        client = issues.Client("owner/repo", run=denied)
        with self.assertRaises(issues.IssueError):
            client.close(58, "Checkpoint", "t0", "completed")
        self.assertEqual(self.fake.issue["state"], "open")
        self.assertEqual(self.fake.comments, [])

    def test_closed_reason_conflict_does_not_write(self):
        self.fake.issue.update(state="closed", state_reason="not_planned")
        with self.assertRaises(issues.IssueError):
            self.client.close(58, "Done", "t0", "completed")
        self.assertEqual(self.writes(), [])

    def test_permission_error_classified_without_raw_payload(self):
        def denied(*args, **kwargs):
            return SimpleNamespace(returncode=1, stdout="", stderr="HTTP 403 sensitive details")
        with self.assertRaises(issues.IssueError) as error:
            issues.Client("owner/repo", run=denied).issue(58)
        self.assertEqual(error.exception.kind, "permission")
        self.assertNotIn("sensitive details", str(error.exception))

    def test_invalid_repo_never_invokes_process(self):
        with self.assertRaises(issues.IssueError):
            issues.Client("owner/repo;command", run=self.fake)
        self.assertEqual(self.fake.calls, [])


class HistoryTests(unittest.TestCase):
    def test_envelope_related_links_and_private_reasoning(self):
        export = {"thread": {"id": "parent"}, "page": {"hasMore": True}, "turns": [{"id": "turn", "items": [
            {"id": "private", "type": "reasoning", "text": "secret reasoning"},
            {"id": "cmd", "type": "commandExecution", "command": "test", "exitCode": 1},
            {"type": "subAgentActivity", "kind": "started", "agentThreadId": "child"}]}]}
        data = history.unwrap({"content": [{"type": "text", "text": json.dumps(export)}]})
        events, meta = history.normalize(data)
        self.assertEqual(meta["related_thread_ids"], ["child"])
        self.assertTrue(meta["page"]["hasMore"])
        self.assertNotIn("secret reasoning", json.dumps(events))

    def test_cumulative_usage_is_latest_not_sum(self):
        rows = [{"type": "event_msg", "payload": {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": n, "cached_input_tokens": n // 2}}}} for n in (100, 250)]
        _, meta = history.normalize(rows)
        self.assertEqual(meta["usage"]["input_tokens"], 250)
        self.assertEqual(meta["usage"]["cached_input_tokens"], 125)

    def test_huge_turn_search_is_bounded_and_finds_late_match(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "export.json"
            path.write_text(json.dumps({"turns": [{"id": "t", "items": [
                {"type": "agentMessage", "id": str(n), "text": "x" * 100000 + " timeout"} for n in range(4)]}]}))
            output = subprocess.check_output([sys.executable, str(ROOT / "scripts/history.py"), "search", str(path),
                                              "--pattern", "timeout", "--limit", "2", "--chars", "120"], text=True)
            result = json.loads(output)
            self.assertEqual(result["matches"], 4)
            self.assertEqual(result["omitted"], 2)
            self.assertLess(len(output), 1000)
            self.assertIn("timeout", result["events"][0]["text"])

    def test_native_jsonl_loads_and_missing_usage_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rollout.jsonl"
            path.write_text(json.dumps({"type": "session_meta", "payload": {"id": "thread"}}) + "\n" +
                            json.dumps({"type": "response_item", "payload": {"type": "function_call", "name": "exec", "arguments": "{}"}}))
            events, meta = history.normalize(history.load(path))
            self.assertEqual(len(events), 1)
            self.assertIsNone(meta["usage"])


class ResultTests(unittest.TestCase):
    def receipt(self, root, **overrides):
        data = {"selected": ["testA"], "executed": ["testA"], "exitCode": 0,
                "status": "passed", "summary": {"failedTests": 0, "skippedTests": 0}}
        data.update(overrides)
        path = root / "run.json"
        path.write_text(json.dumps(data))
        return path

    def test_complete_matching_receipt_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(results.inspect(self.receipt(Path(temp)))["verification"], "passed")

    def test_failed_in_test_name_is_not_a_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "test.log").write_text("Test Case '-[Tests testFailedRequestIsHandled]' started.\n"
                                           "Test Case '-[Tests testFailedRequestIsHandled]' passed (0.01 seconds).\n")
            self.assertEqual(results.inspect(self.receipt(root))["verification"], "passed")

    def test_actual_assertion_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "test.log").write_text("Test Case '-[Tests testSomething]' failed (0.01 seconds).\n")
            report = results.inspect(self.receipt(root, exitCode=65, status="failed", summary={"failedTests": 1, "skippedTests": 0}))
            self.assertEqual(report["failure_kind"], "test_assertion")
            self.assertEqual(report["verification"], "not_passed")

    def test_zero_execution_and_skip_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            for values in ({"executed": []}, {"summary": {"failedTests": 0, "skippedTests": 1}}, {"executed": ["other"]}):
                self.assertEqual(results.inspect(self.receipt(Path(temp), **values))["verification"], "not_passed")

    def test_incomplete_receipt_and_log_only_are_unverified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "test.log"
            log.write_text("BUILD SUCCEEDED\n")
            self.assertEqual(results.inspect(log=log)["verification"], "unverified")
            path = root / "run.json"
            path.write_text('{"status":"passed","exitCode":0}')
            self.assertEqual(results.inspect(path)["verification"], "unverified")

    def test_compiler_errors_are_bounded_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "test.log"
            log.write_text("a.swift:12:3: error: " + "x" * 2000 + "\n" + "a.swift:14:4: error: another\n")
            result = results.inspect(log=log, limit=1, chars=80)
            self.assertEqual(result["failure_kind"], "compiler")
            self.assertEqual(len(result["errors"][0]["text"]), 80)
            self.assertEqual(result["additional_error_lines"], 1)


if __name__ == "__main__":
    unittest.main()
