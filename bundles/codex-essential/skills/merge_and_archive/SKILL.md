---
name: merge_and_archive
description: Merge the current chat's work into main, then archive the chat. Use only when the user explicitly invokes /merge_and_archive or $merge_and_archive. Do not activate from a natural-language request alone.
---

# Merge and Archive

Include only this chat's work and follow the repository's required checks and merge rules.

1. Pull remote `main` into local `main` with a fast-forward-only update so local `main` is up to date. If `main` is checked out in another worktree, update it there. If local `main` has diverged, stop and report the blocker.
2. Rebase the current chat's branch onto the updated local `main`. Resolve conflicts while preserving the intended behavior of both sides, and complete the rebase before testing.
3. Before the full suite, map the rebased changes and conflict resolutions to affected tests and required checks. Include direct callers and shared flows; use broader coverage when impact is uncertain. Run these checks first. Fix failures with focused reruns until all affected checks pass. Verify selected tests actually executed; retain failure evidence and passing result bundles.
4. Then run the full test suite and required checks unless they already passed for the exact rebased code being merged. If it fails, diagnose and fix the failure, verify the fix with affected checks first, then run the full suite on the final code. If an error cannot be resolved, keep the chat open and report the blocker. Use runner progress and completion receipts for elapsed time and remaining tests; inspect detailed logs on failure or a stall instead of repeatedly reading log tails. Report milestones and actionable failures without narrating each test.
5. Merge the verified branch into local `main` and push `main` to the remote. If remote `main` advances before the push, repeat the sync, rebase, and verification steps before retrying. Respect branch protections; if the repository requires a pull request, follow that merge path instead.
6. Confirm the merged work reached remote `main`, then archive the current chat with `mcp__codex_app__set_thread_archived` using `archived: true` and no `threadId`.

If merging or pushing fails, keep the chat open and report the blocker. If archiving is unavailable, report the successful merge and the archive limitation.
