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
4. Resolve upstream metadata for every selected entry:
   - Entries with `upstreamPath` use the catalog-level `upstream` and `bundled`
     metadata. Run `git ls-remote --refs --tags` for the repository and compare
     the highest stable semantic-version tag matching `releaseTagPattern` with
     `bundled.tag`.
   - Entries with an `upstream` object are independently pinned. Run
     `git ls-remote <repository> refs/heads/<ref>` and compare the result with
     the entry's `upstream.commit`.
   - If a newer upstream revision exists, ask whether to use that exact
     revision. If a check fails, ask whether to continue with the bundled
     snapshot.
   - When using upstream, copy only the selected entry's upstream path and
     retain any bundled license or harness metadata files.
5. Inspect each selected destination. Leave identical skills unchanged. Show
   any differing destination and ask before replacing it. Preserve every
   unrelated skill.
6. Copy each selected complete skill directory. Installing a supplement leaves
   Core, Plus, and every unselected supplement unchanged.
7. Validate that every selected skill is discoverable by the active harness and
   that its complete directory contents were copied.

Report the requested names, selected version or revision, destination,
installed or unchanged skills, replaced conflicts, and validation results.
Mention any harness restart or session reload needed before the skills become
visible.
