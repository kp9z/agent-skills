---
name: ticket_marathon
description: Run dependency-ready tickets in parallel Codex chats with isolated worktrees and verified integration.
disable-model-invocation: true
---

# Ticket marathon

The main chat is an **orchestrator only**. It owns queue selection, dispatch,
waiting, and integration. Each ticket has one worker chat that runs the
installed `implement` skill and owns implementation, fixes, checks, review,
commits, and tracker completion. Explicit invocation authorizes creating those
chats and sending their assignment, ownership, and integration follow-ups.
Run continuously in the current chat without a schedule.

## Establish the queue

1. Read the project’s `AGENTS.md`, tracker conventions, and triage mapping.
   Verify that `implement` and its required testing and review skills are
   installed. Use the project’s configured tracker.
2. Honor the user’s ticket list, parent spec, or filter. Otherwise fetch all
   pages of open implementation tickets labeled `ready-for-agent`. Exclude
   parent specs, tracking-only issues, and tickets marked `needs-triage`,
   `needs-info`, `ready-for-human`, or `wontfix`. Preserve this scope across
   resumes. Dependencies outside scope constrain eligibility.
3. Record the repository, scope, stable integration worktree and branch, and
   latest verified integration commit. Keep the integration worktree exclusive
   and preserve unrelated changes. On resume, reconcile unexpected branch
   changes or an existing orchestrator before dispatching. Keep each worker’s
   chat and host IDs, cursor, base commit, checkout, branch, phase, pending
   action, and reserved resources so it can be resumed in place.

## Select and dispatch

Fill available worker slots as tickets become ready. Start with two concurrent
runners when resources permit. Honor a user-specified limit and account for
available worktrees, wait-tool capacity, and exclusive runtime resources.

1. Refresh the queue before filling a slot. Read each candidate’s full issue
   and comments. Resolve native GitHub `blocked_by` dependencies and explicit
   `Blocked by:` links, including across repositories. Require completed
   blockers and verified integration of the changes the candidate needs.
   An ambiguous, cyclic, unreadable, or closed-as-not-planned blocker leaves
   the ticket ineligible.
2. Screen candidates for foreseeable merge conflicts with active workers,
   deferred workers that may resume, and completed work awaiting integration.
   Use acceptance criteria, a quick source search, and known changed paths to
   check for competing edits or interacting behavior in production code, shared
   contracts, tests, and generated files.
   **When you foresee a conflict, run those tickets one at a time.** Wait for
   the earlier change to land, then reassess and start the next ticket from the
   latest verified integration commit. Fill other slots with independent
   tickets. Among those, prefer the least overlap and break ties by ascending
   ticket number after honoring dependencies and explicit user priorities.
3. Give **every worker its own worktree and branch** based on the latest
   verified integration commit. Assign separate build and evidence paths and
   exclusive Simulator, device, or backend resources as needed. Phases that
   need the same exclusive resource can proceed in turn after ownership handoff.
   Carry forward authorized **Device Hub** use. Use the
   [ownership contract](references/ownership.md) to prepare the complete resource
   group before chat creation, attach the actual chat, and confirm ownership
   before worker file or device operations.
4. State the issue and title. Discover `list_projects`, `create_thread`, and
   `wait_threads`, select the matching project, and create a chat for that
   ticket only. Begin its prompt with
   `[$implement](<absolute path to the installed implement/SKILL.md>)` and
   the issue URL. Include the assigned worktree, branch, exact base, dependency
   evidence, resources, and the **Worker testing authorization** verbatim.
   If a skill tool is unavailable, have the worker read the installed skill
   directly. Require a completion comment with the verified commit and a
   readback of issue closure. Ask the worker to return the skill path,
   acceptance results, test and review receipts, exact commit, closure state,
   and any unfinished phase. Record its identity and attachment. If dispatch
   or attachment fails, reconcile the existing attempt through the ownership
   contract.

## Worker testing authorization

Include this instruction in every worker prompt.

> The ticket's acceptance criteria and testing requirements establish the agreed testing scope. Treat the public testing boundaries (seams) specified there as pre-agreed for `implement` and `tdd`. State the seams you will use, then proceed with routine tests within that scope without requesting another confirmation. Choose ordinary test cases and implementation details autonomously, following project conventions. Preserve TDD, required checks and independent review. Ask only when a material testing-scope decision remains unresolved by the ticket, project instructions or existing user authorization, or when an actual environment permission is required; explain the exact missing decision or permission.

If an existing worker only needs confirmation already covered by this
authorization, pass it to that same chat and resume through the ownership
contract. Defer genuinely unresolved decisions or permissions.

## Wait and handle blockers

Use `wait_threads` as a bounded completion wait for active workers and
resumable deferred workers. Pass each thread’s `threadId`, `hostId`, and latest
`afterCursor`. Use the supported timeout within runtime limits. On a timeout,
save each returned cursor and renew the wait. Use an immediate snapshot for a
user status request or a targeted recovery check. Read a worker transcript only
when a completion or attention result lacks information needed to act.

On completion, verify the worker’s evidence and integrate or record the
unfinished verification. On a blocker, report the exact action and link its
chat. Defer it promptly with its identity, cursor, pending action, partial work,
and claims. A deferred worker can resume at any time. Keep its worktree and
resources reserved until explicit release. Continue with independent tickets
whose claims do not overlap. Return to the same worker when the block clears.

Refill free slots after completion or deferral. Report meaningful progress and
required user action. If waiting or dispatch remains unavailable, preserve
worker identities and report which work cannot proceed.

## Integrate verified results

One orchestrator integrates one result at a time. Before integration, verify
the live issue is closed as completed, the worker branch contains the exact
clean commit, and required tests and reviews passed. Keep incomplete results
from unblocking dependents.

1. Preview the merge of the exact ticket commit against the current verified
   integration tip without changing either branch or checkout. Fast-forward
   when the worker’s verified commit contains that tip. For a clean divergent
   merge, inspect automatically combined code where the two changes interact,
   confirm the merged tree matches the preview, and run the project’s required
   checks for the combined result.
2. If the preview conflicts, preserve both commits. With ownership released
   and reassigned, return the conflict to the ticket’s **original chat** on a
   fresh integration worktree and branch based on the exact integration tip.
   Have that worker merge the exact ticket commit there. Leave the orchestrator’s
   integration worktree clean. Follow the
   [merge handoff](references/merge-handoff.md) for the context and evidence.
3. Land the verified result only when it still matches the current integration
   tip. Keep the tip stable during an active conflict resolution where
   practical while independent implementations continue. If the tip advances,
   preview again and verify any new overlap before landing. Confirm the
   required commits and checks on the resulting integration revision before
   dispatching dependents. Keep partial or unintegrated worktrees until the work
   is preserved and their claims are explicitly released.

## Finish or resume

Refresh eligibility after each completion, integration, or deferral. While
runners are active, keep waiting. While eligible work can progress, keep
dispatching. When neither condition holds, report whether the scoped queue is
complete or blocked. Include completed issue links, worker chat links, commit
references, and the exact outstanding blocker or unfinished phase. Resume
through the recorded workers after the user resolves a blocker. Workers commit
locally. Pushing or opening pull requests requires separate authorization.
