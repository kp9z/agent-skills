---
name: free_space
description: Reclaim disk space on this Mac by clearing known rebuildable caches. Use for /free_space, cache cleanup, or a read-only estimate of reclaimable space.
---

# Free space

For `/free_space`, `$free_space`, or a request to clean up disk space, run the installed helper once:

```sh
/usr/bin/python3 -I ~/.agents/skills/free_space/scripts/cleanup.py --apply
```

For a question about what can be cleaned, or a request for a preview, omit `--apply`. Run with the current user's ordinary macOS permissions and request sandbox access when needed to inspect processes or clear user caches.

The helper selects generated Xcode build products and compiler caches, package download caches, and closed browsers’ HTTP and code caches. Its allowlist is the boundary for automatic deletion. Simulator devices, test results, archives, worktrees, saved patches, and application profiles require a separate, specific request.

Report the measured change in free space, current free space, and any skipped or failed groups. A busy group can be cleaned on a later invocation.
