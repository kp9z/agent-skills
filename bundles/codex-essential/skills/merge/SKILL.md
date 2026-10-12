---
name: merge
description: Merge the current chat's work into main, then archive the chat. Use when the user invokes /merge or $merge, or asks to merge and archive.
---

# Merge

Merge the current chat's branch or pull request into `main` and push the result, following the repository's required checks and merge rules. Include only this chat's work.

After confirming the merge reached remote `main`, archive the current chat with `mcp__codex_app__set_thread_archived` using `archived: true` and no `threadId`.

If merging or pushing fails, keep the chat open and report the blocker. If archiving is unavailable, report the successful merge and the archive limitation.
