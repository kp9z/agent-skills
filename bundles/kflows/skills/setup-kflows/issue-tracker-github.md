# Issue tracker: GitHub

Store specs and work items in [OWNER/REPO GitHub Issues](https://github.com/OWNER/REPO/issues).
Use this verified repository explicitly for every operation, including when the
working directory belongs to the skill collection rather than the target project.
Use connected GitHub tools when sufficient, or the authenticated `gh` CLI.

## Conventions

- Create one issue per specification or ticket. For CLI writes, save multiline
  bodies to a temporary file and use `gh issue create --repo OWNER/REPO --body-file PATH`.
- Read the full issue and its comments before changing it; page through results
  when needed. `gh issue view NUMBER --repo OWNER/REPO --comments` reads one issue.
- List with `gh issue list --repo OWNER/REPO` and suitable state/label filters.
  Fetch all pages when the workflow needs the entire queue.
- Comment with `gh issue comment NUMBER --repo OWNER/REPO --body-file PATH`.
- Apply or remove labels with `gh issue edit NUMBER --repo OWNER/REPO
  --add-label LABEL --remove-label OLD_LABEL`, using the configured triage mapping.
- Close only when authorized by the current workflow and record the appropriate
  completion or rejection reason. Closing alone does not prove implementation.
- Link tickets as sub-issues of their specification and record native blocking
  dependencies when supported. If unavailable, use explicit `Part of #NUMBER`
  and `Blocked by #NUMBER` links in issue bodies.
- After an uncertain write result, read live state before retrying to avoid
  duplicate issues or comments.

## Pull requests as a triage surface

**PRs as a request surface: no.** `$setup-kflows triage` reads this flag. An
explicit request for a particular PR can still be handled.

When enabled, read the PR body, comments, labels, and diff. Discover external
requests using author association `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or
`NONE`; a collaborator's in-flight PR is not automatically triage work.
GitHub shares issue and PR numbers, so resolve a bare number before acting.
Use the corresponding connected tools or `gh pr` commands for PR operations.

## Workflow meanings

"Publish to the issue tracker" means create a GitHub issue in OWNER/REPO.
"Fetch the relevant ticket" means read that GitHub issue and its comments.
