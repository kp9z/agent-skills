# Install the kp9z skills

Use this instruction inside the target repository. The installing agent must
have access to a local checkout of `kp9z/agent-skills` containing this file.

## Install

1. Determine the active agent harness and its skill directory. For Codex and
   Claude Code, use the harness's documented project-local location. For
   Hermes Agent, use `~/.hermes/skills/<skill-name>` because Hermes does not
   discover a project's `.agents/skills` directory by default. For another
   harness, use its documented location. Ask the user if the destination is
   uncertain.
2. Read [`manifest.json`](manifest.json) and verify every listed skill path.
3. Inspect each destination before copying. Leave identical skills unchanged.
   If an existing skill differs, show the conflict and ask before replacing it.
4. Copy each complete listed skill directory to the harness's project-local
   skill directory. Preserve unrelated skills.
5. Validate that both skills are discoverable, their `SKILL.md` names match
   their directory names, and every bundled reference resolves.

At the end, report the bundle version, destination, installed or unchanged
skills, replaced conflicts, validation results, and any required harness restart
or session reload.
