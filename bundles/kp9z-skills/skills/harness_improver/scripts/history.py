#!/usr/bin/env python3
"""Bounded inspection of saved Codex chat exports and selected rollout files."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys


def unwrap(data):
    if isinstance(data, dict) and "content" in data and "turns" not in data:
        texts = [x.get("text", "") for x in data["content"] if x.get("type") == "text"]
        for text in texts:
            try:
                candidate = json.loads(text)
            except ValueError:
                continue
            if isinstance(candidate, dict) and "turns" in candidate:
                return candidate
    return data


def load(path):
    text = path.read_text()
    try:
        return unwrap(json.loads(text))
    except ValueError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def content_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict)
                         and x.get("type") in ("text", "input_text", "output_text"))
    return ""


def normalize(data):
    events, related, usage = [], set(), None
    page = data.get("page") if isinstance(data, dict) else None
    thread = data.get("thread", {}).get("id") if isinstance(data, dict) else None

    def links(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("threadId", "agentThreadId", "parent_thread_id", "forked_from_id") and isinstance(item, str):
                    related.add(item)
                elif isinstance(item, (dict, list)):
                    links(item)
        elif isinstance(value, list):
            for item in value:
                links(item)

    def add(item, fallback):
        kind = item.get("type", "unknown")
        if kind in ("reasoning", "contextCompaction"):
            return
        links(item)
        if kind == "commandExecution":
            output = item.get("output", {})
            text = item.get("command", "") + "\n" + (output.get("text", "") if isinstance(output, dict) else str(output))
            extra = {"command": item.get("command"), "exit_code": item.get("exitCode"),
                     "duration_ms": item.get("durationMs"),
                     "source_output_chars": output.get("originalChars", len(output.get("text", ""))) if isinstance(output, dict) and "output" in item else None,
                     "output_truncated": output.get("truncated", False) if isinstance(output, dict) else False}
        elif kind in ("agentMessage", "userMessage", "message"):
            text = item.get("text") or content_text(item.get("content", []))
            extra = {"phase": item.get("phase"), "role": item.get("role")}
        elif kind in ("mcpToolCall", "function_call", "custom_tool_call"):
            args = item.get("arguments", item.get("input", ""))
            if isinstance(args, str):
                try:
                    links(json.loads(args))
                except ValueError:
                    pass
            text = str(item.get("tool", item.get("name", ""))) + " " + (args if isinstance(args, str) else json.dumps(args))
            extra = {}
        elif kind in ("function_call_output", "functionCallOutput"):
            text = str(item.get("output", ""))
            extra = {}
        elif kind == "subAgentActivity":
            text = str(item.get("kind", "")) + " " + str(item.get("agentPath", ""))
            extra = {}
        else:
            return
        events.append({"id": item.get("id") or fallback, "kind": kind, "text": text, **extra})

    if isinstance(data, dict) and "turns" in data:
        for turn in reversed(data["turns"]):
            for n, item in enumerate(turn.get("items", [])):
                add(item, f"{turn['id']}:{n}")
    elif isinstance(data, list):
        for n, row in enumerate(data):
            payload = row.get("payload", {})
            if row.get("type") == "session_meta":
                thread = payload.get("id", thread)
                links(payload)
            elif row.get("type") == "response_item":
                add(payload, f"line:{n + 1}")
            elif row.get("type") == "event_msg" and payload.get("type") == "token_count":
                candidate = (payload.get("info") or {}).get("total_token_usage")
                if isinstance(candidate, dict):
                    usage = candidate  # cumulative snapshot: never sum these
    else:
        raise ValueError("Expected read_thread export/MCP envelope or Codex rollout JSONL")
    related.discard(thread)
    return events, {"thread_id": thread, "related_thread_ids": sorted(related), "page": page,
                    "usage": usage, "usage_note": "Latest cumulative snapshot; cached input/reasoning are subsets" if usage else "Unavailable; event/character counts are not billed tokens"}


def bounded(event, chars):
    result = {k: v for k, v in event.items() if k not in ("text", "command")}
    result.update(text=event["text"][:chars], text_chars=len(event["text"]), truncated=len(event["text"]) > chars)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("overview", "search", "event"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--pattern")
    parser.add_argument("--id")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--chars", type=int, default=600)
    args = parser.parse_args()
    if not 1 <= args.limit <= 50 or not 1 <= args.chars <= 10000:
        parser.error("limit must be 1..50; chars must be 1..10000")
    events, meta = normalize(load(args.path))
    if args.action == "overview":
        commands = Counter(e["command"] for e in events if e.get("command"))
        result = dict(meta, events=len(events), event_types=dict(Counter(e["kind"] for e in events)),
                      observed_text_chars=sum(len(e["text"]) for e in events),
                      source_output_chars=sum(e.get("source_output_chars") or 0 for e in events),
                      truncated_output_events=sum(bool(e.get("output_truncated")) for e in events),
                      commands_without_output=sum(e["kind"] == "commandExecution" and e.get("source_output_chars") is None for e in events),
                      failed_commands=sum(e.get("exit_code") not in (None, 0) for e in events),
                      repeated_command_candidates=[{"command": command[:180], "count": count}
                                                   for command, count in commands.most_common(10) if count > 1])
    elif args.action == "search":
        if not args.pattern:
            parser.error("search requires --pattern")
        pattern = re.compile(args.pattern, re.IGNORECASE)
        matches = [e for e in events if pattern.search(e["text"])]
        excerpts = []
        for event in matches[:args.limit]:
            start = max(0, pattern.search(event["text"]).start() - args.chars // 3)
            excerpt = bounded(event, args.chars)
            excerpt["text"] = event["text"][start:start + args.chars]
            excerpt["offset"] = start
            excerpts.append(excerpt)
        result = {"matches": len(matches), "omitted": max(0, len(matches) - args.limit), "events": excerpts}
    else:
        if not args.id:
            parser.error("event requires --id")
        found = next((e for e in events if e["id"] == args.id), None)
        if found is None:
            raise ValueError("Event not found in this export/page")
        result = bounded(found, args.chars)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, re.error) as error:
        print(json.dumps({"error": str(error)}))
        sys.exit(1)
