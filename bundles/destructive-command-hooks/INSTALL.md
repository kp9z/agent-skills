# Install destructive-command lifecycle hooks

Use this instruction with an agent that supports a command hook before shell
tool execution.

## Install

1. Read [`manifest.json`](manifest.json). Determine the active harness and
   select only its adapter unless the user explicitly requests more than one.
2. Open the current official hook documentation linked in the selected adapter.
   Confirm the event name, matcher, command-handler shape, input payload, denial
   output, configuration path, and trust behavior. If the bundled adapter is no
   longer compatible, stop and explain the mismatch instead of guessing.
3. Inspect the existing user configuration and hook script destination. Preserve
   every unrelated setting, event, matcher group, and hook handler.
4. Copy [`shared/destructive_commands.py`](shared/destructive_commands.py) to
   the selected adapter's `script` path. If a different file already exists,
   compare it and ask before replacing it.
5. Treat the selected JSON fragment as a merge fragment, never as a complete
   replacement file. Add its `PreToolUse` Bash matcher idempotently. Do not add
   a duplicate handler when the same command is already configured.
6. If existing JSON is invalid or its hook structure cannot be merged safely,
   stop and explain the problem. Never overwrite it with the fragment.
7. Run `python3 tests/test_destructive_commands.py` from this bundle before
   installation, then repeat the tests against the installed script.
8. Parse the final JSON configuration and verify all prior unrelated content is
   still present. Inspect the harness hook browser if one is available.
9. For Codex, leave the new non-managed hook untrusted. Tell the user to open
   `/hooks`, review the exact definition, and trust it before use.
10. For Claude Code, tell the user to open `/hooks` and inspect the user-sourced
    hook.

For an unlisted harness, install only if its official documentation confirms a
compatible pre-shell command hook. Add a new adapter under `harnesses/` rather
than changing the shared hook. Stop if the harness cannot express the same
input and denial contract.

At the end, report the bundle version, selected adapter, files changed, merge
result, test results, hook-browser result, and any trust action still required.
