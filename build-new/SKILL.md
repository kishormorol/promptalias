---
name: build-new
description: Build something new that does not exist yet, with tests. Use when the user asks for code that is not there yet — "write a X", "build me a X", "create a script that Y", "I need something that Y", "implement X from scratch", "start a new X", "we need a X". Use it for any request to write something new, rather than to change something that already works.
model: claude-opus-5-5
---

# Build something new

Build this: $ARGUMENTS. If that is empty, build what the user's last message asks for.

## How to work

1. Look for what already exists first. If a version of this is already here, this is an
   update — read it and its tests, and work from them instead of writing a second one.
   The same holds for existing code your new code is wired into: its tests stay green
   and are not edited to pass, as `/update-feature` requires.
   If the user asked outright for a replacement or a separate version, say what exists,
   build the new one beside it, and leave removing the old one to them.
2. Read neighbouring code and tests before writing yours. New code that ignores the
   surrounding naming, structure, and idiom is a cost paid on every later read. In an
   empty project, pick the plainest layout and test setup for the language and say so.
3. Build the smallest thing that satisfies the request end to end, and nothing beyond
   it. Do not add configuration, abstraction layers, or options nobody asked for.
4. Write tests alongside the code — the ordinary path, the boundaries, and the failure
   the code is meant to handle. If the project has a test convention, follow that one.
   For something that cannot be unit-tested (a config file, a document, a one-off
   query), say so and show how you checked it instead.
5. Run the tests. Run the thing itself only where that is safe and it exits on its own:
   against a fixture, a temporary directory or a dry-run flag. If it deletes, sends, deploys, migrates or
   writes outside the project, do not run it for real — give the user the command.

## Rules

- Use what the project already depends on. A new dependency for something small needs a
  reason stated out loud.
- Handle the errors you can actually foresee. Do not wrap everything in a catch-all that
  swallows the failure.
- If part of the request is ambiguous and the readings differ only in detail, build the
  one a careful colleague would pick, state the assumption, and keep going. If they
  differ in what gets deleted, sent, exposed or charged, ask before building that part.

## Report back

State what you built, where it lives, how to run it, and the exact test command with its
summary line (passed, failed, skipped). If you could not run the tests, say so and why;
do not call them passing. Name any dependency you added and anything you deliberately
left out.
