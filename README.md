# Agent Skills and Bundles

Reusable agent skills, engineering workflows, and lifecycle hooks. Everything
installable lives in a self-contained bundle with its own payload, manifest,
and agent-facing installation instruction.

## Start here

Choose the bundle that matches the job, then give its `INSTALL.md` to the agent
performing the installation.

| Bundle | Purpose | Install instruction |
| --- | --- | --- |
| `grill-me` | A pinned 13-skill engineering workflow based on Matt Pocock's skill suite | [`bundles/grill-me/INSTALL.md`](bundles/grill-me/INSTALL.md) |
| `kp9z-skills` | The `plan-vertical-slices` and `skill-maintenance` skills | [`bundles/kp9z-skills/INSTALL.md`](bundles/kp9z-skills/INSTALL.md) |
| `destructive-command-hooks` | A shared destructive-command blocker with Codex and Claude Code adapters | [`bundles/destructive-command-hooks/INSTALL.md`](bundles/destructive-command-hooks/INSTALL.md) |

## How bundles work

Each bundle separates reusable source from the harness-specific destination:

```text
bundles/<bundle-name>/
├── INSTALL.md       # instructions for the installing agent
├── manifest.json    # identity, version, contents, and source metadata
└── ...              # skills, hook code, adapters, tests, or licenses
```

`INSTALL.md` is not copied into the target project. The installing agent reads
the manifest, determines the active harness, inspects existing configuration,
asks before replacing conflicts, and copies only the bundle payload to the
appropriate destination.

## Bundle details

### Grill-me

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
├── grill-me/
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
