# Does the agent invoke these prompts on its own?

**Measured by `scripts/measure_invocation.py` on 17 August 2026.**
The prompts then had one- and two-letter names (`/u`, `/n`, `/t`, `/d`, `/rv`, `/ex`, `/p`). They were
renamed on 10 November 2026 and the rows below show the new names. The descriptions of
`/update-feature`, `/write-tests` and `/plan-approach` were also revised that day, and nothing here
has been measured again since.
Not run in CI: every row is a real billed session, and the model is not
deterministic. Re-run it by hand when the descriptions change.

Every other check here measures `hooks/resolve.py`, because a regex's decision can
be read from outside. This measures what none of them can: whether Claude Code's
own matching picks the prompt out of an ordinary sentence. **Hooks are disabled**
for these runs, so the hook cannot hand over the answer it is being compared to.

**Every row below is one session.** 9 of 9 behaved as expected, at up to 3
turns each — but a session is a coin, not a rate. Read the table as nine coins
that came up heads, and the rate under it as what one row is actually worth.

| Sentence | Expected | What happened | Other tools it used |
| --- | --- | --- | --- |
| make the parser also handle tabs | `/update-feature` | invoked /update-feature ✅ | Bash, Read |
| I need something that watches the log | `/build-new` | invoked /build-new ✅ | Bash, Read |
| cover the validator with tests | `/write-tests` | invoked /write-tests ✅ | Bash, Read |
| why is the resolver broken | `/debug-failure` | invoked /debug-failure ✅ | Bash |
| does this look right to you | `/review-diff` | invoked /review-diff ✅ | Bash |
| walk me through resolve.py | `/explain-code` | invoked /explain-code ✅ | Bash, Read |
| what would it take to support Windows | `/plan-approach` | invoked /plan-approach ✅ | Bash, Read |
| what is the weather today | *nothing* | stayed silent ✅ | — |
| rename the variable on line 40 of validate.py | *nothing* | stayed silent ✅ | Bash, Read |

## What this still does not settle

- **One run each.** The same sentence can go differently on another day;
  nothing here is a rate. The one sentence since run repeatedly says what that
  costs: *why is the resolver broken* reached for `/debug-failure` six times
  out of seven, and nothing once (17-18 August 2026). Read every row above as
  that kind of coin, not as a settled answer.
- **Non-interactive sessions.** `claude -p` is not the same context as typing into
  a live session, where the surrounding conversation is doing work too.
- **Written by the same hand as the descriptions.** Sentences someone else writes,
  about their own code, are the real test.
- **Capped at 3 turns.** A prompt invoked later in a long session is invisible
  here.

So: evidence that the wording carries, not proof that it always will. The
phrasings in [`phrasings.md`](phrasings.md) remain recorded as unambiguous rather
than as proven.
