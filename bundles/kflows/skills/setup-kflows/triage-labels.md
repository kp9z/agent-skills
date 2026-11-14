# Triage Labels

Use one category and one state for each triaged issue. Preserve an existing
intentional mapping; the defaults below use canonical names directly.

| Canonical role | GitHub label | Meaning |
| --- | --- | --- |
| `bug` | `bug` | Existing behavior is broken |
| `enhancement` | `enhancement` | New feature or improvement |
| `needs-triage` | `needs-triage` | Maintainer needs to evaluate |
| `needs-info` | `needs-info` | Waiting for more information |
| `ready-for-agent` | `ready-for-agent` | Fully specified for agent implementation |
| `ready-for-human` | `ready-for-human` | Requires human implementation |
| `wontfix` | `wontfix` | Will not be actioned |

`$setup-kflows` creates missing mapped labels. `$setup-kflows triage` uses this
mapping when labeling issues; preserve unrelated labels.
