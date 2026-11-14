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
refreshes, result verification, and one newly dispatched implementation at a time in both modes. A blocked worker
remains outstanding; follow **Blocked workers and isolation** before dispatching
independent work that could overlap its resumption.

## Establish the queue

1. Read the target project's `AGENTS.md`, configured tracker conventions, and triage mapping. Use that project's configured issue repository as the source of ticket status, not this skill collection. Verify that `implement` and its required testing and review skills are installed. If dependencies or tracker configuration are missing, report what is needed before starting.
2. Honor an explicitly supplied ticket list, parent spec, or filter. Otherwise use all open implementation tickets labeled `ready-for-agent`. Fetch every results page. Exclude parent specs, tracking-only issues, and tickets marked `needs-triage`, `needs-info`, `ready-for-human`, or `wontfix`. Preserve this scope across continuations; new tickets qualify only if they match the original scope. Dependencies outside that scope are constraints, not permission to expand it.
3. Record the repository path, current branch, queue scope, continuation mode, and any existing marathon continuation ID in the chat. Inspect working-tree changes and preserve unrelated work. Resume on the recorded branch; if it has changed unexpectedly or another marathon run is active for this checkout, stop for reconciliation before dispatching work. Preserve each dispatched ticket's worker chat ID, host ID, wait cursor, current phase, checkout, branch, pending action, and reserved shared resources across continuations so an existing worker is monitored rather than duplicated.

## Run one batch

Dispatch at most **three distinct tickets per batch**, strictly one at a time. Select the next ticket after the current worker completes or is safely deferred under **Blocked workers and isolation** below.

For each slot:

1. Refresh the queue. Read a candidate's full body and comments and resolve its native GitHub `blocked_by` dependencies plus explicit `Blocked by:` links. Fetch the blockers' current states, including blockers in other repositories. A ticket is eligible only when every blocker is confirmed complete; a closed-as-not-planned issue is not evidence of completion. Treat unreadable, ambiguous, or cyclic dependencies as blocked. Never start a dependent based on an uncommitted change or an expectation that its blocker will finish later.
2. Choose an eligible ticket in dependency order, breaking ties by ascending issue number. If none is eligible, end the batch and apply the continuation rules below.
3. State the issue number and title, then discover the Codex app's `list_projects`, `create_thread`, and `wait_threads` tools. Select the matching project and create a **new chat for only that ticket**, using the recorded checkout and branch, or an isolated checkout selected under **Blocked workers and isolation**. Begin `create_thread.prompt` with a direct skill invocation, `[$implement](<absolute path to the installed implement/SKILL.md>)`, followed by the issue URL. Resolve the installed skill path from available project or user-level skills; keep the worker’s working directory set to its assigned checkout. The worker must invoke that skill as its implementation workflow; if no Skill tool is available, read and execute the linked skill directly. Pass the repository path, branch, relevant dependency evidence, and any unrelated working-tree changes. Preserve the skill's testing and review requirements, complete tracker updates with a concise completion explanation and commit reference, and confirm closure. The worker must return the invoked skill path, acceptance-criteria results, checks, review outcome, commit references, issue status, and any unfinished phase or blocker. Keep scheduling and queue selection in the orchestrator. Do not pass the whole queue or deliberately dispatch tickets in parallel; account for a deferred worker’s possible resumption using the isolation rules. If chat creation is unavailable or fails, report the blocker and stop scheduling; do not fall back to implementation in the main chat.
4. Count the ticket against the three-ticket limit when its worker is dispatched, including if it is later deferred. Record the returned chat and host IDs and follow **Wait for the worker** below. A successful dispatch or a progress update is not completion. If it needs user action, follow **Blocked workers and isolation**; for other ticket-specific blockers or failures, preserve the exact unfinished step and follow the same deferral and isolation rules. Stop dispatching only when a blocker prevents all remaining eligible work. Retain the worker identity and phase rather than creating a replacement or taking over its work.
5. For a worker reporting completion, verify its evidence against live issue status and its assigned branch's commits, then follow **Integration** below. Confirm the required checks and review succeeded and the issue is closed as completed before using it to unblock another ticket. If evidence is missing or inconsistent, preserve the unfinished verification as a ticket-specific blocker and continue independent eligible work under the isolation rules. Deferred workers remain unfinished and cannot unblock dependents. The orchestrator summarizes the result; the worker owns implementation, fixes, commits, and tracker completion.

## Wait for the worker

Use `wait_threads` as a completion wait, with one target for the current worker, except when monitoring resumable deferred workers as described below. Each target contains its `threadId`, `hostId`, and latest `afterCursor` when available.

- Use `timeoutMs: 120000`, the currently supported two-minute maximum, when runtime instructions permit. If a stricter runtime limit applies, use that shorter bound. A requested three-minute wait cannot be passed as `180000` to the current tool; use supported bounded waits instead. Completion or required attention can return early; worker commentary does not wake the wait. Reserve `timeoutMs: 0` for a user-requested immediate status check, a single recovery snapshot after an interrupted wait, or a targeted recheck after a deferred worker’s required action is resolved.
- On a timeout with the worker still running, save the returned cursor and renew the same bounded wait directly. Retain only compact worker state; unchanged progress needs no analysis or narration. A timeout alone is not a failure or a reason to dispatch another worker.
- Use the wait result as the status source while work runs. Do not interleave `read_thread`, `list_threads`, issue refreshes, Git checks, or messages asking the worker for progress. Read the worker transcript only when a completion or attention result lacks evidence needed for verification or intervention.
- Stay silent on unchanged status. Report meaningful completion, failures, or required user action. If higher-priority runtime instructions require an update, keep it brief and use the latest wait result without an extra status fetch.
- Bounded waits still require renewal; do not assume ending the orchestrator turn will automatically resume it when a separate chat finishes. If waiting is unavailable or errors persist, preserve the worker identity and report the monitoring blocker. Use the existing continuation rules rather than creating a separate polling automation or claiming completion.

## Blocked workers and isolation

When a worker reports a ticket-specific blocker, including pending user input or
approval, report the exact action and link its chat once. Immediately record it
as deferred and refresh dependencies to find another independent eligible ticket;
continue without a fixed grace period. A ticket-specific blocker
alone does not end the marathon. Preserve the worker's chat and host IDs, cursor,
unfinished phase, pending approval, checkout, branch, partial work, and resource
ownership. Keep its ticket unfinished and its dependents blocked. Reuse that
worker after resolution instead of dispatching a replacement.

Before dispatching independent work:

- Treat an approval-blocked worker as able to resume at any time. Reserve its
  checkout even if currently clean. Leave its files, Git operations, and pending
  approval intact; do not stash, discard, commit, reset, or finish its partial work
  to free the checkout. An attention state is not proof that it cannot resume.
- Use a separate checkout/worktree and branch for independent work when existing
  authorization and environment permissions allow it. Base it on the last verified
  integration commit, excluding the blocked ticket's partial work. Record the new
  worker's assigned path and branch. If isolation cannot be established, report
  the specific permission, tool, or resource blocker rather than changing the
  reserved checkout or claiming no independent ticket exists.
- Isolate shared runtime resources as well as files: assign a distinct Simulator
  and build/output paths where needed. Record device ownership and pass it to the
  worker. Never run simultaneous commands against the same checkout or Simulator,
  including commands from a resumed worker. If the project requires a specific
  shared device, reserve it for its existing owner; independent work may proceed
  only through phases that do not use it until handoff is confirmed.
- Carry forward explicit user authorization for routine Device Hub use within the
  requested testing/debugging scope. Name **Device Hub** accurately in worker
  instructions. A skill cannot grant persistent app/OS permissions or bypass an
  approval prompt; preserve a blocked worker's pending prompt, report the exact
  requested approval, and continue eligible work with isolated resources.

Keep unresolved deferred tickets out of selection even if their labels change;
they remain outstanding work. When their required action resolves, reconcile the
existing worker and resource ownership before resuming shared phases. Use its
saved identity and cursor, and include outstanding workers in bounded completion
waits when the tool supports multiple targets. Apply the same timeout and silence
rules as **Wait for the worker**. Avoid polling unchanged attention states.

## Integration

A worker owns its implementation, fixes, checks, review, commits, and tracker
completion. Record a stable integration checkout/branch separately from each
worker checkout. Verify each returned commit and required evidence before
integration. Apply verified commits to the integration branch only when that
checkout is clean and exclusively available, using the authorized local Git
workflow. Never integrate into an approval-blocked worker's reserved checkout.
If no integration checkout is available, use an authorized separate one or report
the specific integration blocker; preserve completed commits for later.

Confirm the commits are present on the integration branch, resolve any conflicts
through the owning worker or a separately authorized integration task, and run
checks warranted by the integrated result. Only then may dependent tickets start,
based on that verified integration commit. A closed issue or a commit on an
unintegrated isolated branch alone cannot unblock them. Retain worktrees with
partial work, pending approvals, or unintegrated commits; clean them up only after
ownership is released and all work is preserved.

## Continue or finish

Refresh the scoped queue after each batch, including batches with fewer than three tickets.

- **Empty queue, with no deferred unfinished tickets:** report completion and disable this marathon's pending continuation, if any. Stop scheduling.
- **Eligible tickets remain, continuous mode:** begin the next batch immediately after refreshing dependencies and verifying the previous results. Do not create an automation or end the run merely because three tickets completed.
- **Tickets remain, scheduled mode:** schedule the next batch **4 hours 30 minutes (270 minutes) after this batch finishes**. A partial batch does not justify starting another immediately. This also applies when tickets are temporarily waiting on external dependencies.
- **User action is required:** defer ticket-specific blockers immediately under **Blocked workers and isolation** and proceed with independent eligible tickets. In continuous mode, continue immediately while independent eligible work remains; in scheduled mode, schedule further batches. If only user-action-blocked tickets and their dependents remain, or the blocker affects the whole marathon (such as unavailable tracker access or an inability to isolate required resources), report the blockers and stop scheduling until resolved. In continuous mode, if only externally blocked dependencies remain, report them and stop without scheduling or repeatedly refreshing an unchanged queue. In scheduled mode, if a dependency-only wait is unchanged across three consecutive runs, report the blocking issues and stop scheduling until the user resumes. Distinguish this blocked state from an empty queue.

In scheduled mode only, use the Codex app's `automation_update` tool, discovering its current schema before scheduling. Create or update a heartbeat attached to the current chat. Keep exactly one pending continuation for this marathon, reuse its ID, and set its next wakeup relative to batch completion. Prefer a one-shot wakeup when supported; otherwise use a 270-minute interval and re-anchor it after every batch. Verify the saved schedule and record the ID and next run time. If the tool cannot express or save the delay, report that scheduling is blocked rather than claiming a continuation exists or substituting a different cadence.

The saved prompt must explicitly invoke `$ticket_marathon` at its installed path and include the repository path, recorded branch, original queue scope, scheduled mode, continuation ID when known, all unfinished tickets and phases with their worker chat IDs, host IDs, and wait cursors, each deferred action and pending approval, worker checkout/branch, shared resource ownership, and the verified integration branch/commit, and the consecutive unchanged dependency-wait count. Direct it to remain an orchestrator only, run one batch by delegating each new ticket to a new chat and waiting for its result using **Wait for the worker**, apply **Blocked workers and isolation**, refresh live issue state, preserve sequential dependency checks, and apply **Continue or finish** when the batch ends. Monitor existing unfinished workers instead of dispatching those tickets again; skip unresolved deferred workers while independent tickets can proceed. Stay quiet on unchanged dependency waits; report completed work, failures, required user action, and final completion.

End each productive run with completed ticket links, worker chat links, and commit references, remaining or blocked tickets, and either the verified next run time in scheduled mode or the completion/blocker outcome in continuous mode. Workers commit locally; pushing or opening pull requests requires separate authorization.
