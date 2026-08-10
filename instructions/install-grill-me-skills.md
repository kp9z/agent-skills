# Install the grill-me engineering workflow

Use this instruction inside a freshly created GitHub repository with either Codex or Claude Code.

```text
Bootstrap this repository with the grill-me engineering workflow.

Use these sources:

- Matt Pocock's skills: https://github.com/mattpocock/skills
- Personal skills: https://github.com/kp9z/agent-skills

Determine which agent is running. Configure only that agent unless I explicitly
ask for both:

- Codex: use AGENTS.md.
- Claude Code: use CLAUDE.md.

Preserve existing instructions and unrelated configuration. If the selected
agent file does not exist, create it before running the setup skill so the setup
updates the correct file.

1. Verify this is a Git repository with a GitHub origin. Verify `git`, `gh`,
   Node.js, and `npx` are available, and verify `gh auth status` succeeds. Stop
   with a clear explanation if any prerequisite is missing.
2. Install Matt Pocock's skills using the current installation method documented
   at https://github.com/mattpocock/skills. Do not install the same collection
   through both the Claude Code plugin and skills.sh.
3. Ensure the installed collection includes at least:
   `setup-matt-pocock-skills`, `triage`, `grill-me`, `grilling`,
   `improve-codebase-architecture`, `codebase-design`, `domain-modeling`,
   `writing-for-agents`, `to-spec`, `to-tickets`, `tdd`, `implement`, and
   `code-review`. Install any dependencies declared by those skills too.
4. Install `skill-maintenance` from https://github.com/kp9z/agent-skills using
   the current skills.sh installer. Avoid replacing an existing skill without
   inspecting it and asking me first.
5. Run `setup-matt-pocock-skills` for this repository. Choose GitHub Issues as
   the issue tracker, keep the default triage label vocabulary, and use the
   recommended single-context domain-doc layout unless the repository has real
   monorepo signals. Complete the setup rather than merely describing it.
6. Ensure these GitHub labels exist without deleting or changing unrelated
   labels: `bug`, `enhancement`, `needs-triage`, `needs-info`,
   `ready-for-agent`, `ready-for-human`, and `wontfix`. Reuse matching labels;
   create only missing ones with `gh label create`.
7. Confirm the selected agent file contains one `## Agent skills` section that
   points to the generated issue-tracker, triage-label, and domain documentation.
   Codex must finish with AGENTS.md. Claude Code must finish with CLAUDE.md.
8. Validate that every required skill is discoverable by the running agent,
   every generated documentation link resolves, the issue tracker says GitHub,
   and the triage label mapping matches the GitHub labels. Do not create a test
   issue or mutate existing issues during validation.

At the end, list installed skills, files changed, labels created or reused, and
every validation result. Mention any restart or session reload needed before new
skills become visible.
```
