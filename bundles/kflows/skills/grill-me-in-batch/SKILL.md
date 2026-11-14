---
name: grill-me-in-batch
description: A batch interview to sharpen multiple features, plans, or ideas in one chat.
disable-model-invocation: true
---

Read the included [grilling workflow](../grilling/SKILL.md) and apply its interview rules with the following batch behavior. These instructions replace its single design tree and session completion criteria.

## Establish the batch

Use the features already supplied in the conversation as the initial batch. If none are supplied, ask which features the user wants to sharpen together. Give each feature a stable identifier and short name. Keep a separate design tree for each feature, plus shared decisions that affect several features.

Maintain a compact ledger in the conversation: each feature's status (open, blocked, ready for confirmation, confirmed, or explicitly deferred), settled decisions, and remaining questions. Keep shared decisions in one place and identify the features they affect. Add new features when the user introduces them without losing earlier decisions.

## Interview across the batch

Compute one frontier across all feature trees and shared decisions. In each round, ask every currently answerable question across the batch, grouping questions by shared decisions or feature. Use the grilling workflow's question format and recommendations, with unique question numbers across the entire chat so partial replies remain unambiguous.

A feature waiting on an answer, investigation, or another feature's decision must not stall independent questions for the rest of the batch. Ask shared decisions once; questions depending on their answers belong to a later round. Follow consequential dependencies deeply while continuing to cover the other features' available questions.

After each reply, record the answers actually given and carry unanswered questions forward. Resolve ambiguous answers before treating them as decisions. When an answer changes an earlier decision, reopen affected branches in every dependent feature. Briefly show ledger changes alongside the next round so the user can see progress across the batch.

## Confirm the batch

A feature is ready for confirmation when its frontier is empty, its dependencies are resolved, and no unresolved assumption remains hidden. Present its agreed behavior and important tradeoffs for confirmation; other features may continue through their rounds. Confirmation of one feature applies only to that feature and its stated decisions.

Finish when every feature is confirmed or explicitly deferred by the user. Give a consolidated handoff with each feature's decisions, shared constraints, dependencies, and any deferred questions. Request confirmation of any remaining ready features together. Keep this an interview: implementation and publishing specs or issues require a subsequent user instruction.
