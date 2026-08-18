---
name: n
description: Build something new that does not exist yet, with tests. Use when the user asks for code that is not there yet — "write a X", "build me a X", "create a script that Y", "I need something that Y", "implement X from scratch", "start a new X", "we need a X". Use it for any request to write something new, rather than to change something that already works.
---

# Build something new

Build this: $ARGUMENTS.

## How to work

1. Look for what already exists first. If a version of this is already here, this is an
   update — read it and its tests, and work from them instead of writing a second one.
2. Read a neighbouring file before writing yours. New code that ignores the surrounding
   naming, structure, and idiom is a cost paid on every later read.
3. Build the smallest thing that satisfies the request end to end, then stop. Do not add
   configuration, abstraction layers, or options nobody asked for.
4. Write tests alongside the code — the ordinary path, the boundaries, and the failure
   the code is meant to handle. If the project has a test convention, follow that one.
5. Run the tests, and run the thing itself if it can be run.

## Rules

- Use what the project already depends on. A new dependency for something small needs a
  reason stated out loud.
- Handle the errors you can actually foresee. Do not wrap everything in a catch-all that
  swallows the failure.
- If part of the request is ambiguous, build the reading a careful colleague would pick,
  state the assumption, and keep going.

## Report back

State what you built, where it lives, how to run it, and the test results. Name anything
you deliberately left out.
