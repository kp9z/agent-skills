---
name: free_space
description: Reclaim disk space on this Mac by clearing known rebuildable caches, then offering larger cleanups for confirmation. Use for /free_space, cache cleanup, or a read-only estimate of reclaimable space.
---

# Free space

For `/free_space`, `$free_space`, or a request to clean up disk space, run the installed helper once:

```sh
/usr/bin/python3 -I ~/.agents/skills/free_space/scripts/cleanup.py --apply
```

For a question about what can be cleaned, or a request for a preview, omit `--apply`. Run with the current user's ordinary macOS permissions and request sandbox access when needed to inspect processes or clear user caches.

The helper selects generated Xcode build products and compiler caches, package download caches, and closed browsers’ HTTP and code caches. Its allowlist is the boundary for automatic deletion.

## Report, then offer the confirmation list

1. Report the measured change in free space, current free space, and any skipped or failed groups. A busy group can be cleaned on a later invocation.
2. Present the helper's **Needs confirmation** section as a table: size, item, and what deleting it costs. Recommend an order, no-risk items such as unavailable simulators first. Then end the turn and wait: each item is deleted only after the user picks it.
3. For each item the user picks, verify before deleting, then measure free space before and after:
   - **Unavailable simulators**: `xcrun simctl delete unavailable`.
   - **Leftover /private/tmp folders**: find every nested `.git`. Delete only when each is a Git worktree (`.git` is a file) with a clean `git status`, or a clone whose branches are all pushed. Afterwards run `git worktree prune` in each main repository those worktrees named. A folder holding uncommitted or unpushed work goes back to the user with its path and state.
   - **Docker data**: `docker system prune` with Docker running, after the user sees what it removes.
   - **Device support, archives, updater caches, Codex visualizations**: delete the listed folders.
   - Anything else (simulator devices still available, worktrees under a project, application profiles) needs its own specific request.
4. Report what was deleted, the space freed, and what is left on the list.
