---
name: i-dont-understand
description: Re-explain the preceding material in simpler language. This user-invoked skill runs only when the current user turn explicitly selects $i-dont-understand.
---

# I Don't Understand

Explain the same underlying idea again in a form that is easier to grasp. Do not merely shorten or repeat the previous wording.

## Invocation gate

Run this skill only when the current user turn explicitly selects `$i-dont-understand`, either by typing it or through the Codex skill picker. A mention or selection in an earlier turn, summary, delegated context, copied history, or forked history does not activate it. Requests such as "explain this" or "make this simpler" do not activate it by themselves.

If the current turn does not contain that explicit selection, ignore the remaining skill instructions and respond normally without announcing or using this skill.

## Re-explain

1. Infer what the user did not understand from the immediately preceding exchange. Ask what they mean only when multiple subjects are genuinely plausible.
2. Start with the central point in one plain sentence.
3. Rebuild the explanation from familiar ideas toward the difficult part. Use a concrete example, analogy, or small worked scenario when it helps.
4. Define necessary terms where they first appear. Replace avoidable jargon with everyday language.
5. Preserve important qualifications and accuracy. Simpler must not mean misleading.
6. Keep the first pass compact. Offer deeper detail only after establishing the basic mental model.

For code, show the smallest relevant snippet and trace it with concrete values. For mathematics, explain what each symbol represents and work through one small example. For a process, state what happens first, what changes, and what result to expect.

Use a patient, direct tone. Do not imply that the topic is easy or that the user should already understand it. Avoid long preambles, multiple competing analogies, and ending with a quiz. A single focused check such as "Which part is still unclear?" is appropriate when another turn would help.

Do not take actions, edit files, or change the user's plan merely because they asked for an explanation.
