#!/usr/bin/env python3
"""Does the agent invoke these prompts on its own, without being told to?

Everything else here measures the hook, because the hook's decision is visible
from outside. This measures the thing that is not: whether Claude Code's own
implicit matching picks a prompt out of an ordinary sentence.

Method — one non-interactive session per sentence, in a throwaway copy of this
repo, with **hooks disabled** so the hook cannot supply the answer it is being
compared against. The session is capped at a few turns and the first Skill call
it makes is recorded.

This costs real money and real time, and the model is not deterministic, so it
is never run in CI. Run it by hand, and treat a pass as evidence rather than
proof.

    ./scripts/measure_invocation.py                       # run every case, once each
    ./scripts/measure_invocation.py --record              # rewrite docs/auto-invocation.md
    ./scripts/measure_invocation.py --only resolver -n 7  # one sentence seven times, as a rate
    ./scripts/measure_invocation.py --only resolver -n 7 --record   # keep that rate
    ./scripts/measure_invocation.py --check               # no sessions: do the docs still
                                                          # match scripts/repeat_runs.json?

A single run says what happened once. When a sentence starts behaving unevenly,
--only narrows to it and --repeat runs it enough times to tell an outlier from a
change. A full pass records the table; a repeated run records a rate in
scripts/repeat_runs.json, and every sentence that cites a rate — in the doc and
on the published page — is generated or checked from that file, so no number
here is a hand-typed one that can quietly go stale.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "scripts" / "invocation_cases.json"
REPEATS = REPO / "scripts" / "repeat_runs.json"
DOC = REPO / "docs" / "auto-invocation.md"
PAGE = REPO / "docs" / "index.html"
TURNS = 3

# Counts read as prose in both files, so a claim is written and checked in words.
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}

# "`/d` six times out of seven" — the shape of a rate wherever one is claimed.
RATE_RE = re.compile(r"[`>]/(\w+)[`<][^.]{0,40}?(\w+) times out of (\w+)")


def first_skill(stream):
    """The first Skill the session invoked, plus the other tools it reached for."""
    skill, tools = None, []
    for line in stream.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if block.get("name") == "Skill":
                got = block.get("input")
                if skill is None:
                    skill = got.get("skill") if isinstance(got, dict) else "?"
            elif block.get("name"):
                tools.append(block["name"])
    return skill, list(dict.fromkeys(tools))


def run_case(prompt, workdir, settings):
    result = subprocess.run(
        ["claude", "-p", prompt, "--settings", str(settings), "--max-turns", str(TURNS),
         "--output-format", "stream-json", "--verbose"],
        cwd=workdir, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return first_skill(result.stdout)


def verdict(expect, skill):
    if expect is None:
        return ("ok", "stayed silent") if skill is None else ("wrong", f"invoked /{skill}")
    if skill == expect:
        return "ok", f"invoked /{skill}"
    if skill is None:
        return "missed", "invoked nothing"
    return "wrong", f"invoked /{skill}"


def word(n):
    """Small counts as words, because the prose around them is prose."""
    return WORDS.get(n, str(n))


def load_repeats(path=REPEATS):
    """Sentences that have been run more than once, with how they landed."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))["runs"]
    except (OSError, ValueError, KeyError):
        return []


def times(n):
    return "once" if n == 1 else "twice" if n == 2 else f"{word(n)} times"


def rate_sentence(entry):
    """One repeated sentence, as the prose that cites it."""
    want = f"`/{entry['expect']}`" if entry["expect"] else "silence"
    held = entry["outcomes"].get(f"/{entry['expect']}" if entry["expect"] else "nothing", 0)
    others = [f"{'nothing' if k == 'nothing' else '`' + k + '`'} {times(v)}"
              for k, v in entry["outcomes"].items()
              if k != (f"/{entry['expect']}" if entry["expect"] else "nothing")]
    tail = f", and {' and '.join(others)}" if others else ""
    return (f"*{entry['prompt']}* reached for {want} {word(held)} times out of "
            f"{word(entry['runs'])}{tail}")


def repeat_bullet(repeats):
    """The 'one run each' caveat, written from the rates rather than from memory."""
    body = ("**One run each.** The same sentence can go differently on another day; "
            "nothing here is a rate. ")
    if repeats:
        cited = ". ".join(rate_sentence(e) for e in repeats)
        dates = ", ".join(dict.fromkeys(e["measured"] for e in repeats))
        many = len(repeats) > 1
        body += (f"The {word(len(repeats))} sentence{'s' if many else ''} since run "
                 f"repeatedly say{'' if many else 's'} what that "
                 f"costs: {cited} ({dates}). Read every row above as that kind of coin, "
                 "not as a settled answer.")
    else:
        body += ("No sentence here has been run twice, so every row is a single coin "
                 "toss reported as an outcome.")
    return textwrap.fill(body, width=79, initial_indent="- ", subsequent_indent="  ")


RATES_COMMENT = (
    "Rates, for sentences run more than once. The table in docs/auto-invocation.md is one "
    "session per row, which says what happened once and not how often. When a sentence "
    "starts behaving unevenly, ./scripts/measure_invocation.py --only TEXT -n N --record "
    "adds it here. Written by that script; the prose that cites it is generated from these "
    "numbers.")


def record_repeats(results, path=REPEATS):
    """Keep a repeated run as a rate. Replaces any earlier rate for that sentence."""
    data = {"comment": RATES_COMMENT, "runs": []}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            pass
    for prompt, expect, _mark, _detail, _tools, outcomes, runs in results:
        entry = {"prompt": prompt, "expect": expect, "runs": runs,
                 "outcomes": outcomes, "measured": f"{date.today():%d %B %Y}"}
        data["runs"] = [e for e in data["runs"] if e["prompt"] != prompt] + [entry]
    data["runs"].sort(key=lambda e: e["prompt"])
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def record(results, path=DOC, repeats=None, when=None):
    ok = sum(1 for r in results if r[2] == "ok")
    repeats = load_repeats() if repeats is None else repeats
    when = when or date.today()
    lines = [
        "# Does the agent invoke these prompts on its own?",
        "",
        f"**Measured by `scripts/measure_invocation.py` on {when:%d %B %Y}.**",
        "Not run in CI: every row is a real billed session, and the model is not",
        "deterministic. Re-run it by hand when the descriptions change.",
        "",
        "Every other check here measures `hooks/resolve.py`, because a regex's decision can",
        "be read from outside. This measures what none of them can: whether Claude Code's",
        "own matching picks the prompt out of an ordinary sentence. **Hooks are disabled**",
        f"for these runs, so the hook cannot hand over the answer it is being compared to.",
        "",
        textwrap.fill(
            f"**Every row below is one session.** {ok} of {len(results)} behaved as "
            f"expected, at up to {TURNS} turns each — but a session is a coin, not a rate. "
            f"Read the table as {word(len(results))} coins that came up heads, and the "
            f"{'rate' if len(repeats) == 1 else 'rates'} under it as what one row is "
            "actually worth." if repeats else
            f"**Every row below is one session.** {ok} of {len(results)} behaved as "
            f"expected, at up to {TURNS} turns each — one coin each, and no sentence here "
            "has been tossed twice.", width=79),
        "",
        "| Sentence | Expected | What happened | Other tools it used |",
        "| --- | --- | --- | --- |",
    ]
    for prompt, expect, mark, detail, tools, *_ in results:
        want = f"`/{expect}`" if expect else "*nothing*"
        symbol = "✅" if mark == "ok" else "⚠️"
        lines.append(f"| {prompt} | {want} | {detail} {symbol} | {', '.join(tools) or '—'} |")
    lines += [
        "",
        "## What this still does not settle",
        "",
        repeat_bullet(repeats),
        "- **Non-interactive sessions.** `claude -p` is not the same context as typing into",
        "  a live session, where the surrounding conversation is doing work too.",
        "- **Written by the same hand as the descriptions.** Sentences someone else writes,",
        "  about their own code, are the real test.",
        f"- **Capped at {TURNS} turns.** A prompt invoked later in a long session is invisible",
        "  here.",
        "",
        "So: evidence that the wording carries, not proof that it always will. The",
        "phrasings in [`phrasings.md`](phrasings.md) remain recorded as unambiguous rather",
        "than as proven.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def claims(text):
    """Every rate a document states, as (trigger, held, runs) in words."""
    return RATE_RE.findall(text)


def check_docs(repeats=None, report=None):
    """Do the doc and the page still say what scripts/repeat_runs.json measured?

    Cheap enough for CI: it opens files, never a session.
    """
    repeats, report = (load_repeats() if repeats is None else repeats), report or []
    measured = {(e["expect"], e["outcomes"].get(f"/{e['expect']}", 0), e["runs"])
                for e in repeats}
    in_words = {(t, word(h), word(r)) for t, h, r in measured}

    for path in (DOC, PAGE):
        if not path.is_file():
            report.append(f"{path.name} is missing")
            continue
        for claim in claims(path.read_text(encoding="utf-8")):
            if claim not in in_words:
                trigger, held, runs = claim
                report.append(f"{path.name} says /{trigger} {held} times out of {runs}, "
                              "which no run in repeat_runs.json measured")

    if repeats and DOC.is_file():
        bullet = repeat_bullet(repeats)
        if bullet not in DOC.read_text(encoding="utf-8"):
            report.append(f"{DOC.name}'s caveat no longer matches repeat_runs.json — "
                          "run ./scripts/measure_invocation.py --record")
    return report


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Does the agent invoke these prompts on its own, without being told to?")
    parser.add_argument("--record", action="store_true",
                        help="rewrite docs/auto-invocation.md from this run")
    parser.add_argument("--repeat", "-n", type=int, default=1, metavar="N",
                        help="run each case N times and report how often it held")
    parser.add_argument("--only", metavar="TEXT",
                        help="only the cases whose sentence contains TEXT")
    parser.add_argument("--check", action="store_true",
                        help="run nothing: check the docs against scripts/repeat_runs.json")
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat needs a positive number of runs")
    if args.check and (args.record or args.only or args.repeat != 1):
        parser.error("--check reads files and runs nothing, so it stands alone")
    if args.record and args.repeat == 1 and args.only:
        parser.error("--record writes the whole table from one run each, so with --only "
                     "it needs --repeat to record a rate instead")
    return args


def select(cases, only):
    if not only:
        return cases
    needle = only.lower()
    return [case for case in cases if needle in case["prompt"].lower()]


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.check:
        report = check_docs()
        for problem in report:
            print(f"stale  {problem}")
        if report:
            return 1
        rates = len(load_repeats())
        print(f"ok  the doc and the page match the {rates} recorded rate(s)")
        return 0

    if not shutil.which("claude"):
        print("the claude CLI is not on PATH, so nothing can be measured")
        return 1

    cases = select(json.loads(CASES.read_text())["cases"], args.only)
    if not cases:
        print(f"no case's sentence contains {args.only!r}")
        return 1
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp) / "fixture"
        shutil.copytree(REPO, workdir, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        settings = Path(tmp) / "nohooks.json"
        settings.write_text(json.dumps({"disableAllHooks": True}))

        for case in cases:
            prompt, expect = case["prompt"], case["expect"]
            want = f"/{expect}" if expect else "silence"
            attempts = []
            for i in range(args.repeat):
                skill, tools = run_case(prompt, workdir, settings)
                mark, detail = verdict(expect, skill)
                attempts.append((mark, detail, tools))
                run = f"run {i + 1}: " if args.repeat > 1 else ""
                print(f"{run}{mark:<7} {want:<8} {prompt!r} — {detail}", flush=True)
            held = sum(1 for mark, _, _ in attempts if mark == "ok")
            outcomes = {}
            for _mark, detail, _tools in attempts:
                landed = detail.replace("invoked ", "").replace("stayed silent", "nothing")
                outcomes[landed] = outcomes.get(landed, 0) + 1
            if args.repeat > 1:
                print(f"         {want} on {prompt!r}: {held} of {args.repeat}")
            results.append((prompt, expect, *attempts[0], outcomes, args.repeat))

    if args.record and args.repeat > 1:
        record_repeats(results)
        print(f"\nwrote {REPEATS.relative_to(REPO)} — regenerate the doc's caveat with "
              "./scripts/measure_invocation.py --record")
    elif args.record:
        record(results)
        print(f"\nwrote {DOC.relative_to(REPO)}")

    held = sum(sum(v for k, v in r[5].items()
                   if k == (f"/{r[1]}" if r[1] else "nothing")) for r in results)
    runs = sum(r[6] for r in results)
    if held < runs:
        print(f"\n{runs - held} of {runs} runs did not behave as expected")
        return 1
    print(f"\nok  {runs} of {runs} runs behaved as expected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
