# Receipt diagnostics

Inspect an existing receipt once with `python3 scripts/test_results.py /absolute/run.json`.
The SkinSense copy is `scripts/evidence/test_results.py`. CLI exit 0 means inspection
succeeded; read `verification` for the execution result. Exit 1 means input could
not be inspected; the bounded error omits payloads. Neither command runs tests.

## Supported evidence

Execution fields are nonempty string arrays `selected` and `executed`, final
`status` (`passed`/`failed`), integer `exitCode`, and nonnegative integer
`summary.failedTests` / `summary.skippedTests`. Passing requires nonempty matching
selection/execution, zero failures/skips, successful final status/exit and no
supported log failures or partial log coverage. Successful builds and silence in
logs alone cannot establish a pass. Missing or malformed execution is unverified.

`source` and `sourceAfter` support `git-working-bytes-v1`: absolute `checkout`,
full lowercase hexadecimal `baseline` and `revision` (40–64 characters), SHA-256
`fingerprint`, string-array `excluded` and optional `installed` (default empty;
objects with `path` and SHA-256 `sha256`). Comparable scopes require identical
checkout, baseline, algorithm, exclusions and installed pins. Revisions may differ
when identical working bytes are committed. Unequal comparable fingerprints prove
`source_changed`, overriding forged passing status/exit. Bounded provenance names
`source.fingerprint` / `sourceAfter.fingerprint`, both hashes/revisions and scope.
Unsupported algorithms or different scopes are unknown; malformed identities are
invalid. One absent identity is unknown. Explicit null identities are unknown.
Both fields absent retain legacy execution-only inspection, with an explicit
limit: execution results do not prove source-bound completion. Matching receipt
identities are local attestations; completion still checks current checkout,
baseline, revision ancestry, installed bytes, reviews and acceptance evidence.

`failure_kind` is the first supported reason. `failure_reasons` preserves all
supported reasons in this order: source_changed, compiler, test_assertion,
execution_mismatch, runner_or_unclassified, receipt_invalid. Compiler/assertion
lines and receipt counters remain evidence even when source changed. Runner status
or exit failure remains visible alongside specific reasons. This is evidence
classification, not proof of causality or a claim that a failure is pre-existing.

## Bounds and references

Defaults: 8 items and 500 characters per variable item/reference. CLI ranges:
`--limit 1..50`, `--chars 1..10000`. Fixed schema labels, six reason codes and
64-character hashes have fixed independent bounds. Missing/unexpected totals are
exact; arrays are clipped with explicit truncation flags. Error entries contain
physical log line numbers and categories, with arbitrary message content omitted
to keep transcripts and secrets out of compact output. Read the original log
locally at that line for details. A clipped reference is explicitly marked; use
the input receipt location to recover its full path. Raw files are never rewritten.

Input limits: 8 MiB receipt, 2 MiB log scan, first 4096 bytes per physical log line,
and 4096 retained distinct error hashes. Repeated error lines are deduplicated;
`matched_lines` counts scanned matches including repetitions. For complete scans,
`additional_error_lines` counts distinct matches omitted by the item cap.
For partial scans it is a lower bound and `distinct_matches` is null. Overlong
lines, scan caps or distinct-hash saturation make log coverage unknown and block
passing inference. An absent log is explicitly unavailable; complete receipts
can still establish execution results. The helper never emits raw log messages.
Malformed JSON, denied inputs and oversized receipts yield a safe unverified error.

## Recovery and handoff

Read `failure_reasons`, source state and receipt location first. For source_changed,
retain stale artifacts, identify the intended source and arrange a separately
authorized exact-source verification. For assertion/compiler/execution reasons,
inspect the referenced raw log line or selected/executed fields. For unknown or
invalid source metadata, recover the original complete identity pair or record
the limitation; never synthesize equality. For partial logs, inspect the original
artifact under appropriate local handling. Diagnostics never retry, edit code,
close issues or authorize requests. Runner output and completion summaries use
this compact classification; original test receipts/logs remain authoritative.

## Synchronization and compatibility

Keep the standalone installation in `~/.agents/skills/harness_improver`.
From the selected reviewed source, explicitly copy `scripts/test_results.py` and
`scripts/completion_record.py` to SkinSense `scripts/evidence/`, and copy
`tests/test_result_diagnostics.py` plus `tests/fixtures/test-result-golden.json`
to `scripts/tests/` (the test discovers either installed or adapter layout).
Review both copies and update the installation pin manifest's hashes/archive.
Preserve prior manifests/receipts. Compare SHA-256 for both consumer scripts and
the shared corpus, then run both suites with `DIAGNOSTICS_PEER_CLI` set to the
other consumer. Every golden case must match its literal expectations and both
CLIs must return identical payloads on the same input paths. Run the targeted
completion-record/runner and snapshot compatibility checks before accepting
new source-bound evidence. Keep global helpers global; no project-local skill
or additional result parser is required.
