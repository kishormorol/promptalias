---
name: t
description: Write tests for code that already works. Use when the user asks for tests — "write tests for X", "add test coverage", "test this", "cover X with tests", "what isn't covered", "unit tests for X", "does this have tests". Use it for any request to test existing behaviour rather than change it.
---

# Write tests

Write tests for: $ARGUMENTS. Default to whatever the last change touched.

## How to work

1. Read the code before testing it, and read the existing tests to learn the project's
   framework, layout, naming, and assertion style. Match them.
2. Test the behaviour, not the implementation. A test that asserts on internal calls
   breaks on every refactor and catches nothing.
3. Cover, in this order: the ordinary path, the boundaries (empty, one, many, maximum),
   and each error the code claims to handle.
4. Run the suite. A new test that has never failed has not been checked — make it fail
   once, by breaking the code or the expectation, then restore it.

## Rules

- Do not change the code under test. If a test cannot be written without changing it,
  say so and say why — that is a design finding worth reporting, not a licence to edit.
- One behaviour per test, named for the behaviour it pins down.
- No sleeps, no dependence on wall-clock time, no network. Fixtures over live services.
- If the code is already covered, say so plainly instead of writing a duplicate.

## Report back

State what you covered, what you deliberately left uncovered and why, and the suite
result. If a new test found a real bug, report the bug rather than adjusting the test
until it passes.
