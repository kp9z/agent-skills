---
name: skill-maintenance
description: Audit an agent skill collection for duplicate skills, weak or overlapping trigger descriptions, stale context pointers, broken local references, invalid metadata, and inconsistent vocabulary. Use when maintaining a skills repository, reviewing skill quality, or cleaning up AGENTS.md and CLAUDE.md pointers across a project.
---

# Skill Maintenance

Audit the collection as a system. Preserve each skill's intent while reducing invocation ambiguity and maintenance drift.

## Process

1. Discover every `SKILL.md`, `agents/openai.yaml`, `AGENTS.md`, and `CLAUDE.md` in scope. Read the repository's contributing instructions before judging conventions.
2. Build an inventory containing each skill's name, folder, invocation mode, trigger description, referenced files, and UI metadata.
3. Check every item below. Cite file paths and lines for each finding.
4. Report findings by severity before editing. Separate definite defects from judgment calls.
5. If the user requested fixes, make the smallest coherent edits, preserve unrelated content, and validate the entire collection again.

## Checks

### Identity and invocation

- Skill folder and frontmatter `name` agree and use lowercase hyphen-case.
- No two installed skills expose the same name unless one is an intentional, documented override.
- Model-invoked descriptions state both the capability and the distinct situations that trigger it.
- User-invoked skills declare `disable-model-invocation: true` and keep their descriptions human-facing.
- Trigger descriptions do not overlap so broadly that several skills compete for the same ordinary request.

### References and metadata

- Every relative Markdown link and referenced local file resolves with exact filename casing.
- `agents/openai.yaml` matches the skill's current name, purpose, and invocation policy.
- Default prompts explicitly name the skill as `$skill-name`.
- AGENTS.md and CLAUDE.md pointers name real documents and state the branch of work that requires reading them.

### Language and maintenance

- Shared concepts use one term across related skills.
- Instructions have one source of truth instead of duplicated procedures that can drift.
- Stale references, obsolete commands, placeholders, and unreachable resources are removed or corrected.
- The main skill file contains ordered execution steps; branch-specific detail lives in directly linked references.

## Validation

Run the repository's existing validators first. When none exist, at minimum:

- parse every YAML frontmatter block and `agents/openai.yaml` file;
- verify skill names and folder names;
- resolve every relative Markdown link from its containing file;
- search for duplicate skill names;
- inspect the final diff for unrelated edits.

End with the inventory size, findings fixed, findings left for human judgment, and validation results.
