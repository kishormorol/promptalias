#!/usr/bin/env python3
"""Claude Code UserPromptSubmit hook: point the agent at a matching prompt.

`docs/prior-art.md` calls this the one case a SKILL.md compiler cannot serve —
selecting a prompt from your own words requires seeing the input string, which
only a hook does. It is Claude Code only, by construction: Codex and Cursor
expose no equivalent, so nothing here works there. Richer `Use when` clauses
cost nothing and work in all three; reach for this only after those miss.

Phrases come from two places:

  * every quoted example in each prompt's `description` — the same text the
    agent already matches on, so the hook and the descriptions cannot drift;
  * `hooks/vocabulary.json`, your own wording, which outranks the above.

What it does not do: block, rewrite, or invoke anything. It appends one line of
context naming the prompt it matched. Any failure exits silently — a broken
hook must never cost you a turn.

    ./hooks/resolve.py --explain "make the parser also handle tabs"
    ./hooks/resolve.py --list
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VOCABULARY = Path(__file__).resolve().parent / "vocabulary.json"

# A quoted example inside a description, straight or typographic quotes.
QUOTED_RE = re.compile(r'"([^"]{3,})"|“([^”]{3,})”')

# A lone capital in an example stands for whatever the user actually says:
# "make X also do Y".
PLACEHOLDER_RE = re.compile(r"^[A-Z]$")

# Your own wording is deliberate, so it beats a phrase lifted from a description.
VOCABULARY_BONUS = 1000


class Phrase:
    def __init__(self, trigger, text, source):
        self.trigger = trigger
        self.text = text
        self.source = source
        self.regex = compile_phrase(text)
        # Longer, more specific phrasings win; placeholders count for nothing.
        self.weight = len(re.sub(r"\s+", " ", strip_placeholders(text)))
        if source == "vocabulary":
            self.weight += VOCABULARY_BONUS


def strip_placeholders(text):
    return " ".join("" if PLACEHOLDER_RE.match(w) else w for w in text.split())


def compile_phrase(text):
    """Turn an example phrasing into a pattern that matches a real sentence."""
    parts = []
    for word in text.split():
        trailing = ""
        while word and word[-1] in ".,!?;:":
            trailing = word[-1] + trailing
            word = word[:-1]
        if PLACEHOLDER_RE.match(word):
            parts.append(r".{1,60}?")
            continue
        if not word:
            continue
        chunk = re.escape(word)
        if trailing:
            # "anything wrong with this?" should still match without the mark.
            chunk += "[" + re.escape(trailing) + "]?"
        parts.append(chunk)
    if not parts:
        return None
    body = r"\s+".join(parts)
    return re.compile(r"(?<!\w)" + body + r"(?!\w)", re.IGNORECASE)


def read_description(skill):
    """The description line, with any indented continuation folded in."""
    lines = skill.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    value, collecting = None, False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if collecting and line[:1].isspace():
            value += " " + line.strip()
            continue
        collecting = False
        key, sep, rest = line.partition(":")
        if sep and key.strip() == "description":
            value, collecting = rest.strip(), True
    return value


def load_phrases(root=REPO):
    phrases = []
    for skill in sorted(root.glob("*/SKILL.md")):
        description = read_description(skill)
        if not description:
            continue
        trigger = skill.parent.name
        for straight, curly in QUOTED_RE.findall(description):
            phrases.append(Phrase(trigger, straight or curly, "description"))

    if VOCABULARY.is_file():
        try:
            data = json.loads(VOCABULARY.read_text(encoding="utf-8"))
            for trigger, own in sorted(data.get("prompts", {}).items()):
                for text in own:
                    phrases.append(Phrase(trigger, text, "vocabulary"))
        except (ValueError, AttributeError, TypeError):
            pass  # A malformed vocabulary is validate.py's problem to report.

    return [p for p in phrases if p.regex]


def resolve(prompt, phrases=None):
    """Return (trigger, phrase, rivals). trigger is None when nothing wins."""
    phrases = load_phrases() if phrases is None else phrases
    if not prompt or prompt.lstrip().startswith("/"):
        # An explicit slash command is already a choice; do not second-guess it.
        return None, None, []

    hits = [p for p in phrases if p.regex.search(prompt)]
    if not hits:
        return None, None, []

    best = max(p.weight for p in hits)
    winners = {p.trigger for p in hits if p.weight == best}
    top = max((p for p in hits if p.weight == best), key=lambda p: len(p.text))
    if len(winners) > 1:
        # Two prompts match equally well. Saying so is worth more than a coin toss.
        return None, top, sorted(winners)
    return top.trigger, top, sorted({p.trigger for p in hits} - winners)


def context_line(trigger, phrase, rivals):
    line = (
        f'The user\'s wording matches the /{trigger} prompt (on "{phrase.text}"). '
        f"Invoke the {trigger} skill unless it plainly does not fit this request."
    )
    if rivals:
        line += " Also matched, less specifically: " + ", ".join("/" + r for r in rivals) + "."
    return line


def explain(prompt):
    trigger, phrase, rivals = resolve(prompt)
    if trigger:
        print(f'/{trigger}  <- "{phrase.text}" ({phrase.source})')
        if rivals:
            print("also matched: " + ", ".join("/" + r for r in rivals))
        return 0
    if phrase:
        print("ambiguous: " + ", ".join("/" + r for r in rivals) + f' both match "{phrase.text}"')
        return 1
    print("no match")
    return 1


def main():
    args = sys.argv[1:]
    if args and args[0] == "--explain":
        return explain(" ".join(args[1:]))
    if args and args[0] == "--list":
        for phrase in sorted(load_phrases(), key=lambda p: (p.trigger, p.text)):
            print(f"/{phrase.trigger:<3} {phrase.weight:>5}  {phrase.text}  [{phrase.source}]")
        return 0

    try:
        payload = json.load(sys.stdin)
        trigger, phrase, rivals = resolve(payload.get("prompt", ""))
        if not trigger:
            return 0
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context_line(trigger, phrase, rivals),
        }}))
    except Exception:
        return 0  # Never cost the user a turn over a hook.
    return 0


if __name__ == "__main__":
    sys.exit(main())
