#!/usr/bin/env python3
"""Check every prompt folder in this repo is a well-formed Agent Skill.

The failure this exists to catch is silent: a `description` without a "Use when"
clause installs fine, shows up in `skills list`, and simply never fires
implicitly. Nothing reports it. So it is checked here.

    ./scripts/validate.py            # errors fail, warnings print
    ./scripts/validate.py --strict   # warnings fail too
    ./scripts/validate.py DIR        # check DIR instead of this repo
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Directories at the repo root that are not prompts.
NOT_PROMPTS = {"docs", "hooks", "scripts", "node_modules"}

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
USE_WHEN_RE = re.compile(r"\buse when\b", re.IGNORECASE)

# Agent Skills frontmatter limits.
MAX_NAME = 64
MAX_DESCRIPTION = 1024

# Repo convention: a body you cannot read in one screen wants to be a real
# skill with reference files, not a shorthand.
MAX_BODY_LINES = 60
MAX_TRIGGER_LEN = 12


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, message):
        self.errors.append((where, message))

    def warn(self, where, message):
        self.warnings.append((where, message))


def split_frontmatter(text):
    """Return (frontmatter_lines, body_lines), or (None, None) if malformed."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1:]
    return None, None


def parse_frontmatter(lines, where, report):
    """Parse the flat `key: value` frontmatter these skills use."""
    fields = {}
    key = None
    for lineno, line in enumerate(lines, start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace():
            # Continuation of the previous value.
            if key is None:
                report.error(where, f"line {lineno}: indented line with no key above it")
            else:
                fields[key] += " " + line.strip()
            continue
        if ":" not in line:
            report.error(where, f"line {lineno}: not `key: value` — {line.strip()!r}")
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if key in fields:
            report.error(where, f"line {lineno}: duplicate key {key!r}")
        fields[key] = value.strip()
    return fields


def check_prompt(folder, report):
    trigger = folder.name
    skill = folder / "SKILL.md"
    where = f"{trigger}/SKILL.md"

    if not skill.is_file():
        report.error(trigger + "/", "no SKILL.md — every prompt folder needs one")
        return None

    text = skill.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    if frontmatter is None:
        report.error(where, "no YAML frontmatter delimited by `---` on the first line")
        return None

    fields = parse_frontmatter(frontmatter, where, report)

    name = fields.get("name")
    if not name:
        report.error(where, "missing `name`")
    else:
        if name != trigger:
            report.error(where, f"`name: {name}` does not match folder name {trigger!r} — the folder is the trigger")
        if len(name) > MAX_NAME:
            report.error(where, f"`name` is {len(name)} chars, limit is {MAX_NAME}")
        if not NAME_RE.match(name):
            report.error(where, f"`name: {name}` must be lowercase letters, digits, and single hyphens")

    description = fields.get("description")
    if not description:
        report.error(where, "missing `description`")
    else:
        if len(description) > MAX_DESCRIPTION:
            report.error(where, f"`description` is {len(description)} chars, limit is {MAX_DESCRIPTION}")
        if not USE_WHEN_RE.search(description):
            report.error(
                where,
                "`description` has no \"Use when\" clause, so this prompt will never "
                "auto-invoke — it will only work if you type the trigger yourself",
            )

    if body is not None and not any(line.strip() for line in body):
        report.error(where, "frontmatter but no body — nothing to prompt with")

    if body is not None and len(body) > MAX_BODY_LINES:
        report.warn(where, f"body is {len(body)} lines; convention is one screen (<= {MAX_BODY_LINES})")

    if len(trigger) > MAX_TRIGGER_LEN:
        report.warn(trigger + "/", f"trigger is {len(trigger)} chars; short triggers are the point")

    return description


def check_vocabulary(root, triggers, report):
    """Every trigger the hook's vocabulary names must be a prompt that exists."""
    path = root / "hooks" / "vocabulary.json"
    if not path.is_file():
        return
    where = "hooks/vocabulary.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        report.error(where, f"not valid JSON — {exc}")
        return
    entries = data.get("prompts")
    if not isinstance(entries, dict):
        report.error(where, "missing a `prompts` object mapping trigger -> phrases")
        return
    for trigger, phrases in sorted(entries.items()):
        if trigger not in triggers:
            report.error(where, f"names {trigger!r}, which is not a prompt folder")
        if not isinstance(phrases, list) or not all(isinstance(x, str) for x in phrases):
            report.error(where, f"{trigger!r}: phrases must be a list of strings")
        elif not phrases:
            report.warn(where, f"{trigger!r}: empty phrase list adds nothing")


def parse_args(argv):
    """Return (root, strict). A bare argument is the directory to check."""
    root, strict = REPO, False
    for arg in argv:
        if arg == "--strict":
            strict = True
        elif arg.startswith("-"):
            print(f"unknown option {arg!r}", file=sys.stderr)
            sys.exit(2)
        else:
            root = Path(arg)
    return root, strict


def main():
    root, strict = parse_args(sys.argv[1:])
    report = Report()

    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1

    folders = sorted(
        p for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name not in NOT_PROMPTS
    )

    if not folders:
        print("no prompt folders found", file=sys.stderr)
        return 1

    for folder in folders:
        check_prompt(folder, report)

    check_vocabulary(root, {f.name for f in folders}, report)

    for where, message in report.errors:
        print(f"error  {where}: {message}")
    for where, message in report.warnings:
        print(f"warn   {where}: {message}")

    counted = len(folders)
    if report.errors:
        print(f"\n{len(report.errors)} error(s) across {counted} prompt(s)")
        return 1
    if report.warnings and strict:
        print(f"\n{len(report.warnings)} warning(s) across {counted} prompt(s), --strict")
        return 1

    triggers = " ".join("/" + f.name for f in folders)
    print(f"ok  {counted} prompt(s) valid: {triggers}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
