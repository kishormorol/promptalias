---
name: rv
description: Review the most recent diff for correctness, security, and performance. Use when the user asks for a review of what just changed — "review this", "review the last diff", "check my changes", "look over what you just wrote", "anything wrong with this?".
---

# Review the last diff

Review the last diff for correctness, security, and performance.

## Scope

Default to the uncommitted working tree (`git diff`), plus staged changes
(`git diff --staged`). If the working tree is clean, review the last commit
(`git show HEAD`). If $ARGUMENTS names a different range, branch, or path, review that
instead.

## What to look for

**Correctness** — off-by-one and boundary errors, unhandled nil/null/undefined, error
paths that swallow failures, race conditions, changed behaviour the existing tests do
not cover.

**Security** — untrusted input reaching a query, path, shell, or deserializer;
secrets or tokens in source or logs; authz checks that were moved or dropped; new
dependencies pulled in for something trivial.

**Performance** — work inside a loop that belongs outside it, N+1 queries, an
accidental O(n²), unbounded reads of data that could be large.

## Rules

- Review only what the diff touches. Pre-existing problems in surrounding code are out
  of scope unless the diff makes them reachable.
- For each finding, give the concrete failure: specific input or state → wrong output or
  crash. A finding you cannot make concrete is a guess — label it as one or drop it.
- Cite `file:line` so each finding is clickable.
- Order findings most severe first. If the diff is clean, say so plainly instead of
  manufacturing nits.
