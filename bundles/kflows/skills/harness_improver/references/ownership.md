# Local resource ownership

This cooperative Python 3 contract coordinates one local host/user. Install the
`harness_improver` and `ticket_marathon` directories as siblings in
`~/.agents/skills/`. Keep helpers global; project adapters may locate these
installed scripts but must not vendor a second registry implementation. Run
`python3 -m unittest discover -s ~/.agents/skills/harness_improver/tests` and
`python3 -m unittest discover -s ~/.agents/skills/ticket_marathon/tests` after
installing or updating. No provider, chat API or device is contacted by the CLI.

## Registry and identity

Default registry: `~/.local/state/codex-harness/ownership.json`. All participating
orchestrators and workers must share this exact location. An explicit
`--registry /absolute/path` overrides `HARNESS_OWNERSHIP_REGISTRY`, which overrides
the default. Use a persistent local filesystem with working `flock`, atomic
rename and fsync; network filesystems are unsupported. Registry paths are resolved
through symlinks. Do not replace the lock file or switch registry locations during
active work. Keep registry/parent permissions private to the participating user;
returned opaque tokens are local cooperative capabilities, not authentication.

Choose one stable local host ID for all workers on the machine (the Codex tool's
host ID), and use actual chat IDs after attachment. Different spellings of a host
ID or separate registry copies cannot coordinate a shared device. Checkout IDs
are `checkout:/absolute/repo/path`, resolved through symlinks and subdirectories to
the Git worktree root. Simulator IDs are `simulator:HOST/DEVICE-UUID`; UUID case is
normalized. Use the device UUID, not its mutable display name. `output:/absolute/path`
reserves shared build/output directories through path aliases; reserve parent and
child output directories as one agreed canonical root, since overlapping trees
are not hierarchical locks. Hard-linked or bind-mounted registry/path aliases are
outside this contract. Independent Git worktrees and device UUIDs remain usable.

## Public JSON interface

Run `python3 ~/.agents/skills/harness_improver/scripts/ownership.py [--registry PATH]
claim|release|reconcile` with one JSON object on stdin. Exit 0 means success; exit 2
means blocked with bounded JSON diagnostics. The API is `Registry(path).operate(op,
request)`; callers catch `OwnershipError` and OS errors, preserving state.

Example request (replace fixture IDs and paths with assigned facts):

```json
{
  "schemaVersion": 1,
  "owner": {"chatId": "worker-chat", "hostId": "local-host"},
  "checkout": "/absolute/assigned-checkout", "branch": "codex/ticket",
  "phase": "implementation", "pendingAction": "edit assigned files",
  "resources": ["checkout:/absolute/assigned-checkout"],
  "evidence": ["handoff://worker/bounded-reference"],
  "budgetReceipts": ["file:///absolute/existing-authoritative-receipt.json"]
}
```

Claims return the canonical group plus an opaque `token` and monotonically
increasing `generation`. A retry with identical canonical request fields returns
the same grant. Different metadata or a partial overlap is a conflict; an entire
group succeeds or leaves no new claims. Conflicts disclose only resource, worker
identity and generation. Requests carry at most 16 resources and 8 references of
512 characters per reference list. The registry holds at most 32 active groups and
128 durable dispatch identities and is capped at 1 MiB. At capacity, stop for
reviewed archival/migration; no automatic pruning of dispatch history is safe.
Raw transcripts, credentials, token counts or receipt bodies do not belong here.

`release` adds the returned `token` and `generation` to the request. Only that
current owner can release requested members of its group. Phase/pending action
are explicit context, not liveness signals. Retain the remaining group during a
partial handoff. An idle chat, pending approval, absent process or elapsed time
never releases anything. Use release, then the recipient's claim; if interrupted
between them the resource is free only because of the explicit release, and the
recipient must still win a claim before use. A competing winner requires a new
reviewed handoff. There is no unconditional takeover operation.

`reconcile` adds `expected`, a bounded array of
`{"resource": "CANONICAL-ID", "owner": {"chatId": "...", "hostId": "..."}, "generation": 1}`
entries in canonical resource order. Empty means the caller expects no claims on
its requested resources. Compare returned observations against saved orchestration
state. A disagreement blocks and reports current observations and registry byte
fingerprint; it never silently updates the orchestrator. Consume bounded handoff
references and point `budgetReceipts` at the *existing authoritative* receipts.
References are supplied attestations, not fetched or verified by this helper.
It neither keeps a second request budget nor authorizes/spends/retries calls.
Reconciliation does not establish test success, review approval or issue closure.

## Interrupted writes, restart and migration

The persistent `.lock` serializes whole transactions across processes. `.pending`
is a fsynced replacement payload; atomic rename publishes it. If publication is
interrupted, the last published JSON remains authoritative, and the pending file
blocks normal operations. A failure after successful atomic publication may have
committed: inspect/reconcile before retrying. Never delete lock/state to unblock.

For a pending write, stop affected effects and compare saved orchestration state,
the last published registry, worker return and existing evidence. Invoke
`reconcile` with matching `expected`, a `reviewer` identity, nonempty `evidence`,
`recoverInterrupted: true`, and the current `expectedFingerprint`. Under the lock,
this removes only the pending replacement and preserves the published facts.
A mismatch or missing review/reference blocks recovery. For initial publication,
the empty-file fingerprint represents an absent registry; review must confirm no
worker effects occurred. Pending chat creation remains a prepared dispatch after
recovery: locate and attach the returned chat rather than dispatching again.
A worker whose process disappeared still owns its group; explicit owner release
with the recorded token/generation is required before another worker can claim.

Malformed/unsupported registry JSON, denied access and ambiguous handoffs fail
closed. Preserve registry/pending files and user work, correct permissions, and
use reviewed reconciliation. Corrupt JSON cannot be repaired by the CLI: restore
only a reviewed complete ownership snapshot that accounts for all possibly active
workers, with affected effects stopped. A stale backup that predates a grant is
insufficient. If completeness cannot be proved, keep affected resources blocked
and use distinct isolated resources. Existing tokens remain necessary for release.

Schema version 1 is the initial format; missing or unsupported versions are
rejected without reset. For a future migration, stop participating effects,
preserve the original registry, review every active grant/dispatch and migrate
under the same lock while retaining identities, generations, tokens, cursor and
authorization references. There is no automatic old-state reset/migration. An
existing manually coordinated marathon needs an explicit reviewed inventory and
claims before adopting this registry. Merging stale saved state is not migration.

## Dispatch and existing-worker resume

Use `ticket_marathon/scripts/runner.py` as described in that skill's
[ownership integration](../../ticket_marathon/references/ownership.md). It records
intent *before* chat creation and attaches the actual worker identity afterward.
Workers recheck ownership before every file/device phase, including after any
approval or interruption. Resume carries the saved cursor and routine-testing
authorization reference; it grants no OS or app permission and resolves no new
material testing-scope decision. Respect actual environment approval prompts.

The in-process `Marathon.resume(request, effect)` keeps the registry lock during
the supplied operation; keep effects short, avoid reentering registry operations,
and do not invoke a remote chat wait inside that callback. A CLI resume is a
point-in-time check, so participating callers must serialize handoffs with their
operations and recheck immediately before work. Registry locks cannot fence an
external editor or an already running device command. Retain source checks and
independent verification. This contract does not promise prevention of
nonparticipating edits or measured savings. Preserve pending approvals, receipts,
unrelated files, no-reset/no-stash rules and separately authorized tracker writes,
pushes and PRs.
