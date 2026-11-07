---
name: ticket_marathon
description: Orchestrate dependency-ready tickets in separate chats, sequentially in batches of three, resuming after 4 hours 30 minutes until the queue is empty.
disable-model-invocation: true
---

# Ticket marathon

The main chat is an **orchestrator only**: inspect open tickets, resolve dependencies, plan the order, delegate, wait, verify returned results, and schedule continuations. Tickets are already prepared for autonomous implementation. Never implement a ticket in the main chat, including when delegation fails.

Explicit invocation authorizes creating a new Codex chat for each selected ticket to execute the installed `implement` skill, and scheduling continuations of this same marathon. This authorization carries into scheduled continuations; it does not enable implicit invocation for unrelated requests. Read worker results through the chat tools; workers return their results in their own final response.

## Establish the queue

1. Read the target project's `AGENTS.md`, configured tracker conventions, and triage mapping. Use that project's configured issue repository as the source of ticket status, not this skill collection. Verify that `implement` and its required testing and review skills are installed. If dependencies or tracker configuration are missing, report what is needed before starting.
2. Honor an explicitly supplied ticket list, parent spec, or filter. Otherwise use all open implementation tickets labeled `ready-for-agent`. Fetch every results page. Exclude parent specs, tracking-only issues, and tickets marked `needs-triage`, `needs-info`, `ready-for-human`, or `wontfix`. Preserve this scope across continuations; new tickets qualify only if they match the original scope. Dependencies outside that scope are constraints, not permission to expand it.
3. Record the repository path, current branch, queue scope, and any existing marathon continuation ID in the chat. Inspect working-tree changes and preserve unrelated work. Resume on the recorded branch; if it has changed unexpectedly or another marathon run is active for this checkout, stop for reconciliation before dispatching work. Preserve each dispatched ticket's worker chat ID, host ID, wait cursor, and current phase across continuations so an existing worker is monitored rather than duplicated.

## Run one batch

Dispatch at most **three distinct tickets per run**, strictly one at a time. Wait for the current ticket's worker to finish implementation, checks, review, commit, and tracker updates before selecting the next.

For each slot:

1. Refresh the queue. Read a candidate's full body and comments and resolve its native GitHub `blocked_by` dependencies plus explicit `Blocked by:` links. Fetch the blockers' current states, including blockers in other repositories. A ticket is eligible only when every blocker is confirmed complete; a closed-as-not-planned issue is not evidence of completion. Treat unreadable, ambiguous, or cyclic dependencies as blocked. Never start a dependent based on an uncommitted change or an expectation that its blocker will finish later.
2. Choose an eligible ticket in dependency order, breaking ties by ascending issue number. If none is eligible, end the batch and apply the continuation rules below.
3. State the issue number and title, then discover the Codex app's `list_projects`, `create_thread`, and `wait_threads` tools. Select the matching project and create a **new chat for only that ticket**, using the recorded local checkout and branch. Pass the issue URL, repository path, branch, relevant dependency evidence, and any unrelated working-tree changes. Explicitly instruct the worker to invoke `$implement` at its installed path (read and execute the skill directly if no Skill tool is available), preserve its testing and review requirements, complete tracker updates with a concise completion explanation and commit reference, and confirm closure. The worker must return acceptance-criteria results, checks, review outcome, commit references, issue status, and any unfinished phase or blocker. Keep scheduling and queue selection in the orchestrator. Do not pass the whole queue or launch parallel ticket implementations. If chat creation is unavailable or fails, report the blocker and stop scheduling; do not fall back to implementation in the main chat.
4. Count the ticket against the three-ticket limit when its worker is dispatched. Record the returned chat and host IDs and wait for that worker with `wait_threads`, carrying its latest cursor into subsequent bounded waits. A successful dispatch or a progress update is not completion. If it needs user input or cannot finish, stop the batch and report the exact unfinished step with a link to its chat; retain the worker identity and phase rather than creating a replacement or taking over its work.
5. After the worker returns, verify its completion evidence against live issue status and the recorded branch's commits. Confirm the required checks and review succeeded and the issue is closed as completed before using it to unblock another ticket. If evidence is missing or inconsistent, report the unfinished verification and stop the batch. The orchestrator summarizes the result; the worker owns implementation, fixes, commits, and tracker completion.

## Continue or finish

Refresh the scoped queue after each batch, including batches with fewer than three tickets.

- **Empty queue:** report completion and disable this marathon's pending continuation, if any. Stop scheduling.
- **Tickets remain:** schedule the next batch **4 hours 30 minutes (270 minutes) after this batch finishes**. A partial batch does not justify starting another immediately. This also applies when tickets are temporarily waiting on external dependencies.
- **User action is required:** for missing requirements, unavailable access, dependency cycles, or a failed ticket that needs intervention, report the blocker and stop scheduling until resolved. If a dependency-only wait is unchanged across three consecutive runs, report the blocking issues and stop scheduling until the user resumes. Distinguish this blocked state from an empty queue.

Use the Codex app's `automation_update` tool, discovering its current schema before scheduling. Create or update a heartbeat attached to the current chat. Keep exactly one pending continuation for this marathon, reuse its ID, and set its next wakeup relative to batch completion. Prefer a one-shot wakeup when supported; otherwise use a 270-minute interval and re-anchor it after every batch. Verify the saved schedule and record the ID and next run time. If the tool cannot express or save the delay, report that scheduling is blocked rather than claiming a continuation exists or substituting a different cadence.

The saved prompt must explicitly invoke `$ticket_marathon` at its installed path and include the repository path, recorded branch, original queue scope, continuation ID when known, any unfinished ticket and phase with its worker chat ID, host ID, and wait cursor, and the consecutive unchanged dependency-wait count. Direct it to remain an orchestrator only, run one batch by delegating each ticket to a new chat and waiting for its result, refresh live issue state, preserve sequential dependency checks, reschedule from batch completion only while work remains, and stop when the queue is empty or intervention is required. Monitor any existing unfinished worker instead of dispatching that ticket again. Stay quiet on unchanged dependency waits; report completed work, failures, required user action, and final completion.

End each productive run with completed ticket links, worker chat links, and commit references, remaining or blocked tickets, and the verified next run time or reason scheduling stopped. Workers commit locally; pushing or opening pull requests requires separate authorization.
