---
name: ios-testing
description: Write, run, and diagnose iOS tests using Swift Testing, XCTest, and XCUITest. Use for regression tests, test coverage for changed behavior, UI test flows, or unreliable test failures.
---

# iOS Testing

Produce tests that verify requirements and report evidence from actual execution.

## Choose the scope and framework

- Inspect repository instructions, test targets, shared schemes, test plans,
  existing helpers, Xcode version, and CI commands before changing tests.
  Reuse the project's framework and conventions; do not migrate suites as a
  side effect of a feature or bug fix.
- For new Swift unit tests, consider Swift Testing when supported by the
  project. Use XCTest for existing XCTest suites, Objective-C tests, XCTest
  performance measurements, and UI automation through XCUIAutomation (XCUITest).
  Swift Testing and XCTest can coexist in a target; keep their assertions and
  lifecycle APIs within their respective test styles.
- Put business rules and state transitions in unit tests, dependency interactions
  in integration tests, and critical user journeys in a small UI suite. Choose
  the lowest layer that can demonstrate the required behavior.

## Establish meaningful assertions

- Derive expected outcomes from requirements, public contracts, or a concrete
  bug reproduction before implementing the change. Cover relevant boundaries,
  failure paths, and cancellation without duplicating implementation details.
- For a bug fix, add a focused regression test and establish that it fails on
  the unfixed behavior for the intended reason before applying the fix. A build
  error or missing fixture is not that evidence. If the fix already exists,
  use a safe isolated comparison when practical; report any unverified red phase.
- For features, develop one meaningful behavior at a time. Prefer assertions
  about outputs, state, or visible outcomes over assertions about private call
  order. Avoid adding tests merely to increase a coverage number.
- Ensure new test files belong to the intended test target and are included by
  the selected scheme and test plan. Do not assume creating a file registers it.

## Control state and concurrency

- Inject or configure deterministic network responses, clocks, identifiers,
  and persistence where needed. Use isolated temporary storage and clean up
  resources owned by each test. Avoid shared user accounts and real services
  unless the task explicitly requires an environment-backed integration test.
- Make tests independent of order and safe under the suite's parallel execution.
  Swift Testing runs tests in parallel by default. Isolate mutable state first;
  use serialization only for a demonstrated shared-resource requirement.
- For Swift concurrency, use `async` or `async throws` tests and await the
  operation. For callback-based XCTest APIs, use expectations and bounded
  asynchronous fulfillment. Never block the main actor waiting for work that
  needs it; use `@MainActor` only where actor-isolated code requires it.
- Wait for observable conditions rather than fixed sleeps. Choose bounded
  timeouts for the operation, and distinguish timeout failures from bad values.

## Make UI tests reliable

- Launch from explicit, repeatable state using existing launch arguments,
  environment settings, or test fixtures. Configure those before `app.launch()`.
  Keep any new test-only app behavior scoped to the test configuration.
- Query stable accessibility identifiers rather than coordinates, element
  indexes, or localized text unless that text is the behavior being tested.
  Wait for existence, disappearance, or readiness as appropriate; an element
  existing alone does not establish that it is hittable.
- Assert the user-visible outcome after an action. Include screenshots,
  accessibility hierarchy details, or relevant logs when diagnosing failures.
  Simulator mirroring and screenshots support diagnosis but do not substitute
  for automated assertions.

## Execute and diagnose

Read [execution.md](references/execution.md) when selecting commands, filtering
tests, or inspecting result bundles. Use the project's supported runner, an
available test-capable MCP tool, or `xcodebuild`; this skill needs no specific MCP.

1. Run the focused test, then the affected suite and repository-required checks.
   Verify the intended tests actually executed and the count is nonzero.
2. Separate assertion failures, build failures, runner or Simulator failures,
   and missing dependencies. Fix the demonstrated cause. For suspected flakiness,
   repeat the focused case under comparable conditions and preserve all outcomes.
   A passing retry does not erase the initial failure.
3. Do not delete assertions, skip cases, inflate timeouts, disable parallelism,
   or change production semantics merely to obtain a green run. Change a test's
   expectation only when requirements or evidence show it was wrong.
4. Report changed behavior, tests added or changed, exact command or tool call,
   scheme and destination, executed counts and outcomes, and result artifact
   paths. State skipped checks or environment blockers explicitly. Claim only
   the coverage demonstrated by executed tests.

## Official guidance

- [Apple testing overview](https://developer.apple.com/documentation/xcode/testing)
- [Adding tests and mixing frameworks](https://developer.apple.com/documentation/xcode/adding-tests-to-your-xcode-project)
- [XCTest asynchronous tests](https://developer.apple.com/documentation/xctest/asynchronous-tests-and-expectations)
- [Swift Testing migration and shared state](https://docs.swift.org/latest/documentation/testing/migratingfromxctest/)
