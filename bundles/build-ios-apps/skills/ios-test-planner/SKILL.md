---
name: ios-test-planner
description: Investigate an iOS testing request such as "test login", propose scenarios with concrete setup, and obtain approval before creating or running tests. Use when the test scope or scenarios have not yet been agreed.
---

# iOS Test Planner

Turn "test {something}" into a reviewable scenario plan grounded in the current
codebase and available tools. After agreement, implement and run the selected
scenarios using the bundled `ios-testing` skill.

## Investigate before proposing

Use read-only inspection to establish:

- The requested feature's entry points, behavior, state transitions, and external
  dependencies. Inspect requirements and existing tests; distinguish intended
  behavior from assumptions inferred only from the implementation.
- Test targets, frameworks, schemes, test plans, fixtures, helpers, CI commands,
  supported environments, and relevant configuration keys.
- Available agent tools and APIs: inspect actual capabilities and schemas for
  code inspection, test execution, Simulator interaction, logs, and result
  collection. Also inspect app or service APIs that could prepare fixtures or
  verify outcomes. Distinguish capabilities that exist from ones that would
  need implementing or connecting. Do not assume XcodeBuildMCP supports a test
  operation merely because it supports building and launching.
- What can be exercised locally, what needs an integration environment, and
  which access or setup gaps affect the proposed test.

Do not create tests, edit configuration, seed or reset data, launch the app,
or run builds or tests during this planning phase. Read-only tool discovery
and environment inspection are allowed. Do not invoke a service API with side
effects to discover its behavior. Avoid displaying secret values; name the
required environment keys and how they are supplied.

Ask about missing information only when it changes the scenario or expected
result. Otherwise present a clearly marked assumption with the proposed plan.

## Present concrete scenarios

Propose the smallest useful set of scenarios for the requested behavior. Start
with user-observable outcomes, then attach enough setup detail to reproduce
each one. Assign stable scenario IDs, and include:

| Field | Include |
| --- | --- |
| Scenario | Behavior, purpose, and requirement or assumption it checks |
| Initial state | App lifecycle, authentication, permissions, persisted data, and fixtures that matter |
| Environment | Scheme, build configuration, OS or Simulator, and service environment |
| Variables and settings | Exact known keys and nonsecret values for environment variables, launch arguments, feature flags, and app settings; explicitly say when none are needed |
| Dependencies | Real services versus stubs or mocks, fixture preparation, isolation, and cleanup |
| Steps | Actions or API calls and the observable expected results |
| Execution | Unit, integration, or UI layer; runner or tool; assertions and evidence to collect |

Share common setup once. Link relevant code or existing helpers so the user
can see why the plan fits this project. Mark proposed new flags, fixtures,
or test hooks as additions instead of inventing existing configuration.
Include planned file or configuration changes and material data or service
effects. State what the scenarios do not cover when that limits the conclusion.

Present the plan in chat and ask which scenario IDs to approve or revise.
Wait for an explicit response. Silence is not approval. Approval of selected
scenarios does not approve omitted scenarios. A response such as "ok" directly
following the concrete plan approves that plan; retain that agreement across
turns without asking again for routine implementation choices.

If the user already supplied or approved a concrete plan, confirm its scope
against the codebase and continue without repeating the approval step. An
explicit request to run an existing named test or exact test command can go
directly to execution; do not impose scenario planning on that request.

## Implement and perform the first run

After approval, read [ios-testing](../ios-testing/SKILL.md) and pass along the
approved IDs, expected outcomes, setup, execution method, and known gaps.
Both skills are distributed together. If the execution skill is unavailable,
report that dependency before proceeding with dependent work.

Create only the agreed tests and necessary fixtures or test configuration.
Prepare isolated state, implement the assertions, and execute the first run.
Record the actual configuration, selected tests, counts, results, and artifacts.
For a regression case, establish the intended failing behavior before a fix
when practical. Planning approval alone does not authorize a product bug fix.

If implementation reveals a material change to the approved expected outcome,
environment, real-service effects, or scope, present the revised part for
agreement before proceeding with that part. Routine test-code corrections
within the approved plan need no repeated approval.

Report each approved ID as passed, failed, or blocked, with the observed result
and evidence. Preserve first-run failures even if later retries pass. Explain
whether a failure indicates a product defect, test issue, or environment blocker;
do not silently rewrite expectations or claim unexecuted scenarios passed.
