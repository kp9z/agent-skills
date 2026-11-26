# Running in the Claude Code desktop app

Use this mapping when the orchestrator runs in the Claude Code desktop app
(Code tab) instead of Codex. Every other marathon rule, including the
[ownership contract](ownership.md), applies unchanged.

## Tool mapping

| Codex | Claude Code desktop |
|---|---|
| `list_projects`, `create_thread` | `mcp__ccd_session__start_session` (load it with `ToolSearch` first) |
| `wait_threads` | None. End the turn; the app resumes the orchestrator with a `<side-sessions-event>` message |
| follow-up to a worker chat | `SendMessage` with `to` set to the worker's `local_…` session id |
| immediate status snapshot | `mcp__ccd_session_mgmt__list_sessions` with `{"linked": true}` |
| read a worker transcript | `mcp__ccd_session_mgmt__get_session` or `list_events` |
| `[$implement](path)` | `/implement` in the worker prompt, plus the absolute path to `implement/SKILL.md` |

## Dispatch

1. Create the worker checkout yourself before `prepare`, so the ownership
   request has its real path:
   `git worktree add -b ticket/<n> <repo>-worktrees/ticket-<n> <verified integration commit>`.
2. Call `start_session` once per prepared dispatch:
   - `initiation: "user_asked"` (invoking this skill is the user's request for
     parallel worker sessions and for integrating their branches)
   - `context: "fresh"`, `cwd: <worker worktree path>`, `use_worktree: false`
   - `title: "#<n> <issue title>"`, `name: "t<n>"`
   - `prompt`: the worker prompt described in SKILL.md step 4
   - `background`: the repository, marathon scope, integration branch and the
     fact that this worker owns only its ticket
   The app may ask the user to trust a new folder once; wait for that instead
   of retrying.
3. For `attach`, use `worker: {chatId: <local_… id>, hostId: "local"}`. There
   are no cursors, so use `not-created` before the first report and
   `report-<k>` after the worker's k-th report, comparing against the previous
   value.

## Waiting

- Never poll or sleep. After dispatch, end the turn with a short status line.
- The app resumes the orchestrator only when **no** worker is still running,
  so a fast worker's slot stays empty until the slower ones finish their turn.
  Prefer worker pairs of similar size, and refill every free slot at once when
  you wake.
- A report quotes only the start of the worker's summary. Verify the branch,
  commit, checks and issue state yourself before integrating.
- After many reports in a row with no user message, further reports wait for
  the user's next message. Before stopping, record each worker's state and
  ask the user to reply "continue".
- A worker that is waiting for the user's answer is not complete. Report it
  with its session link (`[title](#local_…)`) and defer it as SKILL.md describes.

## Finishing

Workers commit locally on `ticket/<n>`. Never push those branches or open pull
requests without separate authorization. After the queue finishes, offer to
archive the worker sessions; archive them only if the user agrees.
