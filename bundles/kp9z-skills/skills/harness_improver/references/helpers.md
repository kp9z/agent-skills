# Helpers

Python 3 standard library only. Run these from the installed skill directory or use absolute script paths. They emit JSON and never invoke a shell. GitHub access uses the installed authenticated `gh` CLI and the execution environment's network permissions. No helper grants authorization for external writes.

## GitHub issues

```sh
python3 scripts/issues.py --repo OWNER/REPO list --state open --label ready-for-agent
python3 scripts/issues.py --repo OWNER/REPO read 58
python3 scripts/issues.py --repo OWNER/REPO read 58 --full
python3 scripts/issues.py --repo OWNER/REPO dependencies 58
python3 scripts/issues.py --repo OWNER/REPO comment 58 --body-file /tmp/comment.md --expected-updated-at TIMESTAMP
python3 scripts/issues.py --repo OWNER/REPO close 58 --reason completed --body-file /tmp/closure.md --expected-updated-at TIMESTAMP
```

List, comments and dependencies fetch every page. Reads default to bounded excerpts and expose truncation; `--full` returns the complete issue/comments for acceptance review. Dependency state/reason is reported, not interpreted as completed merely because it is closed. Explicit links in bodies still need resolution. Pull requests are excluded from lists.

Writes require an expected issue `updated_at` from a fresh read, checked before mutation. This is an optimistic preflight, not an atomic compare-and-swap: GitHub can change between requests. Comment bodies are passed as JSON on stdin. A content-derived marker suppresses duplicate comments on a serial rerun. Comment creation is not atomic across simultaneous writers; serialize writes per issue. The client verifies delivery after a write error rather than blindly retrying it. If verification also fails, the outcome is unknown; inspect live state before retrying. Closing posts its comment first, then verifies state and reason. An already-matching closure is a no-op. Authentication and write failures return classified errors without dumping raw payloads or credentials. GitHub Enterprise is supported via `--hostname`.

## Bounded history

```sh
python3 scripts/history.py overview /tmp/thread-export.json
python3 scripts/history.py search /tmp/thread-export.json --pattern 'permission|timeout' --limit 8 --chars 600
python3 scripts/history.py event /tmp/thread-export.json --id EVENT_ID --chars 2400
python3 scripts/history.py overview /absolute/path/rollout.jsonl
```

Accepts Codex app `read_thread` JSON, its MCP text-content envelope, or one explicitly selected Codex rollout JSONL file. It does not scan all chats or make network calls. Save the tool response outside model context when supported. Page history with the chat tool; one export is not necessarily the whole chat. Exports may already truncate output: the helper cannot recover missing data. Event/search responses have an overall bounded result count and per-event character limit; overview reports counts, repeated command candidates, related thread IDs and usage records if present. Related IDs are pointers to investigate, not permission to expand scope. Repeated commands are candidates, not waste judgments.

Private reasoning events are omitted. Native cumulative token totals are taken from the latest usage record, not summed across snapshots. Different files/threads need separate accounting. Chat exports without usage return unavailable rather than estimated billing. `event` returns one excerpt, not a full turn. Keep raw history local and exclude it from commits/publication.

## Test results

```sh
python3 scripts/test_results.py /path/to/run.json
python3 scripts/test_results.py /path/to/run.json --log /path/to/test.log --limit 8 --chars 500
python3 scripts/test_results.py --log /path/to/test.log
```

Understands the SkinSense-style runner receipt (`selected`, `executed`, `summary`, `status`, `exitCode`) and extracts bounded compiler/assertion/runner errors from a log, defaulting to `test.log` beside a receipt. It verifies nonempty execution, selection agreement and failures/skips when receipt evidence is complete. Incomplete receipts and log-only input are unverified; a successful build or absence of matched error lines is not a passing test result. It does not execute tests, repair assertions, classify a failure as pre-existing, or retry runners. Extend adapters when another runner's concrete schema is needed.

Run helper checks with `python3 -m unittest discover -s tests`.
