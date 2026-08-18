---
name: d
description: Track a failure to its root cause and fix it. Use when something is broken — "this is failing", "why is X broken", "fix this error", "debug X", "X throws Y", "the tests are failing", "it stopped working", "I'm getting an error", "this crashes". Use it for any report of behaviour that is wrong, rather than a request for behaviour that is new.
---

# Debug a failure

Debug this: $ARGUMENTS.

## How to work

1. Reproduce it first. Run the failing command or test and read the actual output. A
   fix for a failure you have not seen is a guess.
2. Read the whole error — stack frame, message, and the line it names. Then read that
   line and what feeds it.
3. Form one hypothesis that explains *all* of the evidence, including anything that
   looks irrelevant. Check it before writing a fix: add a log line, run a narrower test,
   inspect the state.
4. Fix the cause, not the symptom. Silencing the error, widening a catch, or special
   casing the failing input is not a fix.
5. Add a test that fails before your fix and passes after it, then run the whole suite
   to confirm nothing else moved.

## Rules

- Change one thing at a time. Two simultaneous edits mean you do not know which worked.
- If `git diff` or recent commits touch the failing path, look there first — a failure
  that started recently usually started with a change.
- If two hypotheses both fit, say which you tested and what ruled the other out.
- If you cannot reproduce it, say so and report what you tried instead of fixing blind.

## Report back

State the root cause in one sentence, the fix, the regression test, and the suite
result. If you fixed it without reproducing it, label the fix as unverified.
