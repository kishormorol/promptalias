---
name: update-feature
description: Update an existing feature while keeping its tests green. Use when the user asks to change, extend, modify, or adjust behaviour that already exists — phrasings like "update the X", "make X also do Y", "change how X works", "add Y to X", "tweak X", "X should also handle Y", "make X do Y instead", "extend X to cover Y", "adjust X so that Y", "rework X", "X needs to also do Y", "can you make X do Y", "while keeping the tests green". Use it for any request to change what existing code does, rather than to write something new. Not for renames, formatting or docs-only edits.
model: claude-opus-5-5
---

# Update a feature

Update this feature: $ARGUMENTS. If that is empty, work from the user's last message.

Keep the tests for behaviour you are not changing passing. If this turns out to be a
rename, a formatting change or a docs-only edit, just make it: the steps below are for
changes in behaviour.

## How to work

1. Find the feature and read it before changing anything. Read its tests too — they
   are the specification you must not break. If it has no tests, say so, and first pin
   the behaviour you are about to rely on with a test or two (with no test setup at
   all, record a before-and-after run on a fixture or a dry run), so the change is
   checked against something. If it cannot be run safely, say so instead of running it.
2. Run the feature's tests before you change anything, and the whole suite where that
   is quick, and note what already fails. Those are not yours to fix here: report them.
3. Make the smallest change that delivers the request. Match the surrounding code's
   naming, comment density, and idiom.
4. If the change adds behaviour that isn't covered, add a test for it alongside.
5. Run the feature's tests again, then the whole suite, on the final code and tests.
   Fix the failures you caused; for a failure outside the feature's tests, check
   whether it fails without your change before treating it as yours: undo your edit by
   hand or read the diff, never `git checkout`, `git restore` or `git stash`, which
   throw away uncommitted work. If you cannot tell, report it as unattributed. Do not edit a test
   to make it pass unless the request itself changes what that test exercises; then
   change only the setup, calls and assertions the request makes necessary. Never skip
   a test, and delete one only when the request removes the behaviour it asserts.

## Report back

State what changed, the exact test command and its summary line (passed, failed,
skipped), and every test you edited or deleted, with its old and new expectation. List failures
that were there before you started separately. If tests failed and you could not fix
them, or could not be run, say so with the output rather than reporting success.
