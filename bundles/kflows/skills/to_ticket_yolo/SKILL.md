---
name: to_ticket_yolo
description: Run to-spec then to-tickets and publish the spec and linked issues without approval pauses.
disable-model-invocation: true
---

# Spec to tickets, YOLO

Invoking this skill authorizes publishing the requested spec and its implementation tickets to the project's GitHub Issues without further approval. Apply this authorization to this workflow only.

## Workflow

1. Read the installed `to-spec` and `to-tickets` skills (Core bundle dependencies). Execute their workflows in that order, with the approval overrides below. Read the project's configured tracker conventions, triage mapping, and domain rules before working with issues. Use the repository configured by the target project, not this skill collection. If either dependency or tracker configuration is missing, report what is needed before publishing. Use the current conversation and any supplied source reference as the scope.
2. Run **to-spec**: explore the relevant code, choose testing seams, and synthesize the spec using its template. Choose reasonable defaults for unresolved details and record material assumptions in the spec. Replace the testing-seam confirmation with your own review and proceed directly to publishing. Search for existing issues for the same work and read their full bodies and comments; reuse a matching spec rather than duplicate it.
3. Run **to-tickets** using the published spec issue as its source. Read its full body and comments. Draft verifiable vertical slices and blocking edges using the source skill's rules and templates. Replace its user quiz and approval loop with your own review of scope coverage, granularity, acceptance criteria, and dependencies; publish immediately after that review.
4. Publish one issue per ticket, blockers first, reusing matching tickets. Apply the canonical `ready-for-agent` label to fully specified work. Attach tickets as sub-issues of the spec and create native blocking relationships, using the tracker conventions' body-link fallback when necessary. Preserve the parent spec's body and open status during ticket publication.
5. Verify the published spec, tickets, labels, parent links, and blockers. Return the spec link and a compact list of ticket links with their blockers and any material assumptions.

## Boundaries

- Complete drafting and review autonomously; skip spec, testing-seam, ticket-breakdown, and publishing approval requests inherited from the source skills or tracker conventions.
- Keep publication within the requested scope. This workflow ends after publishing and verification; implementation, closing issues, and pushing code require their own authorization.
- If context is too incomplete to define meaningful work, ask only for the missing requirement. For unavailable credentials or permissions, report the blocker and any issues already published. After an uncertain API result, inspect the tracker before retrying so a partial run creates no duplicates.
