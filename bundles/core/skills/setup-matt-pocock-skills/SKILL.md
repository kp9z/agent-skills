---
name: setup-matt-pocock-skills
description: Configure this repo for the engineering skills — set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills.
disable-model-invocation: true
---

# Setup Matt Pocock's Skills

Scaffold the per-repo configuration that the engineering skills assume:

- **Issue tracker** — where issues live (GitHub by default; local markdown is also supported out of the box)
- **Triage labels** — the strings used for the five canonical triage roles
- **Domain docs** — where `CONTEXT.md` and ADRs live, and the consumer rules for reading them

Use an idempotent default fast path. Inspect first, apply unambiguous defaults without
asking, and stop only for a choice that changes the outcome or a conflicting existing
configuration.

## Process

### 1. Explore

Look at the current repo to understand its starting state. Read whatever exists; don't assume:

- `git remote -v` and `.git/config` — is this a GitHub repo? Which one?
- `AGENTS.md` and `CLAUDE.md` at the repo root — does either exist? Is there already an `## Agent skills` section in either?
- `CONTEXT.md` and `CONTEXT-MAP.md` at the repo root
- `docs/adr/` and any `src/*/docs/adr/` directories
- `docs/agents/` — does this skill's prior output already exist?
- `.scratch/` — sign that a local-markdown issue tracker convention is already in use
- Is the `triage` skill installed? (a `triage` skill folder alongside this one, or `triage` in your available skills.) This decides whether Section B runs at all.
- Monorepo signals — a `pnpm-workspace.yaml`, a `workspaces` field in `package.json`, or a populated `packages/*` with its own `src/`. Present only in a genuinely large multi-package repo; their absence means single-context, which is almost every repo.
- The active harness. Codex uses `AGENTS.md`, Claude Code uses `CLAUDE.md`, and Hermes uses `AGENTS.md`.
- For a GitHub tracker, whether `gh auth status` succeeds and which required labels already exist.

### 2. Choose defaults

Apply every default that exploration settles. Ask only when the tracker, harness, label
mapping, or domain layout remains ambiguous, or when existing configuration disagrees.

The zero-prompt fast path is:

- a GitHub remote -> GitHub Issues;
- an installed `triage` skill -> the five canonical label strings unchanged;
- no genuine monorepo signals -> single-context domain docs;
- Codex -> `AGENTS.md`;
- Claude Code -> `CLAUDE.md`;
- Hermes -> repository-root `AGENTS.md`.

When every applicable branch matches this path, write and validate immediately. Report
the choices afterward. Existing output that already matches is a successful no-op;
repair missing files, instruction blocks, or GitHub labels without restarting setup.

**Section A — Issue tracker.**

> Explainer: The "issue tracker" is where issues live for this repo. Skills like `to-tickets`, `triage`, and `to-spec` read from and write to it — they need to know whether to call `gh issue create`, write a markdown file under `.scratch/`, or follow some other workflow you describe. Pick the place you actually track work for this repo.

Default posture: these skills were designed for GitHub. If a `git remote` points at GitHub, select GitHub without asking. If a `git remote` points at GitLab (`gitlab.com` or a self-hosted host), select GitLab without asking. Otherwise (or if existing configuration points somewhere else), offer:

- **GitHub** — issues live in the repo's GitHub Issues (uses the `gh` CLI)
- **GitLab** — issues live in the repo's GitLab Issues (uses the [`glab`](https://gitlab.com/gitlab-org/cli) CLI)
- **Local markdown** — issues live as files under `.scratch/<feature>/` in this repo (good for solo projects or repos without a remote)
- **Other** (Jira, Linear, etc.) — ask the user to describe the workflow in one paragraph; the skill will record it as freeform prose

Record the choice in `docs/agents/issue-tracker.md`. The GitHub and GitLab templates carry a "PRs as a request surface" flag, defaulted **off** — leave it off and don't raise it; a user who wants external PRs in the triage queue can flip the flag in the file later.

**Section B — Triage label vocabulary.** Skip this section entirely if the `triage` skill isn't installed (exploration told you) — an uninstalled skill needs no labels.

If it is installed, use the five canonical roles unchanged: `needs-triage`,
`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Ask only when an
existing mapping uses other strings or the tracker already has an obvious alternate
vocabulary (for example, `bug:triage`). Preserve an existing intentional mapping.

**Section C — Domain docs.** Default to **single-context** — one `CONTEXT.md` + `docs/adr/` at the repo root. This fits almost every repo; write it without asking.

Offer **multi-context** — a root `CONTEXT-MAP.md` pointing to per-context `CONTEXT.md` files — only when exploration found monorepo signals. Then confirm which layout they want.

### 3. Resolve exceptions

For any unresolved choice, summarise the evidence, lead with the recommended answer,
and ask one focused question at a time. If changing an existing intentional setup,
show only the affected draft before writing:

- The `## Agent skills` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is being edited (see step 4 for selection rules)
- The contents of `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, and `docs/agents/triage-labels.md` (the last only when `triage` is installed)

Continue automatically when there is no exception.

### 4. Write

**Pick the file for the active harness:**

- Codex: preserve or create `AGENTS.md`.
- Claude Code: preserve or create `CLAUDE.md`.
- Hermes: preserve or create repository-root `AGENTS.md`.
- Another or unknown harness: ask where project instructions belong.

The presence of another harness's file does not override this selection. Preserve that
file and configure only the active harness.

If an `## Agent skills` block already exists in the chosen file, update its contents in-place rather than appending a duplicate. Don't overwrite user edits to the surrounding sections.

The block:

```markdown
## Agent skills

### Issue tracker

[one-line summary of where issues are tracked]. See `docs/agents/issue-tracker.md`.

### Triage labels

[one-line summary of the label vocabulary]. See `docs/agents/triage-labels.md`.

### Domain docs

[one-line summary of layout — "single-context" or "multi-context"]. See `docs/agents/domain.md`.
```

Include the `### Triage labels` sub-block, and write `docs/agents/triage-labels.md`, only when `triage` is installed and Section B ran. When it isn't, both are omitted.

Then write the docs files using the seed templates in this skill folder as a starting point:

- [issue-tracker-github.md](./issue-tracker-github.md) — GitHub issue tracker
- [issue-tracker-gitlab.md](./issue-tracker-gitlab.md) — GitLab issue tracker
- [issue-tracker-local.md](./issue-tracker-local.md) — local-markdown issue tracker
- [triage-labels.md](./triage-labels.md) — label mapping (only if `triage` is installed)
- [domain.md](./domain.md) — domain doc consumer rules + layout

For "other" issue trackers, write `docs/agents/issue-tracker.md` from scratch using the user's description.

For GitHub with `triage` installed, ensure the two category labels (`bug`,
`enhancement`) and five state labels (`needs-triage`, `needs-info`,
`ready-for-agent`, `ready-for-human`, `wontfix`) exist without changing unrelated
labels. Reuse exact matches and create only missing labels. If GitHub authentication or
permissions prevent this, finish the local setup and report the exact label operation
still required.

### 5. Validate

- The selected instruction file contains exactly one `## Agent skills` section.
- Every link from that section resolves.
- Tracker and label docs agree with the detected repository and live labels.
- A second run of this setup skill would make no local changes and create no labels.

### 6. Done

Tell the user which defaults were applied, what was repaired or left unchanged, and which
engineering skills will read these files. Mention they can edit `docs/agents/*.md`
directly later and rerun setup safely to validate or repair the configuration.
