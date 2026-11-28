---
name: sync
description: Pull the latest remote main into local main in the current repository. Use only when the user explicitly invokes /sync or $sync. Do not activate from a natural-language request alone.
disable-model-invocation: true
---

# Sync

Bring local `main` up to date with the remote without touching other work.

1. Confirm the current folder is inside a Git repository. If not, report that and stop.
2. Find the remote and default branch: use `origin` unless the repository has no `origin`, and use `main` unless the remote's default branch (`git remote show origin` or `refs/remotes/origin/HEAD`) is named differently, such as `master`.
3. Run `git fetch --prune` for that remote.
4. Fast-forward local `main` only; never merge, rebase, reset, or stash to get there.
   - If `main` is checked out here, run `git pull --ff-only`. Uncommitted changes that would be overwritten block the update: report them and stop.
   - If `main` is checked out in another worktree (`git worktree list`), run `git -C <that worktree> pull --ff-only`.
   - Otherwise update the ref without switching branches: `git fetch <remote> main:main`.
   - If local `main` does not exist yet, create it tracking the remote branch without checking it out.
5. If local `main` has diverged from the remote, stop and report the commits unique to each side. Do not resolve it unless the user asks.
6. Leave the current branch as it is. Do not rebase or merge it onto `main` unless the user asks.

Report the old and new `main` commits (or that it was already up to date), how many commits came in, and the current branch with how far it is behind the new `main`.
