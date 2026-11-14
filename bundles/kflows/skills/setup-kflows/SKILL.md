---
name: setup-kflows
description: Set up a repository's GitHub Issues, triage labels, and AGENTS.md for kFlows, or triage its GitHub issues using the configured workflow.
disable-model-invocation: true
---

# Setup kFlows

Configure GitHub Issues and the repository-root `AGENTS.md` for the installed
kFlows skills. Triage is a mode of this skill rather than a separate skill.

## Choose the mode

- `$setup-kflows` configures the current repository.
- `$setup-kflows triage` lists issues needing attention.
- `$setup-kflows triage #42` triages a specific issue; the user may also describe
  a label change or another triage action after `triage`.

For triage, read the project's `AGENTS.md`, `docs/agents/issue-tracker.md`, and
`docs/agents/triage-labels.md`, then follow [the triage workflow](references/triage.md).
If configuration is missing, identify it and complete setup before triaging.
An explicit triage request does not require repeating an already-complete setup.

## 1. Inspect the repository

Read the root `AGENTS.md`, existing `docs/agents/` files, Git remotes, and any
existing glossary or ADR layout. Inspect the installed kFlows skills and existing
GitHub labels. Resolve the intended GitHub repository from the remote and verify
access with `gh repo view OWNER/REPO` or the connected GitHub tools.

Use GitHub Issues as the tracker and `AGENTS.md` as the project instruction file.
If the repository is missing, inaccessible, or ambiguous, ask only for the missing
repository/access information. Preserve Git configuration; setup does not create
a remote, repository, or credentials. Report an existing conflicting tracker
configuration before replacing it.

## 2. Prepare the configuration

Use these defaults unless the repository or user already supplies a deliberate
alternative within GitHub:

- Categories: `bug` and `enhancement`.
- Triage states: `needs-triage`, `needs-info`, `ready-for-agent`,
  `ready-for-human`, and `wontfix`.
- Pull requests as a triage request surface: off.
- Domain layout: root `GLOSSARY.md` and `docs/adr/`. Preserve an established
  multi-context layout. Create glossary entries and ADRs only when real terms or
  decisions are resolved; setup writes the consumer rules, not empty domain docs.

Draft the following files from the bundled references, replacing repository
placeholders with the verified repository:

- `docs/agents/issue-tracker.md`: [GitHub conventions](issue-tracker-github.md).
- `docs/agents/triage-labels.md`: [canonical labels](triage-labels.md), preserving
  an intentional existing mapping and creating only missing configured labels.
- `docs/agents/domain.md`: [domain consumer rules](domain.md).

Prepare a single `## Agent skills` section in the root `AGENTS.md`:

```markdown
## Agent skills

Use `$setup-kflows` to configure this repository and `$setup-kflows triage` to
triage issues. Use `$grill-me`, `$to-spec`, `$to-tickets`, and `$implement` for the
planning-to-implementation workflow.

### Issue tracker

Store specs and tickets in [OWNER/REPO GitHub Issues](https://github.com/OWNER/REPO/issues).
Read [tracker conventions](docs/agents/issue-tracker.md) before reading or publishing issues.

### Triage

Read [the label mapping](docs/agents/triage-labels.md) before triaging or labeling issues.

### Domain docs

Read [domain rules](docs/agents/domain.md) before exploring terminology or architectural decisions.
```

List only installed skills. Preserve surrounding project instructions and update
an existing section in place. Existing `CLAUDE.md` content does not change the
`AGENTS.md` destination; leave it alone unless the user asks to update it.

## 3. Apply and verify

Show the concrete document changes and missing labels. Proceed when the user has
already authorized setup with these defaults; ask about unresolved conflicts
before replacing differing project conventions. Use the available GitHub tools or
`gh label create --repo OWNER/REPO` to create missing configured labels. Preserve
unrelated labels, colors, descriptions, and repository settings.

Write the prepared documents. Verify that all links resolve, the configured
GitHub repository is reachable, every mapped label exists, and `AGENTS.md` has
one Agent skills section. A rerun should leave an already-matching setup unchanged.
Report changed files, labels created, the GitHub repository, and unresolved
requirements. Setting up triage does not itself label, comment on, or close issues.
