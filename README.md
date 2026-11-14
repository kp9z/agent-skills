# Agent Skills and Bundles

Reusable agent skills, engineering workflows, and lifecycle hooks. Every
installable package has a manifest and an agent-facing installation
instruction. A package can own its payload or compose another package.

## Start here

Choose the bundle that matches the job, then give its `INSTALL.md` to the agent
performing the installation.

| Bundle | Purpose | Install instruction |
| --- | --- | --- |
| `build-ios-apps` | Nine OpenAI iOS skills, testing, and Apple design review | [`bundles/build-ios-apps/INSTALL.md`](bundles/build-ios-apps/INSTALL.md) |
| `core` | The pinned 13-skill engineering workflow | [`bundles/core/INSTALL.md`](bundles/core/INSTALL.md) |
| `kp9z-skills` | Original planning, skill maintenance, and spec-to-ticket workflows | [`bundles/kp9z-skills/INSTALL.md`](bundles/kp9z-skills/INSTALL.md) |
| `codex-essential` | Personal Codex workflow essentials | [`bundles/codex-essential/INSTALL.md`](bundles/codex-essential/INSTALL.md) |
| `destructive-command-hooks` | A shared destructive-command blocker with Codex and Claude Code adapters | [`bundles/destructive-command-hooks/INSTALL.md`](bundles/destructive-command-hooks/INSTALL.md) |

## How bundles work

Each bundle separates reusable source from the harness-specific destination:

```text
bundles/<bundle-name>/
├── INSTALL.md       # instructions for the installing agent
├── SETUP.md         # optional default setup profile
├── manifest.json    # identity, version, contents, and source metadata
└── ...              # skills, included bundles, hooks, tests, or licenses
```

`INSTALL.md` is not copied into the target project. The installing agent reads
the manifest, determines the active harness, inspects existing configuration,
asks before replacing conflicts, and copies only the bundle payload to the
appropriate destination.

## Bundle details

### Build iOS Apps

The complete OpenAI plugin snapshot includes nine skills for App Intents,
SwiftUI, Simulator debugging and browser mirroring, performance profiling,
and memory leak investigation. The local `ios-testing` skill adds Swift Testing,
XCTest, and XCUITest workflows. `ios-test-planner` inspects the codebase and
available APIs, proposes scenarios and setup for user approval, then hands
approved scenarios to `ios-testing` for implementation and the first run. Both
local skills remain included when upstream is refreshed. The bundled
`apple-design` skill adds HIG-based design review and is also preserved on refresh.
Installation and source details are in
[`bundles/build-ios-apps/INSTALL.md`](bundles/build-ios-apps/INSTALL.md) and
[`bundles/build-ios-apps/UPSTREAM.md`](bundles/build-ios-apps/UPSTREAM.md).

### Core

The bundle contains exactly these 13 skills:

- `setup-matt-pocock-skills`
- `triage`
- `grill-me`
- `grilling`
- `improve-codebase-architecture`
- `codebase-design`
- `domain-modeling`
- `writing-for-agents`
- `to-spec`
- `to-tickets`
- `tdd`
- `implement`
- `code-review`

The bundled snapshot is pinned to an upstream release. Before every new
installation, the agent checks the upstream release tags. If a newer stable
release exists, the agent asks whether to install that exact release or use the
bundled snapshot.

Project-specific files such as `AGENTS.md`, `CLAUDE.md`, and `docs/agents/*`
are generated during setup. They are not stored as generic templates in this
repository.

[`bundles/core/SETUP.md`](bundles/core/SETUP.md) records the recommended
repository defaults for an installing agent. It supplies answers to the setup
workflow without changing the bundled setup skill itself.

For Hermes Agent, skills install under `~/.hermes/skills` and portable project
instructions belong in the repository-root `AGENTS.md`. Run Hermes from that
root so it loads the file. The destructive-command hook bundle currently has
adapters only for Codex and Claude Code.

### kp9z skills

The original skills are stored together without assuming a harness-specific
installation directory. Each complete skill directory is copied as one unit.

- `plan-vertical-slices` plans runnable, verifiable software milestones.
- `skill-maintenance` audits skill collections and their context pointers.
- `grill-me-in-batch` sharpens multiple features in one chat, tracking shared
  decisions and dependencies. It requires Core’s `grilling` skill and runs only
  through explicit `$grill-me-in-batch` or `/grill-me-in-batch` invocation.
- `to_ticket_yolo` runs Core's `to-spec` then `to-tickets`, publishing a spec and
  linked issues without approval pauses. It requires those two skills and project
  tracker configuration, and runs only when explicitly invoked as
  `$to_ticket_yolo` or `/to_ticket_yolo`.

- `push_to_testflight` archives and uploads the current production iOS app through
  its configured CLI workflow. It runs only as `$push_to_testflight` or
  `/push_to_testflight`, preserves the app version, and ends after upload.

- `ticket_marathon` keeps the main chat as an orchestrator: it checks dependencies,
  delegates each ticket to a new chat running Core's `implement`, and waits for its
  result before selecting the next. It processes up to three tickets per batch,
  then schedules continuation after 4 hours 30 minutes until the queue is empty or
  intervention is required. It requires project tracker configuration and Codex app
  chat and scheduling tools, and starts only through explicit
  `$ticket_marathon` or `/ticket_marathon` invocation.

- `harness_improver` investigates the current chat and related workers for recurring
  workflow blockers, then proposes reusable harness fixes with evidence and quality
  checks. It includes issue read/write, bounded history and test-result helpers,
  and runs only through explicit `$harness_improver` or `/harness_improver` invocation.

The underscore spellings of `to_ticket_yolo`, `push_to_testflight`, `ticket_marathon`,
and `harness_improver` preserve their requested invocation names.

### Codex Essential

Codex Essential contains personal workflow skills that should remain available
across projects. `continue-in-new-chat` distills the useful state of the current
chat and continues the work in a clean Codex task. `i-dont-understand`
re-explains difficult material in simpler language without discarding important
accuracy. `merge-to-local-main` merges the current chat's work into `main`, pushes the result,
and keeps the chat open after the merge succeeds. It requires explicit invocation
via `/merge-to-local-main` or `$merge-to-local-main`.

### Destructive-command hooks

The hook bundle stores one shared Python implementation plus separate merge
fragments for Codex and Claude Code. The installer merges the selected adapter
into existing user configuration and never replaces unrelated hooks or settings.

## Repository map

```text
bundles/
├── build-ios-apps/
│   ├── INSTALL.md
│   ├── manifest.json
│   ├── UPSTREAM.md
│   ├── .codex-plugin/
│   ├── .mcp.json
│   ├── agents/
│   ├── assets/
│   └── skills/
├── core/
│   ├── INSTALL.md
│   ├── manifest.json
│   ├── LICENSE
│   └── skills/
├── kp9z-skills/
│   ├── INSTALL.md
│   ├── manifest.json
│   └── skills/
├── codex-essential/
│   ├── INSTALL.md
│   ├── manifest.json
│   └── skills/
└── destructive-command-hooks/
    ├── INSTALL.md
    ├── manifest.json
    ├── shared/
    ├── harnesses/
    └── tests/
```

Agents should start with this README, select one bundle, read that bundle's
`manifest.json`, and then follow only its `INSTALL.md`.
