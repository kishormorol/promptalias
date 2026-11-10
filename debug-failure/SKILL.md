---
name: debug-failure
description: Track a failure to its root cause and fix it. Use when something is broken — "this is failing", "why is X broken", "fix this error", "debug X", "X throws Y", "the tests are failing", "it stopped working", "I'm getting an error", "this crashes". Use it for any report of behaviour that is wrong, rather than a request for behaviour that is new.
model: claude-opus-5-5
---

# Debug a failure

Debug this: $ARGUMENTS. If that is empty, work from the user's last message.

## How to work

1. Reproduce it first. Run the failing command or test and read the actual output. A
   fix for a failure you have not seen is a guess. If the command destroys or changes
   anything beyond its own output (it deletes, deploys, migrates, sends or charges), do
   not run it again: reproduce from the logs, a dry run or a copy, or ask.
2. Read the whole error — stack frame, message, and the line it names — or, where
   there is no error, the exact wrong output. Then read the code that produced it.
3. Form one hypothesis that explains *all* of the evidence, including anything that
   looks irrelevant. Check it before writing a fix: add a log line, run a narrower test,
   inspect the state. If the user asked only why it is broken, stop here: remove any
   logging you added, report the cause and the fix you would make, and apply it when
   they ask.
4. Unless an existing test already fails on this bug, write a test that reproduces
   the failure and watch it fail. If no test can express it (a build, a config, an
   environment), or the project has no test setup, say so and keep the failing output.
5. Fix the cause, not the symptom. Silencing the error, widening a catch, or
   hard-coding the reported input is not a fix. Handling a boundary the code should
   always have handled is. Never get to green by weakening, skipping or deleting a
   failing test; if the test itself is wrong, show why and change only the part of it that is
   wrong (setup, call or assertion).
6. Run the new test, then the whole suite, and remove any logging you added. Where no
   test expresses the failure, run the command from step 1 again and show its output
   now; if that command must not be run again, say the fix is unverified against the
   original failure and give the user the command.

## Rules

- Change one thing at a time. Two simultaneous edits mean you do not know which worked.
- If `git diff` or recent commits touch the failing path, look there first — a failure
  that started recently usually started with a change.
- If two hypotheses both fit, say which you tested and what ruled the other out.
- If you cannot reproduce it, do not change code. Report what you tried, the most
  likely cause, and the fix you would propose. If the user then asks for that fix
  anyway, apply it and label it unverified.

## Report back

State the root cause in one sentence, the fix, the regression test, and the evidence:
the failing output before, and after it the test command with its summary line, or
the re-run command and its output. Name any
test you changed and why. A fix applied without reproducing the failure is unverified,
and the report says so.
