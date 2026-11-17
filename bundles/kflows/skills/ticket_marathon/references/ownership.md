# Ownership at the chat-tool boundary

Use the installed sibling `harness_improver` contract. Read its
[operations/recovery guide](../../harness_improver/references/ownership.md) when
installing, migrating, handing off or recovering ownership. All workers and the
orchestrator use the same discovered registry; a saved chat status never releases
resources. No new scheduler or automation is introduced.

## Dispatch

Use `python3 ~/.agents/skills/ticket_marathon/scripts/runner.py --registry PATH
prepare|attach|resume|reassign` with a bounded JSON request on stdin. Errors return
exit 2 with a recoverable JSON reason; keep the current worker and unfinished phase.
The Python `Marathon(path).dispatch(request, create_worker)` performs the same
prepare/create/attach sequence with a supplied chat-tool boundary. It never calls
a chat service itself. Do not use bare `create_thread` before preparing ownership.

1. Select an eligible ticket under the existing marathon rules. Choose a stable
   `dispatchId` unique to this marathon/ticket, e.g. `marathon-id:139`. Record the
   assigned checkout/branch and exact resources; no device is needed for a helper
   ticket. Construct the ownership request with the current orchestrator chat/host
   as `owner`, an initial cursor string such as `not-created`, and
   `authorizationRef` pointing at the existing user routine-testing authorization.
   Include the required worker testing authorization verbatim in the actual prompt.
2. Call `prepare`. Only `status: prepared` authorizes the *single* chat creation
   attempt for this dispatch. It reserves the whole group and persists intent.
   `existing_worker` means follow the stored actual worker identity/cursor.
   `pending_dispatch` means creation may already have happened: inspect the exact
   attempt/returned chat, then attach it; never create a replacement. A group
   conflict leaves no new claims and requires isolation or explicit handoff.
3. Call the existing Codex `create_thread` tool once, using the assigned checkout
   and branch and direct installed implement invocation. Pass registry location,
   preparation identity, phase, pending action and resource group in the prompt.
   Instruct the worker to wait for attachment before file/device operations.
   Preserve the actual returned chat ID, host ID and cursor. Use a known initial
   cursor sentinel if the create response supplies no cursor, then advance it from
   the first bounded wait result. Chat creation is not completion.
4. Call `attach` with the original preparation request, its `token`/`generation`,
   `worker: {chatId, hostId}` from the actual result, and `workerCursor`. It rotates
   credentials, transfers the group to that worker, and records identity/cursor/
   authorization atomically. Deliver the attached ownership credentials and cursor
   to that existing worker via the authorized follow-up tool. Cross-host attachment
   is blocked because this is a local registry; choose local workers/resources or
   explicitly solve remote coordination outside this contract.
5. If creation/attachment fails or delivery is unknown, retain the preparation.
   Recover the specific chat identity, then attach once. With confirmed no chat
   created, the coordinator may explicitly release its claim, but the dispatch ID
   remains a tombstone; use a reviewed new attempt ID only after reconciling all
   prior effects. Never remove dispatch history to retry an ambiguous creation.

## Resume, handoff and waiting

Before any existing worker file/device operation, use `resume` with its attached
owner, checkout/branch, resources for that operation, token/generation,
`dispatchId`, **current saved cursor**, `authorizationRef`, phase and pending
 action. A match returns `resumable`; otherwise stop the affected operation and
reconcile saved state. `nextCursor` may advance the cursor after an actual bounded
wait observation, using the previous cursor as the compare condition. Never
replace the saved cursor with a stale snapshot. Preserve pending approval actions.
The in-process `resume(request, effect)` guards a short cooperating effect under
the lock; CLI permits are point-in-time checks and require operational
serialization of handoffs. These APIs confer no permission to execute new work.

Deferral keeps claims. For an explicit phone handoff, the current worker releases
only its Simulator member using current credentials, retaining its checkout. The
recipient must then claim/prepare its own entire group on an isolated checkout.
A late original worker resume with the released phone is rejected; it can resume
only still-owned resources. Reconcile release evidence before updating saved
orchestration state. Do not free resources because a chat is idle or needs input.

To resume that **same chat** on a new clean checkout after partial work is preserved,
explicitly release its entire previous group, then call `reassign` with its current
attached credentials/identity/cursor/authorization and the new checkout/branch and
resource group. It atomically claims that group and rotates credentials, preserving
worker identity, cursor and authorization. If another owner blocks the new group,
no new claim is retained. A stale saved owner/token/generation cannot resume it.
Retain any still-reserved dirty original checkout until an explicit approved
preservation/handoff decision, without reset/stash/cleanup.

Keep existing bounded wait rules and separate check/review/closure obligations.
Update the orchestrator's durable worker record from actual attachment/resume
results. Include current registry, dispatch ID, credentials, chat/host, cursor,
checkout/branch, phase/pending action and authorization reference on continuation.
Request-budget references point to existing authoritative receipts, never to a new
counter. Reconciliation disagreements stop affected work; no automatic live retry
or acceptance inference from chat status is allowed.

## Disposable demonstration

`HARNESS_DEMO_RECEIPT=/tmp/handoff-demo.json python3 -m unittest discover -s
~/.agents/skills/ticket_marathon/tests` executes the actual dispatch/resume API
with fake chat/device effects and disposable Git repositories. The #120/#122-shaped
case retains a dirty checkout, releases the fake phone, rejects late device reuse,
reassigns the original worker to a clean checkout, rejects stale state, and releases
all fixture resources. The before observation is an uncoordinated fake-device
overlap; after observations count registry conflicts, explicit releases, duplicate
dispatches and fake effects. These are fixture results, not claims about preventing
nonparticipating edits or savings on real marathons. Request receipt URIs are mocks;
no #125 receipt or request budget is changed.

## Fixed verification input

For opt-in disposable verification, use the sibling harness-improver
[snapshot guide](../../harness_improver/references/snapshots.md). Retain the integration
checkout claim while explicitly releasing the Simulator for the snapshot group.
Review the fixed snapshot, then validate its content mapping at integration; direct
verification keeps its existing source detector and completion checks.
