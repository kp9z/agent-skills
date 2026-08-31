# Install Codex Essential

Use this instruction in a local checkout of `kp9z/agent-skills`. This bundle contains personal Codex skills intended to be available across projects.

## Install

1. Read [`manifest.json`](manifest.json) and verify every listed skill path.
2. Resolve the personal Codex skill directory as `$CODEX_HOME/skills` when `CODEX_HOME` is set, or `~/.codex/skills` otherwise.
3. Inspect each destination before copying. Leave an identical skill unchanged. If an existing skill differs, show the conflict and ask before replacing it.
4. Copy each complete listed skill directory into the personal Codex skill directory. Preserve unrelated skills.
5. Validate that every skill is discoverable, its `SKILL.md` name matches its directory name, its local references resolve, and its explicit invocation policy is preserved.

At the end, report the bundle version, destination, installed or unchanged skills, replaced conflicts, validation results, and whether Codex needs a restart or session reload.
