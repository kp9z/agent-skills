# Install kFlows

Install this collection from a local checkout of `kp9z/agent-skills`. Read
[manifest.json](manifest.json) for the complete list of skills and their sources.
The engineering skills are adapted from the recorded Matt Pocock v1.3.2
installation; preserve [its MIT license](LICENSE). Install this curated payload
as recorded. An upstream refresh is separate maintenance work because replacing
it with upstream files would discard the kFlows setup and triage customizations.

## Install

1. For Codex, install kFlows at user level in `~/.agents/skills` by default.
   Preserve an explicitly requested alternative destination. Keep project-specific
   `AGENTS.md` and `docs/agents/` in each target repository. Inspect both the user
   destination and legacy project/`~/.codex/skills` copies. Leave identical skills unchanged,
   preserve unrelated skills, and show differing copies before replacing them.
   The user's explicit update request may already authorize those replacements.
   When migrating, back up affected legacy copies outside all skill discovery
   folders, then remove superseded duplicate skills and old installation records
   only within the authorized projects/user directories. Preserve unrelated skills.
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
   the other user-level kFlows skills; its Git commands operate in the target
   project checkout, not the installation directory.
8. `sync_skills` needs read access to installed skills and authenticated push/PR
   access to `kp9z/agent-skills`. Preserve its explicit-only invocation policy.
   It publishes local updates through a review branch, without merging or
   modifying installations.
9. Verify all manifest skills are discoverable, their names match their folders,
   bundled references resolve, generated project links resolve, and `AGENTS.md`
   contains one Agent skills section. Record the collection repository URL, source
   commit, installed names and file hashes in a local installation receipt outside
   skill folders; compare installed contents and modes against that commit.
   Check the configured GitHub repository and
   label mapping, preserving unrelated settings.

Report the bundle version, destinations, installed/unchanged skills, resolved
conflicts, setup changes, validation results, and any required session reload.
