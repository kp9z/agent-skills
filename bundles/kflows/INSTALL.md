# Install kFlows

Install this collection from a local checkout of `kp9z/agent-skills`. Read
[manifest.json](manifest.json) for the complete list of skills and their sources.
The engineering skills are adapted from the recorded Matt Pocock v1.3.2
installation; preserve [its MIT license](LICENSE). Install this curated payload
as recorded. An upstream refresh is separate maintenance work because replacing
it with upstream files would discard the kFlows setup and triage customizations.

## Install

1. Resolve the active harness's project skill directory; for Codex, use
   `.agents/skills`. Inspect every destination. Leave identical skills unchanged,
   preserve unrelated skills, and show differing copies before replacing them.
   The user's explicit update request may already authorize those replacements.
2. Verify every manifest skill directory, then copy each complete directory,
   including references, scripts, templates, metadata, and executable modes.
   Keep the skills together so their sibling references resolve.
3. Run `$setup-kflows` in the target repository to configure GitHub Issues,
   triage labels, and the root `AGENTS.md`. Follow the included setup workflow;
   preserve existing project instructions and resolve conflicting conventions.
   Triage is available as `$setup-kflows triage`, not a separate skill.
4. Preserve explicit invocation policies. `to_ticket_yolo` uses the included
   `to-spec` and `to-tickets` skills and intentionally skips their approval pauses
   when explicitly invoked. `grill-me-in-batch` uses the included `grilling` skill.
5. `ticket_marathon` requires the included `implement`, testing and review skills,
   GitHub tracker configuration, and Codex chat tools (plus scheduling tools in
   scheduled mode). It runs sequential
   batches of up to three tickets with scheduled continuation after 4 hours 30 minutes
   or immediate continuation when the user requests continuous mode.
   In scheduled mode, report unavailable scheduling rather than claiming unattended continuation.
6. Copy all `harness_improver` scripts, references, and helper tests. Its helpers
   need Python 3; GitHub CLI operations also need authenticated `gh`. Run its
   offline checks with `python3 -m unittest discover -s <skill-directory>/tests`.
7. `merge-to-local-main` needs Git and authenticated push access. Install it with
   the other project skills by default; use `$CODEX_HOME/skills` or
   `~/.codex/skills` only when the user requests personal availability.
8. Verify all manifest skills are discoverable, their names match their folders,
   bundled references resolve, generated project links resolve, and `AGENTS.md`
   contains one Agent skills section. Check the configured GitHub repository and
   label mapping, preserving unrelated settings.

Report the bundle version, destinations, installed/unchanged skills, resolved
conflicts, setup changes, validation results, and any required session reload.
