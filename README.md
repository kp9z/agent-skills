# Agent Skills

Personal Codex skills that can be installed across multiple machines.

## Available skills

### `plan-vertical-slices`

Plans and executes software builds as runnable, end-to-end vertical slices.

Each phase must:

- leave the application runnable;
- provide one user-observable capability;
- cross the necessary frontend, backend, and data layers;
- include an end-to-end check;
- include exact manual verification instructions;
- reach a clear done gate before the next phase.

Invoke it explicitly with:

```text
Use $plan-vertical-slices to plan and build this application.
```

Codex may also select it automatically for requests mentioning vertical slices,
phasal planning, walking skeletons, end-to-end milestones, or verifiable phases.

## Install on another machine

Clone this repository:

```bash
git clone https://github.com/kp9z/agent-skills.git "$HOME/agent-skills"
```

Create the personal skills directory:

```bash
mkdir -p "$HOME/.agents/skills"
```

Symlink the skill so repository updates become available automatically:

```bash
ln -s "$HOME/agent-skills/skills/plan-vertical-slices" \
  "$HOME/.agents/skills/plan-vertical-slices"
```

If that destination already exists, rename or remove the existing copy before
creating the symlink.

Restart Codex if the skill does not appear immediately.

## Update installed skills

Pull the latest repository changes:

```bash
git -C "$HOME/agent-skills" pull --ff-only
```

Because the installed skill is symlinked, no additional copying is required.

## Repository structure

Each skill is stored under `skills/<skill-name>/` and contains a required
`SKILL.md`. A skill may also include UI metadata, scripts, references, or assets.
