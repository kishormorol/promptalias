#!/usr/bin/env python3
"""Tests for hooks/resolve.py.

A UserPromptSubmit hook runs on every prompt you type, so the two properties
that matter most here are negative: it stays silent when it should, and it
never fails loudly enough to cost you a turn.

    ./scripts/test_resolve.py     # or: python3 -m unittest discover scripts
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "resolve.py"
sys.path.insert(0, str(REPO / "hooks"))

import resolve as resolver  # noqa: E402


def phrases(*specs):
    return [resolver.Phrase(trigger, text, source) for trigger, text, source in specs]


class MatchingTest(unittest.TestCase):
    def test_plain_phrase_matches_inside_a_sentence(self):
        p = phrases(("rv", "does this look right", "description"))
        trigger, matched, _ = resolver.resolve("hey, does this look right to you?", p)
        self.assertEqual(trigger, "rv")
        self.assertEqual(matched.text, "does this look right")

    def test_placeholder_stands_for_real_words(self):
        p = phrases(("u", "make X also do Y", "description"))
        self.assertEqual(resolver.resolve("make the parser also do tabs", p)[0], "u")

    def test_placeholder_does_not_match_across_a_whole_paragraph(self):
        p = phrases(("u", "make X also do Y", "description"))
        far = "make " + "word " * 30 + "also do it"
        self.assertIsNone(resolver.resolve(far, p)[0])

    def test_trailing_punctuation_is_optional(self):
        p = phrases(("rv", "anything wrong with this?", "description"))
        self.assertEqual(resolver.resolve("anything wrong with this", p)[0], "rv")
        self.assertEqual(resolver.resolve("anything wrong with this?", p)[0], "rv")

    def test_matching_ignores_case_and_extra_spacing(self):
        p = phrases(("t", "write tests for X", "description"))
        self.assertEqual(resolver.resolve("Write   Tests  For the parser", p)[0], "t")

    def test_partial_words_do_not_match(self):
        p = phrases(("p", "plan X", "description"))
        self.assertIsNone(resolver.resolve("replanting the garden", p)[0])

    def test_more_specific_phrase_wins(self):
        p = phrases(("d", "fix this", "description"),
                    ("rv", "fix this error in the review", "description"))
        self.assertEqual(resolver.resolve("fix this error in the review", p)[0], "rv")

    def test_your_own_wording_outranks_a_description(self):
        p = phrases(("d", "check the logs for X", "description"),
                    ("rv", "check", "vocabulary"))
        self.assertEqual(resolver.resolve("check the logs for errors", p)[0], "rv")

    def test_a_tie_between_prompts_stays_silent(self):
        p = phrases(("u", "same words", "description"),
                    ("n", "same words", "description"))
        trigger, matched, rivals = resolver.resolve("same words", p)
        self.assertIsNone(trigger)
        self.assertEqual(matched.text, "same words")
        self.assertEqual(rivals, ["n", "u"])

    def test_weaker_matches_are_reported_as_rivals(self):
        p = phrases(("rv", "review the last diff", "description"),
                    ("u", "diff", "description"))
        trigger, _, rivals = resolver.resolve("review the last diff", p)
        self.assertEqual((trigger, rivals), ("rv", ["u"]))

    def test_a_typed_slash_command_is_left_alone(self):
        p = phrases(("rv", "review this", "description"))
        self.assertIsNone(resolver.resolve("/u review this", p)[0])

    def test_empty_prompt_matches_nothing(self):
        p = phrases(("rv", "review this", "description"))
        self.assertIsNone(resolver.resolve("", p)[0])


class DescriptionTest(unittest.TestCase):
    def test_folded_description_is_read_whole(self):
        skill = Path(REPO / "u" / "SKILL.md")
        self.assertIn("Use when", resolver.read_description(skill))

    def test_every_prompt_in_this_repo_contributes_phrases(self):
        found = {p.trigger for p in resolver.load_phrases()}
        expected = {d.name for d in REPO.iterdir()
                    if (d / "SKILL.md").is_file()}
        self.assertEqual(found, expected)


class HookContractTest(unittest.TestCase):
    def run_hook(self, stdin, *args):
        result = subprocess.run(
            [sys.executable, str(HOOK), *args],
            input=stdin, capture_output=True, text=True,
        )
        return result.returncode, result.stdout

    def test_match_emits_useprompt_context(self):
        code, out = self.run_hook(json.dumps({"prompt": "write tests for the resolver"}))
        self.assertEqual(code, 0)
        payload = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(payload["hookEventName"], "UserPromptSubmit")
        self.assertIn("/t", payload["additionalContext"])

    def test_no_match_says_nothing(self):
        code, out = self.run_hook(json.dumps({"prompt": "what is the weather today"}))
        self.assertEqual((code, out.strip()), (0, ""))

    def test_malformed_stdin_exits_quietly(self):
        for stdin in ("", "not json", "[]", json.dumps({"no_prompt": 1})):
            code, out = self.run_hook(stdin)
            self.assertEqual((code, out.strip()), (0, ""), stdin)

    def test_explain_and_list_are_usable_from_the_shell(self):
        code, out = self.run_hook("", "--explain", "does this look right")
        self.assertEqual((code, out.split()[0]), (0, "/rv"))
        code, out = self.run_hook("", "--explain", "what is the weather")
        self.assertEqual((code, out.strip()), (1, "no match"))
        code, out = self.run_hook("", "--list")
        self.assertEqual(code, 0)
        self.assertIn("[vocabulary]", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
