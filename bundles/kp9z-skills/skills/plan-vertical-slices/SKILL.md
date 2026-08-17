---
name: plan-vertical-slices
description: Plan and execute software artifact builds as runnable, verifiable vertical slices. Use for multi-layer features, full-stack apps, prototypes, MVPs, and implementation plans when the user asks for phased or phasal planning, vertical slices, walking skeletons, end-to-end milestones, demonstrable checkpoints, or something they can verify after every phase. Do not use for a tiny localized edit or for non-software artifacts unless the user explicitly requests this planning style.
---

# Plan Vertical Slices

Turn the build into thin end-to-end phases. Make every phase leave the system runnable and add one behavior the user can verify.

## Establish the path

1. Use prior exploration, critique, or requirements work as input; do not repeat it unnecessarily.
2. Identify the primary actor, the first valuable journey, the participating layers, and the riskiest integration boundary.
3. Resolve only questions that materially change the first slice. State safe assumptions and continue.
4. Choose the smallest real path that crosses the relevant layers.

## Build the phase plan

Plan by behavior, not by technical layer. Do not create phases such as “finish the database,” “finish the backend,” then “finish the frontend.”

Make Phase 1 a walking skeleton. For a frontend/backend/database system, prefer:

- one command or documented sequence that starts the required services;
- the real database connection, initial migration or schema, and minimal seed data when needed;
- one thin backend route or operation;
- one minimal frontend path wired through the backend to the database;
- one end-to-end check proving the round trip;
- one exact manual verification with an expected result.

Make each later phase extend that running system with one user-observable capability. Let a slice touch UI, backend, data, and tests whenever that behavior requires them.

For every phase, specify:

1. **Outcome**: the behavior newly available to a user.
2. **Vertical path**: the layers and boundaries the behavior crosses.
3. **Implementation**: the smallest coherent changes required.
4. **End-to-end proof**: an automated check at the widest practical boundary.
5. **User verification**: exact commands or actions and the expected observable result.
6. **Done gate**: evidence required before the next phase begins.

Keep the plan concrete enough to execute, but avoid file-by-file detail before inspecting the repository.

## Execute in slices

1. Keep the system runnable at the end of every phase.
2. Implement only the infrastructure needed by the current or immediately following slice.
3. Prefer real integrations. If a real dependency is unavailable, isolate a temporary substitute behind the intended boundary and state what remains unverified.
4. Prioritize end-to-end and integration checks over broad unit-test coverage. Add focused unit tests for dense logic or edge cases.
5. Run the phase's automated checks and perform any safe local verification available.
6. Report the delivered behavior, evidence, and user verification steps.
7. Unless the user asked for autonomous end-to-end completion, pause at the done gate so the user can verify before continuing.

## Guardrails

- Do not count scaffolding alone as a completed phase.
- Do not leave a phase with disconnected frontend, backend, or data work when those layers belong to its behavior.
- Do not defer all end-to-end testing to a final phase.
- Do not expand a slice merely to make a layer “complete.”
- Allow a horizontal prerequisite only when it is unavoidable; keep it narrow and attach it to the next demonstrable slice.
- Preserve user-approved scope and architecture unless a discovered constraint requires a change.

## Example phase shape

For a reporting app, prefer this sequence:

- **Phase 1 — View one real report:** start the stack, migrate and seed the database, expose one read query, render the result, and verify the browser-to-database round trip.
- **Phase 2 — Filter the report:** add the filter control, request validation, query behavior, and an end-to-end filter check.
- **Phase 3 — Save a report view:** add persistence, the save/load API behavior, the UI action, and an end-to-end reload check.

Adapt the number and content of phases to the artifact. The invariant is runnable, observable, and verified progress after each phase.
