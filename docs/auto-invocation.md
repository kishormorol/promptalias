# Does the agent invoke these prompts on its own?

**Measured by `scripts/measure_invocation.py` on 17 August 2026.**
Not run in CI: every row is a real billed session, and the model is not
deterministic. Re-run it by hand when the descriptions change.

Every other check here measures `hooks/resolve.py`, because a regex's decision can
be read from outside. This measures what none of them can: whether Claude Code's
own matching picks the prompt out of an ordinary sentence. **Hooks are disabled**
for these runs, so the hook cannot hand over the answer it is being compared to.

9 of 9 cases behaved as expected, at up to 3 turns each.

| Sentence | Expected | What happened | Other tools it used |
| --- | --- | --- | --- |
| make the parser also handle tabs | `/u` | invoked /u ✅ | Bash, Read |
| I need something that watches the log | `/n` | invoked /n ✅ | Bash, Read |
| cover the validator with tests | `/t` | invoked /t ✅ | Bash, Read |
| why is the resolver broken | `/d` | invoked /d ✅ | Bash |
| does this look right to you | `/rv` | invoked /rv ✅ | Bash |
| walk me through resolve.py | `/ex` | invoked /ex ✅ | Bash, Read |
| what would it take to support Windows | `/p` | invoked /p ✅ | Bash, Read |
| what is the weather today | *nothing* | stayed silent ✅ | — |
| rename the variable on line 40 of validate.py | *nothing* | stayed silent ✅ | Bash, Read |

## What this still does not settle

- **One run each.** The same sentence can go differently on another day; nothing
  here is a rate. The one sentence measured repeatedly — *why is the resolver
  broken*, seven runs across 17-18 August — invoked `/d` six times and nothing
  once. Read every row above as that kind of coin, not as a settled answer.
- **Non-interactive sessions.** `claude -p` is not the same context as typing into
  a live session, where the surrounding conversation is doing work too.
- **Written by the same hand as the descriptions.** Sentences someone else writes,
  about their own code, are the real test.
- **Capped at 3 turns.** A prompt invoked later in a long session is invisible
  here.

So: evidence that the wording carries, not proof that it always will. The
phrasings in [`phrasings.md`](phrasings.md) remain recorded as unambiguous rather
than as proven.
