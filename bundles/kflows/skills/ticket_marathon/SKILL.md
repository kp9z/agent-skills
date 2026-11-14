---
name: ticket_marathon
description: Orchestrate dependency-ready tickets in separate chats, sequentially in batches of three, with scheduled or user-requested continuous execution.
disable-model-invocation: true
---

# Ticket marathon

The main chat is an **orchestrator only**: inspect open tickets, resolve dependencies, plan the order, delegate, wait, verify returned results, and manage the selected continuation mode. Tickets are already prepared for autonomous implementation. Never implement a ticket in the main chat, including when delegation fails.

Explicit invocation authorizes creating a new Codex chat for each selected ticket to execute the installed `implement` skill, and, in scheduled mode, scheduling continuations of this same marathon. This authorization carries into scheduled continuations; it does not enable implicit invocation for unrelated requests. Read worker results through the chat tools; workers return their results in their own final response.

## Choose the continuation mode

Default to **scheduled mode**: run a batch of up to three tickets, then resume
4 hours 30 minutes after batch completion.

A user request such as "don't schedule anymore, run until finish" selects
**continuous mode**. Record the selected mode with the queue state. Continue
sequentially into the next batch immediately while eligible work remains;
create no automation. On a switch from scheduled to continuous, disable only
this marathon's known pending continuation and verify the result before continuing.
If it cannot be disabled, report the blocker to avoid duplicate orchestrators.
Preserve orchestration-only execution, separate per-ticket chats, dependency
refreshes, result verification, and one active implementation at a time in both modes.

## Establish the queue

1. Read the target project's `AGENTS.md`, configured tracker conventions, and triage mapping. Use that project's configured issue repository as the source of ticket status, not this skill collection. Verify that `implement` and its required testing and review skills are installed. If dependencies or tracker configuration are missing, report what is needed before starting.
2. Honor an explicitly supplied ticket list, parent spec, or filter. Otherwise use all open implementation tickets labeled `ready-for-agent`. Fetch every results page. Exclude parent specs, tracking-only issues, and tickets marked `needs-triage`, `needs-info`, `ready-for-human`, or `wontfix`. Preserve this scope across continuations; new tickets qualify only if they match the original scope. Dependencies outside that scope are constraints, not permission to expand it.
3. Record the repository path, current branch, queue scope, continuation mode, and any existing marathon continuation ID in the chat. Inspect working-tree changes and preserve unrelated work. Resume on the recorded branch; if it has changed unexpectedly or another marathon run is active for this checkout, stop for reconciliation before dispatching work. Preserve each dispatched ticket's worker chat ID, host ID, wait cursor, and current phase across continuations so an existing worker is monitored rather than duplicated.

## Run one batch

Dispatch at most **three distinct tickets per batch**, strictly one at a time. Select the next ticket after the current worker completes or is safely deferred under **User-action grace period** below.

For each slot:

1. Refresh the queue. Read a candidate's full body and comments and resolve its native GitHub `blocked_by` dependencies plus explicit `Blocked by:` links. Fetch the blockers' current states, including blockers in other repositories. A ticket is eligible only when every blocker is confirmed complete; a closed-as-not-planned issue is not evidence of completion. Treat unreadable, ambiguous, or cyclic dependencies as blocked. Never start a dependent based on an uncommitted change or an expectation that its blocker will finish later.
2. Choose an eligible ticket in dependency order, breaking ties by ascending issue number. If none is eligible, end the batch and apply the continuation rules below.
3. State the issue number and title, then discover the Codex app's `list_projects`, `create_thread`, and `wait_threads` tools. Select the matching project and create a **new chat for only that ticket**, using the recorded local checkout and branch. Begin `create_thread.prompt` with a direct skill invocation, `[$implement](<absolute path to the installed implement/SKILL.md>)`, followed by the issue URL. Resolve the installed skill path from available project or user-level skills; keep the worker’s working directory set to the recorded checkout. The worker must invoke that skill as its implementation workflow; if no Skill tool is available, read and execute the linked skill directly. Pass the repository path, branch, relevant dependency evidence, and any unrelated working-tree changes. Preserve the skill's testing and review requirements, complete tracker updates with a concise completion explanation and commit reference, and confirm closure. The worker must return the invoked skill path, acceptance-criteria results, checks, review outcome, commit references, issue status, and any unfinished phase or blocker. Keep scheduling and queue selection in the orchestrator. Do not pass the whole queue or launch parallel ticket implementations. If chat creation is unavailable or fails, report the blocker and stop scheduling; do not fall back to implementation in the main chat.
4. Count the ticket against the three-ticket limit when its worker is dispatched, including if it is later deferred. Record the returned chat and host IDs and follow **Wait for the worker** below. A successful dispatch or a progress update is not completion. If it needs user action, follow **User-action grace period**; for other failures, stop the batch and report the exact unfinished step with a link to its chat. Retain the worker identity and phase rather than creating a replacement or taking over its work.
5. For a worker reporting completion, verify its evidence against live issue status and the recorded branch's commits. Confirm the required checks and review succeeded and the issue is closed as completed before using it to unblock another ticket. If evidence is missing or inconsistent, report the unfinished verification and stop the batch. Deferred workers remain unfinished and cannot unblock dependents. The orchestrator summarizes the result; the worker owns implementation, fixes, commits, and tracker completion.

## Wait for the worker

Use `wait_threads` as a completion wait, with one target containing the current worker's `threadId`, `hostId`, and latest `afterCursor` when available.

- Use `timeoutMs: 120000`, the currently supported two-minute maximum, when runtime instructions permit. If a stricter runtime limit applies, use that shorter bound. A requested three-minute wait cannot be passed as `180000` to the current tool; use supported bounded waits instead. Completion or required attention can return early; worker commentary does not wake the wait. Reserve `timeoutMs: 0` for a user-requested immediate status check, a single recovery snapshot after an interrupted wait, or the grace-period recheck below.
- On a timeout with the worker still running, save the returned cursor and renew the same bounded wait directly. Retain only compact worker state; unchanged progress needs no analysis or narration. A timeout alone is not a failure or a reason to dispatch another worker.
- Use the wait result as the status source while work runs. Do not interleave `read_thread`, `list_threads`, issue refreshes, Git checks, or messages asking the worker for progress. Read the worker transcript only when a completion or attention result lacks evidence needed for verification or intervention.
- Stay silent on unchanged status. Report meaningful completion, failures, or required user action. If higher-priority runtime instructions require an update, keep it brief and use the latest wait result without an extra status fetch.
- Bounded waits still require renewal; do not assume ending the orchestrator turn will automatically resume it when a separate chat finishes. If waiting is unavailable or errors persist, preserve the worker identity and report the monitoring blocker. Use the existing continuation rules rather than creating a separate polling automation or claiming completion.

## User-action grace period

When a worker requires user input or approval, report the exact action and link its chat. Record the first observation time and a deadline **5 minutes (300 seconds)** later, together with the ticket, worker identity, cursor, and unfinished phase. Elapsed time never grants approval.

Give the user until that deadline. Use interruptible sleeps bounded by runtime limits while the worker needs attention; repeated `wait_threads` calls can return immediately in that state. Avoid status reads during the grace period. If new input arrives, assess it and resume normal completion waiting when the worker is running. Otherwise make one compact worker-state recheck at the deadline; preserve the original deadline across interruptions and continuations.

If the action is still outstanding, defer that ticket and try the next eligible ticket in the same batch, using any remaining slots. Before switching, confirm the deferred worker is inactive and the checkout has no unfinished changes or operations from its ticket. Preserve unrelated baseline changes. If safe handoff cannot be confirmed, stop the batch and report the checkout blocker. The orchestrator must not discard, stash, commit, or finish the worker's partial implementation to free the checkout.

Keep deferred tickets open and their dependents blocked. Exclude unresolved deferred tickets from selection so they do not consume another five-minute wait or another worker chat. Retain them as outstanding work even if their labels change. Revisit their existing workers only after the required action is resolved, and serialize their resumption with other workers on this checkout. If no other eligible ticket exists, apply the continuation rules below.

## Continue or finish

Refresh the scoped queue after each batch, including batches with fewer than three tickets.

- **Empty queue, with no deferred unfinished tickets:** report completion and disable this marathon's pending continuation, if any. Stop scheduling.
- **Eligible tickets remain, continuous mode:** begin the next batch immediately after refreshing dependencies and verifying the previous results. Do not create an automation or end the run merely because three tickets completed.
- **Tickets remain, scheduled mode:** schedule the next batch **4 hours 30 minutes (270 minutes) after this batch finishes**. A partial batch does not justify starting another immediately. This also applies when tickets are temporarily waiting on external dependencies.
- **User action is required:** a ticket-specific request uses the five-minute grace period and permits other eligible tickets to proceed. In continuous mode, continue immediately while independent eligible work remains; in scheduled mode, schedule further batches. If only user-action-blocked tickets and their dependents remain, or the blocker affects the whole marathon (such as unavailable tracker access or an unsafe checkout), report the blockers and stop scheduling until resolved. In continuous mode, if only externally blocked dependencies remain, report them and stop without scheduling or repeatedly refreshing an unchanged queue. In scheduled mode, if a dependency-only wait is unchanged across three consecutive runs, report the blocking issues and stop scheduling until the user resumes. Distinguish this blocked state from an empty queue.

In scheduled mode only, use the Codex app's `automation_update` tool, discovering its current schema before scheduling. Create or update a heartbeat attached to the current chat. Keep exactly one pending continuation for this marathon, reuse its ID, and set its next wakeup relative to batch completion. Prefer a one-shot wakeup when supported; otherwise use a 270-minute interval and re-anchor it after every batch. Verify the saved schedule and record the ID and next run time. If the tool cannot express or save the delay, report that scheduling is blocked rather than claiming a continuation exists or substituting a different cadence.

The saved prompt must explicitly invoke `$ticket_marathon` at its installed path and include the repository path, recorded branch, original queue scope, scheduled mode, continuation ID when known, all unfinished tickets and phases with their worker chat IDs, host IDs, and wait cursors, any deferred user actions with their original grace deadlines, and the consecutive unchanged dependency-wait count. Direct it to remain an orchestrator only, run one batch by delegating each new ticket to a new chat and waiting for its result using **Wait for the worker**, apply **User-action grace period**, refresh live issue state, preserve sequential dependency checks, and apply **Continue or finish** when the batch ends. Monitor existing unfinished workers instead of dispatching those tickets again; skip unresolved deferred workers while independent tickets can proceed. Stay quiet on unchanged dependency waits; report completed work, failures, required user action, and final completion.

End each productive run with completed ticket links, worker chat links, and commit references, remaining or blocked tickets, and either the verified next run time in scheduled mode or the completion/blocker outcome in continuous mode. Workers commit locally; pushing or opening pull requests requires separate authorization.
