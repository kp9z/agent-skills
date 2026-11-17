# Fixed source verification

Use the standalone `harness_improver/scripts/snapshot.py` helper without invoking
the audit skill. Its public JSON CLI supports `run`, `map`, `release`, and `cleanup`.
SkinSense exposes the same CLI through `scripts/ticket_runner.py snapshot`; use
`scripts/verify_snapshot.py` for its existing XCTest selection/filter adapter.
Direct `scripts/test.sh` verification retains its original source-change detector.

## Run and transfer

Provide an explicit `source` checkout, `revision` commit, ancestor `baseline`, new
canonical `destination` outside source, `owner: {chatId, hostId}`, shared `registry`,
optional `simulator` UUID, `inputs` array, `selection` description and `command`
argv. Execution uses no shell. Commands must produce the existing runner receipt
format under `build/results/runs/*/run.json`; zero/missing/mismatched execution
never passes. SkinSense forwards its ordinary selection and filter options to its
existing runner. The `build/` exclusion is the existing SkinSense runner policy,
not a receipt-supplied exclusion. Build/cache/result output stays within the
snapshot's `build/`; keep arbitrary supplied commands within the same contract.

Recheck the attached source worker through marathon `resume` before preparation.
If the worker owns the Simulator, explicitly release only that member first;
retain the integration checkout. The snapshot then claims its new output area,
creates an independent detached clone (not a user worktree), and claims that
checkout and Simulator atomically through #139 before invoking the command.
An existing claim, including one by the same chat under a different group, blocks
execution. Never infer a transfer or silently adopt another grant. Actual device,
filesystem and network permissions still apply.

The default is the selected committed revision, even when the original working
tree contains unrelated edits. Supply `inputs` only when working bytes are needed:
repeat exact repository-relative individual paths for dirty tracked files,
tracked deletions or nonignored untracked files. Each selected file replaces the
revision's version; unrelated working files stay behind. Missing/duplicate paths,
directories, ignored files, credential filenames, unsafe paths and selected
symlinks fail explicitly. Commit symlink changes when needed. Required inputs are
the caller's explicit responsibility; a helper cannot infer an unmentioned source
file. Review the recorded complete content inventory before using the result.
No stash/reset, original checkout writes, credential import or request-budget
operation occurs. Original edits during execution do not change the snapshot.

The receipt records canonical original/snapshot checkouts, revision/baseline,
content paths/modes/SHA-256, source identities before/after, selected inputs,
selection, test receipt paths and hashes, setup/wall time, and source bytes.
Installed helpers pinned by `docs/agents/snapshot-verification-installation.json`
are verified and copied into `globals/` for snapshot adapter execution. Their
recorded original paths and exact hashes remain part of source identity; validate
the real installation when accepting evidence at integration. Output paths and
Python bytecode are outside the source set. Mutation of snapshot source through
collection or review is rejected on recapture; transient edits reverted between
checks and nonparticipating editors remain outside the cooperative guarantee.

Every explicitly selected path must also be nonignored under the completed snapshot
ignore policy; a changed `.gitignore` cannot hide a selected input from identity.

## Review and integrate

Retain the snapshot and its copied helpers unchanged through independent review.
Reviewers capture the actual snapshot identity before review and supply their
normal independent judgment, scopes, ticket and durable reference. `map` takes
`run` (the snapshot receipt), `target` checkout and `reviews` (absolute review JSON
paths). It recomputes the snapshot, verifies passing pinned test receipts and
content-equivalent target bytes/baseline, checks revision ancestry, and pins review
bytes and the actual local report bytes. Remote reviews require a retained local report
export for this mapping; ordinary direct completion still accepts URI references.
Put the returned object in the ordinary completion manifest's `provenance`.
Keep required test receipts, independent scopes and all acceptance evidence in the
manifest. The existing completion validator recomputes both checkouts, compares
the mapping's target against current source, and checks receipt/review/report inventories
and hashes. An unsupported claim, changed target/test/review input, different
baseline or scope gap cannot become verified. Committing identical content remains
valid. Local attestations are unsigned; check reviewer independence and inventory
completeness against the agreed spec.

## Retain and recover

All snapshots are protected evidence by default. `cleanup` is a conservative,
repeatable retention preview: it preserves active, failed, protected and referenced
evidence and reports test status separately. It neither releases resources nor
removes source, clones or user worktrees. Existing runner retention sees protected
XCTest artifacts. Preserve snapshot directories, mapping, test/review records and
completion manifest together; a summary alone is insufficient.

`release` requires `run` and the exact recorded `owner`. It releases only that
run's recorded grants with their current token/generation, then retains all files.
It is repeatable after recorded success. Release before final `map`, because
release updates the run bytes and invalidates a prior mapping hash. Failed runs
also require explicit release. A release error is a lifecycle error, never a test
result. If a process stops between registry publication and receipt persistence,
stop effects and reconcile the shared registry against the run/returned grant
and actual owner; preserve the current published credentials. Do not delete
registry state, retry unknown effects, clean failed diagnostics or claim an idle
worker's resources. Use the #139 reviewed interrupted-write recovery protocol.
Do not remove a snapshot while any tests/reviews/completion evidence references it.

## Checks and comparison

Run `python3 -m unittest discover -s ~/.agents/skills/harness_improver/tests` and
SkinSense's focused adapter/completion checks. The public CLI fixture suite uses
disposable Git repositories and stub execution, including source/snapshot edits,
content mismatches, changed review bytes, selections, aliases/spaces, secrets,
setup/runner errors and recoverable ownership. `SNAPSHOT_DEMO_RECEIPT=/tmp/demo.json`
writes the #125-shaped comparison: direct collection invalidates one source-changing
run and requires one intervention; snapshot collection keeps the tested input.
Report measured wall/setup/storage overhead separately. This fixture makes no
fixed speedup, real-marathon prevention, token savings, provider or phone claim.
