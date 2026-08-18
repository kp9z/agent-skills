# Default Repository Setup

Use this profile when installing Core or Plus and the user asks for the default
setup. It supplies the recommended answers to `setup-matt-pocock-skills`; it does
not modify that skill, its invocation policy, or its setup workflow.

## Profile

- **Harness:** configure only the active harness. For Codex, use `AGENTS.md`.
  For Claude Code, use `CLAUDE.md`. For Hermes Agent, use the repository-root
  `AGENTS.md`.
- **Issue tracker:** use GitHub Issues when `git remote -v` identifies a GitHub
  repository. Leave "PRs as a request surface" off.
- **Triage vocabulary:** use the canonical label strings unchanged:
  `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and
  `wontfix`.
- **Issue categories:** use `bug` and `enhancement`.
- **Domain docs:** use the single-context layout unless exploration finds real
  monorepo signals.

For GitHub, the resulting label set is `bug`, `enhancement`, `needs-triage`,
`needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. Reuse matching
labels and create only missing labels.

## Applying the profile

Treat an explicit request for "default setup" as the user's answer to the setup
choices above. Inspect the repository first and surface any conflict with existing
configuration. Then follow `setup-matt-pocock-skills` unchanged, including its
required draft review before writing.

If the repository is not on GitHub, has an existing noncanonical label mapping,
or has genuine monorepo signals, present the detected exception and let the setup
skill ask for that choice. Preserve unrelated files, labels, and harness
configuration.
