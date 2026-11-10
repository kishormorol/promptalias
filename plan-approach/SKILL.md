---
name: plan-approach
description: Plan an approach before any code is written. Use when the user asks how to approach something — "how should I X", "plan X", "write a plan for X", "what's the best way to Y", "design X", "think through X before coding", "give me an approach for X", "what would it take to X". Use it for any request that asks for a route rather than the work itself.
model: claude-fable-5-2
---

# Plan an approach

Plan: $ARGUMENTS. If that is empty, plan what the user's last message asks for.

## How to work

1. Read the code this would touch before proposing anything. A plan written against
   what you assume is there is worth nothing. If nothing exists yet, say so and plan
   the layout. If the question is not about this codebase, answer it directly.
2. State the goal in one sentence, and what would make it done.
3. Give the steps in dependency order — each one small enough to finish and check on
   its own, naming the files it touches.
4. Name the real decision points, with a recommendation and the tradeoff in a line
   each. Compare only the alternatives that are viable: usually two, sometimes one.
5. Say what could go wrong: the parts most likely to break, what is already covered by
   tests, and what would need new ones.

## Rules

- Change no files: the plan goes in your reply, unless the user asked for it as a
  document, and then that document is the only file you write. No implementation code.
  Signatures, file layout, and short sketches are fine; a finished function is not.
- If the user also asked for the work itself ("design and build X"), give the plan
  first and ask whether to go ahead. Once they say yes, the rule above no longer
  holds: do the work the way `/build-new` or `/update-feature` would.
- Prefer the approach that fits what the project already does over the one that is
  theoretically cleaner.
- Say plainly if the request does not need a plan — some work is one obvious edit, and
  saying so is more useful than a five-step ceremony around it.
- Flag anything you could not resolve from the code and would need answered.

## Report back

The plan is the deliverable. Aim for one screen. If the steps do not fit, go longer;
never fit the screen by dropping a step, a decision or a risk. End with the first step
to take.
