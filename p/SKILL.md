---
name: p
description: Plan an approach before any code is written. Use when the user asks how to approach something — "how should I X", "plan X", "what's the best way to Y", "design X", "think through X before coding", "give me an approach for X", "what would it take to X". Use it for any request that asks for a route rather than the work itself.
---

# Plan an approach

Plan: $ARGUMENTS.

## How to work

1. Read the code this would touch before proposing anything. A plan written against
   what you assume is there is worth nothing.
2. State the goal in one sentence, and what would make it done.
3. Give the steps in dependency order — each one small enough to finish and check on
   its own, naming the files it touches.
4. Name the real decision points, with a recommendation and the tradeoff in a line
   each. Two options with a pick, not four with a survey.
5. Say what could go wrong: the parts most likely to break, what is already covered by
   tests, and what would need new ones.

## Rules

- Write no implementation code. Signatures, file layout, and short sketches are fine;
  a finished function is not.
- Prefer the approach that fits what the project already does over the one that is
  theoretically cleaner.
- Say plainly if the request does not need a plan — some work is one obvious edit, and
  saying so is more useful than a five-step ceremony around it.
- Flag anything you could not resolve from the code and would need answered.

## Report back

The plan is the deliverable. Keep it to what fits on one screen, and end with the first
step to take.
