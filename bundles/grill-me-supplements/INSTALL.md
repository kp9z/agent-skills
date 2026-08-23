# Install a Grill-me Supplement

This catalog provides optional skills that complement `grill-me`. Install only
the exact supplement names supplied by the user. With no named supplement,
list the names in [`manifest.json`](manifest.json) and stop.

## Install

1. Read [`manifest.json`](manifest.json). Resolve each user-supplied name to one
   manifest entry. If any name is absent, report the available names and stop.
2. Determine the active agent harness and its skill directory:
   - For Codex and Claude Code, use the harness's documented project-local
     skill directory.
   - For Hermes Agent, use `~/.hermes/skills/<skill-name>`.
   - For another harness, use its documented location.
   Ask when more than one destination is valid and the user has not selected
   one.
3. Verify every selected directory exists and contains its complete skill
   contents. The selection contains exactly the names supplied by the user.
4. Check for a newer stable upstream release:
   - Run `git ls-remote --refs --tags https://github.com/mattpocock/skills.git
     'refs/tags/v*'`.
   - Compare the highest stable semantic-version tag with `bundled.tag`.
   - If upstream is newer, ask whether to use that exact tag. If the check
     fails, ask whether to continue with the bundled release.
   - When using upstream, clone the selected tag and copy only each selected
     entry's `upstreamPath`.
5. Inspect each selected destination. Leave identical skills unchanged. Show
   any differing destination and ask before replacing it. Preserve every
   unrelated skill.
6. Copy each selected complete skill directory. Installing a supplement leaves
   Core, Plus, and every unselected supplement unchanged.
7. Validate that every selected skill is discoverable by the active harness and
   that its complete directory contents were copied.

Report the requested names, selected version, destination, installed or
unchanged skills, replaced conflicts, and validation results. Mention any
harness restart or session reload needed before the skills become visible.
