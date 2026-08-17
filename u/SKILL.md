---
name: u
description: Update an existing feature while keeping its tests green. Use when the user asks to change, extend, modify, or adjust behaviour that already exists and already has tests — phrasings like "update the X", "make X also do Y", "change how X works".
---

# Update a feature

Update this feature: $ARGUMENTS.

Keep existing tests passing.

## How to work

1. Find the feature and read it before changing anything. Read its tests too — they
   are the specification you must not break.
2. Make the smallest change that delivers the request. Match the surrounding code's
   naming, comment density, and idiom.
3. Run the existing tests. If any fail, fix the code — do not edit a test to make it
   pass unless the request itself changed the expected behaviour, and say so explicitly
   if you do.
4. If the change needs new behaviour that isn't covered, add a test for it alongside.

## Report back

State what changed, which tests you ran, and their result. If tests failed and you
could not fix them, say so with the output rather than reporting success.
