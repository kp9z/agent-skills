# Install Build iOS Apps

This bundle preserves the complete upstream plugin and adds the local
`ios-testing` skill. Read [manifest.json](manifest.json)
and [UPSTREAM.md](UPSTREAM.md) before installing.

## Check official updates before every installation

Original source: [OpenAI Build iOS Apps](https://github.com/openai/plugins/tree/main/plugins/build-ios-apps).

1. Read `source` in the bundle manifest. Resolve the official repository's
   `main` branch to an exact commit, then compare `plugins/build-ios-apps`
   at that commit with the bundled `source.commit`. Compare the directory's
   Git tree hash at both official commits, or the imported file hashes and
   modes excluding the local `ios-testing` addition, not just the plugin version
   or repository commit: unrelated repository changes are not plugin updates.
2. If the plugin differs, summarize the changes and ask whether to install
   that exact official snapshot or the bundled snapshot. Do not silently
   replace the bundled payload or overwrite local modifications.
3. When the user selects the official update, fetch the complete plugin
   directory at the resolved commit. Discover its skills and MCP configuration
   from that snapshot's plugin manifest, preserve all references and script
   permissions, and follow the installation steps below using that snapshot.
   The bundled skill list describes the pinned snapshot plus local additions.
   Always include the repository-owned `ios-testing` skill from this bundle
   when installing either snapshot. Preserve it separately during refreshes.
   If upstream introduces the same name, report the collision and resolve
   which version to install rather than silently overwriting either one.
4. If the source cannot be checked, report the failure and ask whether to
   continue with the bundled snapshot. Never claim it is current without
   checking. Report the selected source URL, exact commit, plugin version,
   and update-check result after installation.

## Install the selected snapshot

1. Determine the active harness and its documented skill directory. For Codex,
   use the project's `.agents/skills`; for Claude Code, use `.claude/skills`;
   for Hermes, use `~/.hermes/skills`. Resolve other harness destinations first.
2. Verify every skill path in the manifest. Inspect existing destinations, leave
   identical copies unchanged, and ask before replacing differing skills.
3. Copy each complete listed skill directory, including its references, agent
   metadata, scripts, and templates. Preserve executable permissions and unrelated skills.
4. For workflows requiring XcodeBuildMCP, merge the server entry from [.mcp.json](.mcp.json)
   into the harness's supported MCP configuration. Preserve existing settings
   and resolve conflicting server entries before changing them. Copying skills
   alone does not register this server. Read each skill for its tool requirements.
5. Verify skill discovery, names, bundled references, script permissions, and
   required tool availability. Report the version, destinations, installed or
   unchanged skills, MCP changes, and any required session reload. Distinguish the
   bundle version, official plugin version and commit, and local testing skill.

Simulator, build, and profiling workflows require a Mac with Xcode and suitable
Simulator runtimes. The MCP command requires Node.js and npx. Browser mirroring
also requires the browser tools described by its skill. Do not run bundled
scripts or install dependencies merely to copy this bundle.

For native plugin installation, use the complete bundle directory as the plugin
root through the host's supported plugin installation workflow. Keep
`.codex-plugin`, `.mcp.json`, `agents`, `assets`, and `skills` together. When
installing a newer official snapshot as a plugin, include the local
`ios-testing` directory in its `skills` directory after resolving any collision.
