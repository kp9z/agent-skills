# Install Build iOS Apps

This bundle preserves the complete upstream plugin. Read [manifest.json](manifest.json)
and [UPSTREAM.md](UPSTREAM.md) before installing.

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
   unchanged skills, MCP changes, and any required session reload.

Simulator, build, and profiling workflows require a Mac with Xcode and suitable
Simulator runtimes. The MCP command requires Node.js and npx. Browser mirroring
also requires the browser tools described by its skill. Do not run bundled
scripts or install dependencies merely to copy this bundle.

For native plugin installation, use the complete bundle directory as the plugin
root through the host's supported plugin installation workflow. Keep
`.codex-plugin`, `.mcp.json`, `agents`, `assets`, and `skills` together.
