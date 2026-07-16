# Install destructive-command lifecycle hooks

Use this instruction with either Codex or Claude Code on a new machine.

```text
Set up a real lifecycle hook that blocks a small list of destructive shell
commands. Follow the current official hook documentation for the agent you are
running in:

- Codex: https://learn.chatgpt.com/docs/hooks
- Claude Code: https://code.claude.com/docs/en/hooks

Determine which agent is running:

- If you are Codex, install the Codex configuration described below.
- If you are Claude Code, install the Claude Code configuration described
  below.
- Install both only if I explicitly ask for both.

Do not implement this only as a command-execution rules or permissions file.
Use a real PreToolUse command hook with a Bash matcher.

Before changing anything, inspect the existing hook configuration and preserve
it. Do not modify unrelated configuration.

For Codex:

1. Create or merge ~/.codex/hooks.json.
2. Add a PreToolUse matcher for Bash.
3. Create ~/.codex/hooks/destructive_commands.py.
4. Configure the command hook to invoke it with portable Python, for example:
   /usr/bin/env python3 "$HOME/.codex/hooks/destructive_commands.py"
5. Preserve every existing event, matcher group, hook handler, and unrelated
   top-level field.

For Claude Code:

1. Create or merge ~/.claude/settings.json.
2. Add a PreToolUse matcher for Bash under the existing "hooks" field.
3. Create ~/.claude/hooks/destructive_commands.py.
4. Configure the command hook to invoke it with portable Python, for example:
   /usr/bin/env python3 "$HOME/.claude/hooks/destructive_commands.py"
5. Preserve every existing setting, event, matcher group, and hook handler.

The Python script must:

- read the hook JSON payload from stdin;
- inspect tool_input.command;
- never execute, expand, source, or evaluate the inspected command;
- handle shell command segments such as:
  echo ok; rm -rf /
  npm test && diskutil eraseDisk disk-name GPT /dev/disk9
- avoid treating destructive text inside a quoted argument as an executed
  command segment;
- exit successfully with no output when the command is safe or the payload is
  malformed or incomplete;
- emit the documented PreToolUse denial JSON when a blocked command is found.

Block these command prefixes with the exact listed reasons:

- rm -rf / — Never delete the root filesystem.
- rm -rf /* — Never delete the contents of the root filesystem.
- rm -rf ~ — Never delete the entire home directory.
- rm -rf $HOME — Never delete the entire home directory.
- rm -rf /Users — Never delete all user directories.
- rm -rf /System — Never delete macOS system files.
- diskutil eraseDisk — Never erase or repartition a disk.
- diskutil eraseVolume — Never erase or repartition a disk.
- diskutil partitionDisk — Never erase or repartition a disk.
- mkfs — Never format a filesystem.

Return this denial shape:

{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}

Make the merge idempotent: rerunning this instruction must not duplicate the
hook. If the existing JSON is invalid or its hooks structure is incompatible,
stop and explain the problem instead of overwriting it.

Validate without executing any destructive command:

- parse the modified JSON configuration;
- compile the Python script;
- feed synthetic JSON fixtures for every blocked command;
- test every blocked command both directly and after a safe shell segment;
- feed representative safe commands and confirm they produce no output;
- confirm quoted destructive text is allowed;
- confirm malformed and incomplete payloads are allowed;
- confirm existing configuration was preserved;
- confirm the hook appears through the agent's /hooks command.

For Codex, leave the new non-managed hook untrusted. Remind me that I must open
/hooks, review the exact hook definition, and trust it before it can run.

For Claude Code, remind me to open /hooks and inspect the user-sourced hook.
Claude Code's /hooks browser is read-only and does not use Codex's trust step.

At the end, tell me exactly which files changed and summarize every validation
result.
```
