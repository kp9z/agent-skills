# Portable Destructive Command Hooks Design

## Goal

Add a reusable, testable installer to `kp9z/agent-skills` that configures the
same destructive-command `PreToolUse` policy for personal Codex and Claude Code
installations on another machine without overwriting unrelated configuration.

## Supported clients

### Codex

- Merge a `PreToolUse` matcher for `Bash` into `~/.codex/hooks.json`.
- Install the runtime hook script at
  `~/.codex/hooks/destructive_commands.py`.
- Use a portable Python invocation in the command hook.
- Tell the user to open `/hooks`, review the non-managed hook, and explicitly
  trust it before it can run.

### Claude Code

- Merge a `PreToolUse` matcher for `Bash` into
  `~/.claude/settings.json`.
- Install the runtime hook script at
  `~/.claude/hooks/destructive_commands.py`.
- Use Claude Code's command-hook configuration and the documented
  `hookSpecificOutput` denial shape.
- Tell the user to open `/hooks` to inspect the installed user hook. Claude
  Code's `/hooks` browser is read-only and does not use Codex's hook-trust
  workflow.

## Repository layout

```text
hooks/
  destructive_commands.py
scripts/
  install_destructive_command_hooks.py
tests/
  test_destructive_command_hooks.py
README.md
```

`hooks/destructive_commands.py` is the shared runtime policy. The installer
copies it into each client's stable user-level hook directory so the installed
configuration does not depend on where the repository was cloned.

## Command policy

The runtime hook reads one JSON object from standard input and inspects
`tool_input.command`. It must not execute or expand any part of the command.
It splits shell command segments while respecting quoted text, so a command
such as `echo ok; rm -rf /` is denied while a quoted string containing
`rm -rf /` is not treated as an executed segment.

The following prefixes and exact reasons are denied:

| Prefix | Reason |
| --- | --- |
| `rm -rf /` | Never delete the root filesystem. |
| `rm -rf /*` | Never delete the contents of the root filesystem. |
| `rm -rf ~` | Never delete the entire home directory. |
| `rm -rf $HOME` | Never delete the entire home directory. |
| `rm -rf /Users` | Never delete all user directories. |
| `rm -rf /System` | Never delete macOS system files. |
| `diskutil eraseDisk` | Never erase or repartition a disk. |
| `diskutil eraseVolume` | Never erase or repartition a disk. |
| `diskutil partitionDisk` | Never erase or repartition a disk. |
| `mkfs` | Never format a filesystem. |

For a denied command, the script writes:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}
```

Safe commands, missing command fields, and malformed JSON produce no output and
exit successfully so they do not interfere with normal tool use.

## Installer interface

The installer is dependency-free Python and supports:

```bash
python3 scripts/install_destructive_command_hooks.py --codex
python3 scripts/install_destructive_command_hooks.py --claude
python3 scripts/install_destructive_command_hooks.py --all
```

`--all` installs both clients and is the README's recommended command.

For each selected client, the installer:

1. Creates the required user hook directory.
2. Copies the shared policy script with user-only writable permissions.
3. Reads the existing JSON configuration if present.
4. Preserves every unrelated top-level field, event, matcher group, and hook
   handler.
5. Adds the managed destructive-command handler only when an equivalent
   handler is not already present.
6. Writes formatted JSON atomically.
7. Prints the files changed and the client-specific `/hooks` follow-up.

If an existing configuration file is invalid JSON or has an incompatible
`hooks` structure, the installer exits with an actionable error and makes no
change to that file. It does not silently replace malformed configuration.

## Idempotency and merging

Running the same installation option repeatedly must not create duplicate
matcher groups or handlers. If a compatible `PreToolUse` Bash group already
exists, the installer appends only the missing handler. Existing hooks remain
in their original order.

The Codex and Claude configurations use client-specific installed script paths,
so the hook commands are not shared verbatim even though the runtime policy is.

## Verification

Automated tests use temporary home directories and never run destructive shell
commands. They verify:

- every listed prefix is denied with its exact reason;
- each prefix is also denied after a safe shell segment;
- representative safe commands are allowed;
- destructive text inside quoted arguments is allowed;
- malformed and incomplete hook payloads are allowed;
- fresh Codex, Claude, and combined installations create valid JSON;
- existing unrelated settings and hooks survive installation;
- a second installation is byte-for-byte or structurally idempotent;
- invalid existing JSON fails without modifying the source file.

The README documents these local checks:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile hooks/destructive_commands.py \
  scripts/install_destructive_command_hooks.py
```

It also documents product-level inspection:

- Codex: open `/hooks`, review the `PreToolUse` Bash hook, and trust the
  non-managed hook.
- Claude Code: open `/hooks` and inspect the user-sourced `PreToolUse` Bash
  hook.

## Scope boundaries

- Do not add or modify Codex execution-policy rule files.
- Do not configure project-local hooks.
- Do not trust the Codex hook automatically.
- Do not alter existing hook behavior beyond adding the new handler.
- Do not require third-party Python packages.
- Do not automatically install Codex or Claude Code themselves.
