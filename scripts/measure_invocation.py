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

    ./scripts/measure_invocation.py            # run every case
    ./scripts/measure_invocation.py --record   # also rewrite docs/auto-invocation.md
"""

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
    for prompt, expect, mark, detail, tools in results:
        want = f"`/{expect}`" if expect else "*nothing*"
        symbol = "✅" if mark == "ok" else "⚠️"
        lines.append(f"| {prompt} | {want} | {detail} {symbol} | {', '.join(tools) or '—'} |")
    lines += [
        "",
        "## What this still does not settle",
        "",
        "- **One run each.** The same sentence can go differently on another day; nothing",
        "  here is a rate.",
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


def main():
    if not shutil.which("claude"):
        print("the claude CLI is not on PATH, so nothing can be measured")
        return 1

    cases = json.loads(CASES.read_text())["cases"]
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp) / "fixture"
        shutil.copytree(REPO, workdir, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        settings = Path(tmp) / "nohooks.json"
        settings.write_text(json.dumps({"disableAllHooks": True}))

        for case in cases:
            prompt, expect = case["prompt"], case["expect"]
            skill, tools = run_case(prompt, workdir, settings)
            mark, detail = verdict(expect, skill)
            results.append((prompt, expect, mark, detail, tools))
            want = f"/{expect}" if expect else "silence"
            print(f"{mark:<7} {want:<8} {prompt!r} — {detail}")

    if "--record" in sys.argv[1:]:
        record(results)
        print(f"\nwrote {DOC.relative_to(REPO)}")

    failed = [r for r in results if r[2] != "ok"]
    if failed:
        print(f"\n{len(failed)} of {len(results)} cases did not behave as expected")
        return 1
    print(f"\nok  {len(results)} of {len(results)} cases behaved as expected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
