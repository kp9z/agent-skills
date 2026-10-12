---
name: merge_and_archive
description: Merge the current chat's work into main, then archive the chat. Use only when the user explicitly invokes /merge_and_archive or $merge_and_archive. Do not activate from a natural-language request alone.
---

# Merge and Archive

Merge the current chat's branch or pull request into `main` and push the result, following the repository's required checks and merge rules. Include only this chat's work.

After confirming the merge reached remote `main`, archive the current chat with `mcp__codex_app__set_thread_archived` using `archived: true` and no `threadId`.

If merging or pushing fails, keep the chat open and report the blocker. If archiving is unavailable, report the successful merge and the archive limitation.
