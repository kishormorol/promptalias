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

    ./scripts/measure_invocation.py                      # run every case, once each
    ./scripts/measure_invocation.py --record             # also rewrite docs/auto-invocation.md
    ./scripts/measure_invocation.py --only resolver -n 5  # one sentence five times, as a rate

A single run says what happened once. When a sentence starts behaving unevenly,
--only narrows to it and --repeat runs it enough times to tell an outlier from a
change. Only a full pass of one run each may be recorded, because that is the
shape of the table in the doc.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "scripts" / "invocation_cases.json"
DOC = REPO / "docs" / "auto-invocation.md"
TURNS = 3


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


def record(results, path=DOC):
    ok = sum(1 for r in results if r[2] == "ok")
    lines = [
        "# Does the agent invoke these prompts on its own?",
        "",
        f"**Measured by `scripts/measure_invocation.py` on {date.today():%d %B %Y}.**",
        "Not run in CI: every row is a real billed session, and the model is not",
        "deterministic. Re-run it by hand when the descriptions change.",
        "",
        "Every other check here measures `hooks/resolve.py`, because a regex's decision can",
        "be read from outside. This measures what none of them can: whether Claude Code's",
        "own matching picks the prompt out of an ordinary sentence. **Hooks are disabled**",
        f"for these runs, so the hook cannot hand over the answer it is being compared to.",
        "",
        f"{ok} of {len(results)} cases behaved as expected, at up to {TURNS} turns each.",
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
        "- **One run each.** The same sentence can go differently on another day; nothing",
        "  here is a rate. The one sentence measured repeatedly — *why is the resolver",
        "  broken*, seven runs across 17-18 August — invoked `/d` six times and nothing",
        "  once. Read every row above as that kind of coin, not as a settled answer.",
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


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Does the agent invoke these prompts on its own, without being told to?")
    parser.add_argument("--record", action="store_true",
                        help="rewrite docs/auto-invocation.md from this run")
    parser.add_argument("--repeat", "-n", type=int, default=1, metavar="N",
                        help="run each case N times and report how often it held")
    parser.add_argument("--only", metavar="TEXT",
                        help="only the cases whose sentence contains TEXT")
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat needs a positive number of runs")
    if args.record and (args.repeat != 1 or args.only):
        parser.error("--record writes the whole table from one run each, "
                     "so it cannot be combined with --repeat or --only")
    return args


def select(cases, only):
    if not only:
        return cases
    needle = only.lower()
    return [case for case in cases if needle in case["prompt"].lower()]


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

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
            if args.repeat > 1:
                print(f"         {want} on {prompt!r}: {held} of {args.repeat}")
            results.append((prompt, expect, *attempts[0], held, args.repeat))

    if args.record:
        record(results)
        print(f"\nwrote {DOC.relative_to(REPO)}")

    held = sum(r[5] for r in results)
    runs = sum(r[6] for r in results)
    if held < runs:
        print(f"\n{runs - held} of {runs} runs did not behave as expected")
        return 1
    print(f"\nok  {runs} of {runs} runs behaved as expected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
