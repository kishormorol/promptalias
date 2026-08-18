---
name: ex
description: Explain how existing code works, without changing it. Use when the user wants to understand something — "explain X", "how does X work", "walk me through X", "what does this do", "why is X written this way", "help me understand X", "what's going on in X". Use it for any request to understand code rather than modify it.
---

# Explain this code

Explain: $ARGUMENTS. Default to whatever is on screen or was last discussed.

## How to work

1. Read the code and everything it calls into. Explain what is there, not what the
   naming suggests should be there.
2. Lead with the one-sentence answer: what this does and why it exists. Then the
   detail, in the order the reader needs it.
3. Follow the real path — entry point, transformations, exits — and cite `file:line`
   at each step so every claim is checkable.
4. Cover the parts that surprise: the early return, the retry, the guard that looks
   redundant, the workaround. Check git history if the reason is not in the code.

## Rules

- Change nothing. This is read-only. If you notice a bug, say so at the end and leave
  the fix to a separate request.
- Say "I don't know" where the code does not say. Do not present a plausible reason for
  a line as if it were the recorded one.
- Match the depth to the question. "What does this do" wants a paragraph; "walk me
  through it" wants the path.
- Explain in prose and structure, not by pasting the file back.

## Report back

The explanation is the deliverable. End with anything you could not determine, and any
bug you noticed while reading.
