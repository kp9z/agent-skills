# Agent Skills and Bundles

Reusable agent skills, engineering workflows, and lifecycle hooks. Every
installable package has a manifest and an agent-facing installation
instruction. A package can own its payload or compose another package.

## Start here

Choose the bundle that matches the job, then give its `INSTALL.md` to the agent
performing the installation.

| Bundle | Purpose | Install instruction |
| --- | --- | --- |
| `core` | The pinned 13-skill engineering workflow | [`bundles/core/INSTALL.md`](bundles/core/INSTALL.md) |
| `plus` | Core plus Wayfinder, Research, and Prototype | [`bundles/plus/INSTALL.md`](bundles/plus/INSTALL.md) |
| `kp9z-skills` | The `plan-vertical-slices` and `skill-maintenance` skills | [`bundles/kp9z-skills/INSTALL.md`](bundles/kp9z-skills/INSTALL.md) |
| `destructive-command-hooks` | A shared destructive-command blocker with Codex and Claude Code adapters | [`bundles/destructive-command-hooks/INSTALL.md`](bundles/destructive-command-hooks/INSTALL.md) |

## How bundles work

Each bundle separates reusable source from the harness-specific destination:

```text
bundles/<bundle-name>/
├── INSTALL.md       # instructions for the installing agent
├── manifest.json    # identity, version, contents, and source metadata
└── ...              # skills, included bundles, hooks, tests, or licenses
```

`INSTALL.md` is not copied into the target project. The installing agent reads
the manifest, determines the active harness, inspects existing configuration,
asks before replacing conflicts, and copies only the bundle payload to the
appropriate destination.

## Bundle details

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

For Hermes Agent, skills install under `~/.hermes/skills` and portable project
instructions belong in the repository-root `AGENTS.md`. Run Hermes from that
root so it loads the file. The destructive-command hook bundle currently has
adapters only for Codex and Claude Code.

### Plus

Plus composes the entire Core bundle with three additional skills:

- `wayfinder`
- `research`
- `prototype`

`wayfinder` maps a large, uncertain effort into decision tickets. Its
`research` and `prototype` dependencies are included so every Wayfinder ticket
type works.

### kp9z skills

The two original skills are stored together without assuming a harness-specific
installation directory. Each complete skill directory is copied as one unit.

### Destructive-command hooks

The hook bundle stores one shared Python implementation plus separate merge
fragments for Codex and Claude Code. The installer merges the selected adapter
into existing user configuration and never replaces unrelated hooks or settings.

## Repository map

```text
bundles/
├── core/
│   ├── INSTALL.md
│   ├── manifest.json
│   ├── LICENSE
│   └── skills/
├── plus/
│   ├── INSTALL.md
│   ├── manifest.json
│   ├── LICENSE
│   └── skills/
├── kp9z-skills/
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
