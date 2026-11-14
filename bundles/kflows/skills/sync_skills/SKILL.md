---
name: sync_skills
description: Publish newer locally installed versions of this collection's skills to kp9z/agent-skills when explicitly invoked by the user.
disable-model-invocation: true
---

# Sync skills

Run only on explicit `$sync_skills` or `/sync_skills` invocation. This authorizes
comparing installed skills and publishing supported local updates to
[the skill collection](https://github.com/kp9z/agent-skills) on a review branch
and pull request. It does not authorize merging the PR or updating installations.

## Scope and source

By default, inspect installed skills that appear in the target collection's
bundle manifests. Optional skill names narrow the scope, for example
`$sync_skills ticket_marathon` or `$sync_skills ticket_marathon ios-testing`.
A supplied local path selects that copy of a named skill.

Resolve actual installed locations from the available skill inventory, current
project skill folders, and user skill folders. Inspect `~/.agents/skills` and
`$CODEX_HOME/skills` (or `~/.codex/skills`) as applicable; deduplicate symlinks by
resolved path. Multiple differing copies of the same skill require selection
from the user or current session evidence. Do not choose by filesystem timestamp.
Keep the target project checkout and all installed skills unchanged.

## Compare with the collection

1. Fetch the repository's default branch and manifests into an isolated checkout,
   or read its exact current commit through the GitHub tools. Read its agent and
   contribution instructions. Use manifests to map skill names to bundle paths;
   installed directory layout does not determine the remote destination. Respect
   a review branch explicitly selected by the user, including structural changes
   already agreed there, instead of recreating a removed bundle.
2. Compare each complete skill directory: instructions, references, scripts,
   templates, assets, metadata, and executable modes. Exclude installation-local
   receipts, caches, logs, credentials, bytecode, and Git internals. Identical
   content and modes mean no update, regardless of version labels or timestamps.
3. Establish which copy is newer from a recorded installation commit and its
   historical skill contents, an explicit skill version, Git history, or a local
   edit the user authorized in this session. A bundle version or upstream-source
   version alone does not prove which copy of a customized skill is newer.
   Where a common baseline exists, compare both copies against it: local-only
   changes are update candidates; remote-only changes stay remote; divergent
   changes need reconciliation. If provenance is missing and neither version
   nor session evidence establishes direction, show the difference and ask which
   copy to publish rather than treating every local difference as an upgrade.
4. Report candidates, identical skills, remote-newer copies, and conflicts.
   Proceed with established local updates without an extra approval pause.
   Preserve remote improvements when reconciling; ask about contradictory intent.
   A skill missing locally is not a deletion request. A local skill absent from
   the selected manifests is not automatically added. Explicitly requested new
   skills need an agreed bundle destination before publishing.

## Prepare and publish

5. Copy only selected skill changes into a clean `codex/` branch of the collection.
   Keep complete directories together. Reflect intentional file removals inside
   an updated skill when the baseline establishes them. Resolve dependencies on
   external shared helpers by including the required portable resources or
   recording the dependency; a skill referencing an unshipped local `_shared`
   directory is not a complete update. Preserve licenses and source attribution.
6. Update affected manifests, versions, source/adaptation metadata, and docs only
   as needed to describe the actual change. Preserve curated names, bundle
   organization, and invocation policies. Do not replace the collection's setup
   customizations with an older installed upstream copy.
7. Validate skill and UI YAML, matching names/folders, unique manifest entries,
   paths and relative references. Run relevant existing checks for changed
   scripts and meaningful behavior; inspect the staged diff for unrelated files
   and local-only data. Commit a focused change.
8. Fetch the target branch again before publishing. If it advanced, reconcile
   against its new contents and repeat affected validation. Push the review
   branch without force and create or update a PR describing the actual updates
   and checks. An existing PR may be reused only when selected by the user or
   established by the active session. Verify the remote commit and PR result.
   On an uncertain write result, inspect remote state before retrying.

If no supported update exists, report a no-op without creating a commit or PR.
If access or validation fails, report the blocker and any already-published
branch/PR; leave the user's local installations intact. Finish with the source
paths, updated skills, unresolved differences, checks, commit, and PR link.
