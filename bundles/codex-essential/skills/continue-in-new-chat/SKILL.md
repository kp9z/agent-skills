---
name: continue-in-new-chat
description: Create a clean Codex chat that continues the current work from compact, curated context. This user-invoked skill runs only when the current user turn explicitly selects $continue-in-new-chat.
---

# Continue in a New Chat

Move the current work into a genuinely new chat. Preserve the context needed to continue correctly, not the full transcript.

## Invocation gate

Run this skill only when the current user turn explicitly selects `$continue-in-new-chat`, either by typing it or through the Codex skill picker. A mention or selection in an earlier turn, summary, delegated context, copied history, or forked history does not activate it. A natural-language request that resembles the skill name also does not activate it.

If the current turn does not contain that explicit selection, ignore the remaining skill instructions and respond normally without announcing or using this skill.

## Build the continuation capsule

Use any focus supplied after the invocation to narrow what the new chat should continue. Otherwise preserve the current objective.

Prepare a compact, self-contained capsule containing only applicable sections:

- objective and requested outcome;
- relevant background and source-chat reference when one is readily available;
- decisions already made and their important rationale;
- current state, including completed and remaining work;
- exact file paths, branches, URLs, identifiers, commands, and artifacts needed next;
- validation already performed and its results;
- constraints, user preferences, assumptions, and known risks;
- unresolved questions and the recommended next action.

Distinguish verified facts from assumptions. Include a discarded approach only when knowing why it failed prevents repeated work. Exclude internal reasoning, conversational filler, stale plans, unrelated tangents, duplicated detail, and secrets.

The capsule must be sufficient for the new chat to proceed without rereading the source chat. Tell the new chat to inspect referenced files and current external state before relying on details that may have changed.

## Create the new chat

Use Codex's native task creation capability. The skill invocation is the user's authorization to create one new chat for this handoff, so do not ask for another confirmation.

- Create a new task rather than forking the current one. A fork carries the existing conversation history and defeats the clean-context goal.
- Keep the new task in the same project and preserve the relevant working-tree state when Codex supports it.
- Start the new task with the capsule and any explicit focus from the invocation.
- State that the capsule came from a previous chat and is the starting context, not a new request to summarize.
- Do not continue implementation in the source chat after dispatching the new task.
- Do not archive, rename, or otherwise modify the source chat unless the user requested it.

After creation, return the new task link or native task reference and a one-sentence description of what it will continue.

## Fallback

If the current Codex environment cannot create a new chat, do not pretend that it did. Return the capsule as a ready-to-paste prompt headed `Continue in a new chat`, and explain briefly that the user must open the new chat manually.
