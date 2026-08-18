#!/usr/bin/env python3
"""Check docs/index.html still tells the truth about this repo.

The published page states counts and routing outcomes. Those are exactly the
claims that rot silently: add a prompt, rename a probe, gain a test, and the
page keeps saying the old number to everyone who visits it.

    ./scripts/check_page.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "docs" / "index.html"
PROBES = REPO / "scripts" / "probes.json"

# A probe row: what you type, then either a trigger or the silence marker.
ROW_RE = re.compile(
    r'<td class="said">([^<]+)</td>.*?'
    r'<td>(?:<span class="trig">/(\w+)|<span class="silent">silence)',
    re.S)


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True, cwd=REPO)
    return result.stdout + result.stderr


def check(page, report):
    triggers = sorted(d.name for d in REPO.iterdir() if (d / "SKILL.md").is_file())
    for trigger in triggers:
        if f">/{trigger}<" not in page:
            report.append(f"/{trigger} exists but the page never mentions it")
    listed = set(re.findall(r'<div class="trig">/(\w+)</div>', page))
    for extra in sorted(listed - set(triggers)):
        report.append(f"the page advertises /{extra}, which is not a prompt folder")
    if f"{len(triggers)} prompts" not in page:
        report.append(f"the page's prompt count is not {len(triggers)}")

    expected = {p["prompt"]: p["expect"] for p in json.loads(PROBES.read_text())["probes"]}
    for said, trigger in ROW_RE.findall(page):
        want, got = expected.get(said, "not a probe at all"), trigger or None
        if want != got:
            report.append(f'"{said}" is shown running /{got or "nothing"}, '
                          f'but probes.json expects {want or "silence"}')

    counts = re.search(r"ok  (\d+) phrasings and (\d+) probes", run("./scripts/check_phrasings.py"))
    if not counts:
        report.append("check_phrasings.py is failing, so its numbers cannot be trusted")
    else:
        phrasings, probes = counts.groups()
        if f"{phrasings} phrasings and {probes} probes" not in page:
            report.append(f"the page's split is not {phrasings} phrasings and {probes} probes")
        if f"{int(phrasings) + int(probes)} phrasings &amp; probes measured" not in page:
            report.append(f"the page's badge total is not {int(phrasings) + int(probes)}")

    tests = re.search(r"Ran (\d+) tests",
                      run("python3", "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py"))
    if tests and f"{tests.group(1)} tests across" not in page:
        report.append(f"the page's test count is not {tests.group(1)}")


def main():
    if not PAGE.is_file():
        print(f"{PAGE.relative_to(REPO)} is missing")
        return 1
    report = []
    check(PAGE.read_text(encoding="utf-8"), report)
    for problem in report:
        print(f"stale  {problem}")
    if report:
        print(f"\n{len(report)} claim(s) on the page no longer match the repo")
        return 1
    print("ok  docs/index.html matches the prompts, probes, and counts it claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())
