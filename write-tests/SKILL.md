---
name: write-tests
description: Write tests for code that already works. Use when the user asks for tests — "write tests for X", "write a test for X", "add tests to X", "add test coverage", "test this", "cover X with tests", "what isn't covered", "unit tests for X", "does this have tests". Use it for any request to test existing behaviour rather than change it.
model: claude-sonnet-5-5
---

# Write tests

Write tests for: $ARGUMENTS. With nothing named, default to the uncommitted diff; if the
tree is clean, the last commit; if neither exists or this is not a git repository, ask
which code to test.

If the user asked a question about coverage ("does this have tests", "what isn't
covered"), answer it: list what is covered and what is not, with `file:line`. Write
nothing, and offer to write the missing tests. If they asked for the tests to be run
rather than written, run them and report the result.

## How to work

1. Read the code before testing it, and read the existing tests to learn the project's
   framework, layout, naming, and assertion style. Match them. If there are no tests
   yet, use the runner the language ships or the one the project's tooling already
   implies, and say which. A new test dependency needs a reason stated out loud.
2. Test the behaviour, not the implementation. A test that asserts on internal calls
   breaks on every refactor and catches nothing.
3. Cover, in this order: the ordinary path, the boundaries (empty, one, many, maximum),
   and each error the code claims to handle.
4. Run the suite. A new test that has never failed has not been checked. Make each one
   fail once for the right reason: break the behaviour it pins with a small edit to
   the code, watch it fail, then undo that edit by hand and check the file is back
   exactly as it was. Never undo it with `git checkout`, `git restore` or `git stash`:
   those throw away the user's uncommitted work. Run the suite again at the end.

## Rules

- Leave the code under test as you found it. The temporary edit in step 4 is the only
  exception, and it must be gone before you report. If a test cannot be written without
  changing the code, say so and say why — that is a design finding worth reporting,
  not a licence to edit.
- One behaviour per test, named for the behaviour it pins down.
- Unit tests: no sleeps, no dependence on wall-clock time, no live services. Fixtures
  instead. When the user asks for an integration test, use a local or disposable
  service and bounded waits.
- If the code is already covered, say so plainly instead of writing a duplicate.
- If a new test exposes a real bug, keep the test and do not fix the code here. Mark it
  as an expected failure the way the project does, with a comment naming the bug, so
  the suite stays usable and the evidence stays in.

## Report back

State what you covered, what you deliberately left uncovered and why, and the exact test
command with its summary line (passed, failed, skipped). Confirm each new test was seen
failing. If a test found a real bug, report the bug with its failing output rather than
adjusting the test until it passes. If you could not run the suite, say so and why.
