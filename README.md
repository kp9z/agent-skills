# kFlows

Reusable agent skills, engineering workflows, and lifecycle hooks. Every
installable package has a manifest and an agent-facing installation
instruction. A package can own its payload or compose another package.

## Start here

Choose the bundle that matches the job, then give its `INSTALL.md` to the agent
performing the installation.

| Bundle | Purpose | Install instruction |
| --- | --- | --- |
| `build-ios-apps` | Nine OpenAI iOS skills, testing, design review, and TestFlight upload | [`bundles/build-ios-apps/INSTALL.md`](bundles/build-ios-apps/INSTALL.md) |
| `kflows` | GitHub setup, triage, planning, implementation, review, and personal workflows | [`bundles/kflows/INSTALL.md`](bundles/kflows/INSTALL.md) |
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

- `push_to_testflight` archives and uploads the current production iOS app through
  its configured CLI workflow. It runs only as `$push_to_testflight` or
  `/push_to_testflight`, preserves the app version, and ends after upload.

### kFlows

kFlows combines the personal workflows with the engineering skills from the
existing Matt Pocock v1.3.2 installation. Source metadata is recorded per skill
in the manifest, and the upstream MIT license is preserved. Each complete skill
directory is installed as one unit.

- `setup-kflows` configures GitHub Issues, canonical labels, and the root
  `AGENTS.md`. Its `$setup-kflows triage` mode handles issue triage using bundled
  brief and rejection references; no separate `triage` skill is installed.
- `grill-me` and `grilling` sharpen a plan or design through an interview.
- `to-spec` and `to-tickets` publish an agreed specification and linked tickets.
- `implement`, `tdd`, and `code-review` implement and verify the agreed work.
- `codebase-design` and `improve-codebase-architecture` guide module design
  and architectural improvements.
- `domain-modeling` maintains `GLOSSARY.md` and architectural decisions.
- `writing-for-agents` guides skill and project instruction authoring.

- `grill-me-in-batch` sharpens multiple features in one chat, tracking shared
  decisions and dependencies. It requires the included `grilling` skill and runs only
  through explicit `$grill-me-in-batch` or `/grill-me-in-batch` invocation.
- `to_ticket_yolo` runs the included `to-spec` then `to-tickets`, publishing a spec and
  linked issues without approval pauses. It requires those two skills and project
  tracker configuration, and runs only when explicitly invoked as
  `$to_ticket_yolo` or `/to_ticket_yolo`.

- `ticket_marathon` keeps the main chat as an orchestrator: it checks dependencies,
  delegates each ticket to a new chat running the included `implement`, and waits for its
  result before selecting the next. It processes up to three tickets per batch,
  then schedules continuation after 4 hours 30 minutes until the queue is empty or
  intervention is required. It requires project tracker configuration and Codex app
  chat and scheduling tools, and starts only through explicit
  `$ticket_marathon` or `/ticket_marathon` invocation.

- `harness_improver` investigates the current chat and related workers for recurring
  workflow blockers, then proposes reusable harness fixes with evidence and quality
  checks. It includes issue read/write, bounded history and test-result helpers,
  and runs only through explicit `$harness_improver` or `/harness_improver` invocation.

- `merge-to-local-main` merges the current chat's verified work into `main`,
  pushes the result, and keeps the chat open. It requires explicit invocation
  via `/merge-to-local-main` or `$merge-to-local-main`.

The underscore spellings of `to_ticket_yolo`, `ticket_marathon`,
and `harness_improver` preserve their requested invocation names.

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
├── kflows/
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
