---
name: ticket_marathon
description: Implement dependency-ready tickets sequentially in batches of three, resuming after 4 hours 30 minutes until the queue is empty.
disable-model-invocation: true
---

# Ticket marathon

Explicit invocation authorizes executing the installed `implement` skill once per ticket and scheduling continuations of this same marathon. Read and execute that skill's instructions directly if no Skill tool is available. This authorization carries into scheduled continuations; it does not enable implicit invocation for unrelated requests.

## Establish the queue

1. Read the target project's `AGENTS.md`, configured tracker conventions, and triage mapping. Use that project's configured issue repository as the source of ticket status, not this skill collection. Verify that `implement` and its required testing and review skills are installed. If dependencies or tracker configuration are missing, report what is needed before starting.
2. Honor an explicitly supplied ticket list, parent spec, or filter. Otherwise use all open implementation tickets labeled `ready-for-agent`. Fetch every results page. Exclude parent specs, tracking-only issues, and tickets marked `needs-triage`, `needs-info`, `ready-for-human`, or `wontfix`. Preserve this scope across continuations; new tickets qualify only if they match the original scope. Dependencies outside that scope are constraints, not permission to expand it.
3. Record the repository path, current branch, queue scope, and any existing marathon continuation ID in the chat. Inspect working-tree changes and preserve unrelated work. Resume on the recorded branch; if it has changed unexpectedly or another marathon run is active for this checkout, stop for reconciliation before editing.

## Run one batch

Process at most **three distinct tickets per run**, strictly one at a time. Complete implementation, checks, review, commit, and tracker updates for the current ticket before selecting the next.

For each slot:

1. Refresh the queue. Read a candidate's full body and comments and resolve its native GitHub `blocked_by` dependencies plus explicit `Blocked by:` links. Fetch the blockers' current states, including blockers in other repositories. A ticket is eligible only when every blocker is confirmed complete; a closed-as-not-planned issue is not evidence of completion. Treat unreadable, ambiguous, or cyclic dependencies as blocked. Never start a dependent based on an uncommitted change or an expectation that its blocker will finish later.
2. Choose an eligible ticket in dependency order, breaking ties by ascending issue number. If none is eligible, end the batch and apply the continuation rules below.
3. State the issue number and title, then execute `$implement` for **only that ticket**. Preserve its testing and review requirements and any necessary clarification steps. Do not launch parallel ticket implementations or pass the whole queue to it.
4. Count the ticket against the three-ticket limit as soon as implementation starts. After its acceptance criteria, required checks, review, and commit are complete, post a concise completion explanation with the commit reference and close the issue using tracker conventions. Confirm closure before using it to unblock another ticket. If implementation, verification, review, commit, or tracker updates cannot finish, stop the batch and report the exact unfinished step; retain enough context to resume that ticket rather than starting it again.

## Continue or finish

Refresh the scoped queue after each batch, including batches with fewer than three tickets.

- **Empty queue:** report completion and disable this marathon's pending continuation, if any. Stop scheduling.
- **Tickets remain:** schedule the next batch **4 hours 30 minutes (270 minutes) after this batch finishes**. A partial batch does not justify starting another immediately. This also applies when tickets are temporarily waiting on external dependencies.
- **User action is required:** for missing requirements, unavailable access, dependency cycles, or a failed ticket that needs intervention, report the blocker and stop scheduling until resolved. If a dependency-only wait is unchanged across three consecutive runs, report the blocking issues and stop scheduling until the user resumes. Distinguish this blocked state from an empty queue.

Use the Codex app's `automation_update` tool, discovering its current schema before scheduling. Create or update a heartbeat attached to the current chat. Keep exactly one pending continuation for this marathon, reuse its ID, and set its next wakeup relative to batch completion. Prefer a one-shot wakeup when supported; otherwise use a 270-minute interval and re-anchor it after every batch. Verify the saved schedule and record the ID and next run time. If the tool cannot express or save the delay, report that scheduling is blocked rather than claiming a continuation exists or substituting a different cadence.

The saved prompt must explicitly invoke `$ticket_marathon` at this repo-local path and include the repository path, recorded branch, original queue scope, continuation ID when known, any unfinished ticket and phase, and the consecutive unchanged dependency-wait count. Direct it to run one batch, refresh live issue state, preserve sequential dependency checks, reschedule from batch completion only while work remains, and stop when the queue is empty or intervention is required. Stay quiet on unchanged dependency waits; report completed work, failures, required user action, and final completion.

End each productive run with completed ticket links and commit references, remaining or blocked tickets, and the verified next run time or reason scheduling stopped. Commit locally; pushing or opening pull requests requires separate authorization.
