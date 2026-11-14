---
name: improve-test-quality
description: Audit and improve an existing test suite for faster feedback and stronger regression protection. Use when pruning low-value or overlapping tests, strengthening assertions, or reducing test setup and runtime costs.
---

# Improve test quality

Optimize for a small, trustworthy suite that catches meaningful regressions and explains failures. Test count, line coverage, and runtime are evidence, not independent targets. A useful outcome may strengthen coverage without deleting any tests.

Respect the requested scope: an audit produces candidates; an implementation request makes and verifies focused changes. Apply repository testing conventions and existing authorization. Keep platform details in the repository rather than assuming a framework or device.

## Establish the baseline

Read the test configuration, runner selections, fixtures, relevant production code, and available results. Identify the behaviors and integration boundaries the selected tests protect. Inspect historical regression context when available.

Distinguish test execution from builds, application or simulator launch, fixture setup, external services, and waiting. Prefer existing timings initially; run a comparable baseline for the area being changed when practical. Record existing failures separately. State when findings come from source inspection without execution.

For large suites, inventory the whole requested scope, then prioritize costly or weak clusters. Report areas not inspected instead of implying a complete audit.

## Evaluate candidates

For each actionable candidate, identify the test, protected behavior, concrete weakness or cost, proposed change, and coverage that must survive. Prioritize confidence gained relative to execution and maintenance cost.

Look for:

- **Redundancy:** the same behavior, conditions, boundary, and failure mode asserted repeatedly. Shared code paths or similar names alone do not establish duplication. Preserve distinct inputs, boundary conditions, integration checks, and historical regressions.
- **Weak assertions:** checks that can pass when the intended behavior is broken, expected values derived from the implementation, or snapshots without a useful review signal. Prefer independently justified outcomes. Where failure should preserve data, test preservation of existing data as well as absence of new data.
- **Implementation coupling:** assertions about private structure or internal call choreography where a stable observable outcome would protect the contract. Keep protocol sequencing assertions when ordering itself is the contract.
- **Expensive setup:** full user journeys repeated merely to prepare state for unrelated checks. Seed valid state through existing fixtures while retaining focused tests of the actual journey and persistence boundary.
- **Wrong test layer:** detailed business cases repeated through UI or network workflows. Move appropriate cases to a faster public boundary and retain the integration or interaction coverage the lower layer cannot prove.
- **Unnecessary waiting:** sleeps, real deadlines, repeated handshakes, or polling unrelated to the behavior under test. Use controllable clocks, schedulers, and callbacks where appropriate. Retain focused real-time or system checks when actual timing, delivery, or lifecycle behavior is the contract.
- **Fragility and diagnosis:** nondeterministic inputs, shared mutable fixtures, broad scenarios whose failures obscure the cause, and excessive artifact capture. Preserve useful failure evidence and intentionally collected visual or system evidence.

Parameterization is useful when cases share a contract and each failing input remains identifiable. Consolidation should preserve test isolation and diagnostic clarity; fewer test methods alone is not a benefit.

Before deleting a test or assertion, name the surviving test and explain how it catches the same meaningful regression. If replacement coverage is needed, establish it first. Keep uncertain cases and explain the uncertainty. A test going green after deletion is not evidence of improvement.

## Make focused improvements

Work in coherent batches so each coverage change can be reviewed and verified. Preserve unrelated work. Keep production changes limited to small, justified testability seams with unchanged product behavior; report larger architectural opportunities separately.

Fix flaky synchronization or isolation at its cause. Preserve expectations instead of skipping failures, inflating timeouts, or adding retries that hide defects. Keep existing test-selection manifests and fixture inventories consistent when tests move or are renamed.

## Verify protection and speed

Run affected tests and relevant integration or regression checks, then broaden only as required by the change and repository conventions. Separate baseline failures from new failures. If execution is unavailable, report the unverified changes and blocker.

For important rewritten or replacement coverage, use a bounded fault check when practical: temporarily introduce a representative regression at the relevant boundary and confirm the intended test fails for the expected reason. Restore only the temporary edit, preserve user changes, and rerun the clean test. Use an isolated copy when concurrent edits make restoration uncertain. Mutation tooling is optional; do not require a suite-wide campaign.

Compare before and after using the same selection and comparable environment, build/cache conditions, and concurrency. Separate removed fixed waits from measured wall-clock savings. Repeat noisy measurements only enough to support the claim. Report any coverage tradeoffs or remaining uncertainty; coverage percentages alone cannot prove equivalent protection.

## Report

Summarize the inspected scope and highest-value findings. For implemented changes, report:

- Removed, consolidated, strengthened, or moved tests, with the behavior and surviving coverage for each deletion.
- Setup and timing changes, with measured results or clearly labeled estimates and affected runner selections.
- Checks run, fault checks where used, existing failures, and unverified areas.
- Candidates retained or deferred because their value or replacement coverage remains uncertain.

Finish when the requested scope is accounted for and implemented batches have relevant verification, or explicitly identify what remains blocked. Do not pursue a deletion quota or add speculative tests to compensate for an unproven removal.
