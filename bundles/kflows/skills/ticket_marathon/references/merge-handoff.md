# Merge handoff

When Git reports a conflict, prepare an isolated worktree and branch at the
exact integration tip. Preserve the worker’s tested commit and use the
[ownership contract](ownership.md) to assign the new worktree to the original
ticket chat. Have that worker merge the exact commits and preserve their
ancestry.

Give the worker both sides of the merge.

- The exact integration and ticket commits, checkout, branch, and resource
  grant. Identify the issues whose changes overlap and link their acceptance
  criteria and relevant review or test receipts.
- The conflicting files and any related code Git merged automatically. Explain
  what each ticket was trying to change, what behavior it must preserve, and
  which edge cases or regression checks should prove both still work together.
- The verification required for this combination. Use focused checks for the
  affected production behaviors, required project-wide checks, and independent
  review of the resolution. Follow the project’s rules for native tests.

For example, a sensor ticket may let an early Start tap queue and save exactly
one report in either completion order. A Care ticket may use that same report
to suppress a repeat-check prompt for its owner. Ask the worker to preserve both
test cases and inspect the shared report path even if Git only flags their
tests. If the documented requirements genuinely disagree, keep both commits
and surface the specific product decision.

Have the worker return the clean merge commit, its ancestry, how the overlap
was resolved, evidence for both behaviors, and any remaining blocker. Confirm
that the verified result still applies to the current integration tip before
landing it.
