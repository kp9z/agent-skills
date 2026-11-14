# Install kFlows

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
5. For `to_ticket_yolo`, verify that the target environment also has Core's
   `to-spec` and `to-tickets` skills and project tracker configuration. If missing,
   follow [`../core/INSTALL.md`](../core/INSTALL.md) for the dependencies and its
   setup instructions for tracker configuration before using the workflow.
   Preserve `disable-model-invocation: true` and Codex's
   `policy.allow_implicit_invocation: false`; this skill is user-invoked only.
6. For `ticket_marathon`, verify Core's `implement` skill and its testing and
   review dependencies, project tracker configuration, and Codex app scheduling
   tools are available. Preserve both explicit-only invocation flags. Each batch
   implements up to three dependency-ready tickets sequentially; continuations
   run 4 hours 30 minutes after batch completion. On a harness without compatible
   scheduling tools, report that unattended continuation is unavailable.
7. For `grill-me-in-batch`, verify Core’s `grilling` skill is installed beside
   it. If missing, follow [`../core/INSTALL.md`](../core/INSTALL.md) for that
   dependency before using the interview. Preserve `disable-model-invocation:
   true` and Codex’s `policy.allow_implicit_invocation: false`; this skill is
   user-invoked only.
8. For `harness_improver`, preserve both explicit-only invocation flags and copy
   the complete directory, including scripts, references and helper tests. Python 3
   is required; GitHub operations additionally require authenticated `gh`. Chat
   inspection uses available chat tools or explicitly supplied local exports.
   No audit implicitly authorizes mutations or publishing. Run its offline checks
   with `python3 -m unittest discover -s <skill-directory>/tests`.
9. For `merge-to-local-main`, preserve its explicit-only invocation policy in
   `agents/openai.yaml`. It requires Git and authenticated push access. Copy it
   into the project skill directory by default; when requested across projects,
   use `$CODEX_HOME/skills` or `~/.codex/skills` for Codex.
10. Validate that all listed skills are discoverable, their `SKILL.md` names match
   their directory names, and every bundled reference resolves.

At the end, report the bundle version, destination, installed or unchanged
skills, replaced conflicts, validation results, and any required harness restart
or session reload.
