"""The parts of measure_invocation.py that do not cost a billed session.

Everything here is the bookkeeping around the measurement: the rates it keeps,
the prose it generates from them, and the check that the documents still agree
with the numbers. The measuring itself needs the real model and is run by hand.
"""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure_invocation as m  # noqa: E402

ROW = {"prompt": "why is the resolver broken", "expect": "d", "runs": 7,
       "outcomes": {"/d": 6, "nothing": 1}, "measured": "17-18 August 2026"}


class RateProse(unittest.TestCase):
    def test_a_rate_is_written_in_words(self):
        self.assertIn("`/d` six times out of seven", m.rate_sentence(ROW))

    def test_the_other_outcomes_are_named_too(self):
        self.assertIn("nothing once", m.rate_sentence(ROW))

    def test_the_caveat_carries_the_measured_numbers(self):
        bullet = m.repeat_bullet([ROW])
        self.assertIn("six times out of seven", bullet)
        self.assertIn("17-18 August 2026", bullet)

    def test_the_caveat_says_so_when_nothing_was_repeated(self):
        self.assertIn("has been run twice", m.repeat_bullet([]))


class RecordingARate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.file = Path(self.tmp.name) / "repeat_runs.json"

    def test_a_repeated_run_is_kept_as_data(self):
        results = [("why is the resolver broken", "d", "ok", "invoked /d", [],
                    {"/d": 6, "nothing": 1}, 7)]
        m.record_repeats(results, path=self.file)
        kept = json.loads(self.file.read_text())["runs"]
        self.assertEqual(kept[0]["outcomes"], {"/d": 6, "nothing": 1})
        self.assertEqual(kept[0]["runs"], 7)

    def test_a_later_run_replaces_the_earlier_rate(self):
        for held in (6, 5):
            m.record_repeats([("why is the resolver broken", "d", "ok", "invoked /d", [],
                               {"/d": held, "nothing": 7 - held}, 7)], path=self.file)
        kept = json.loads(self.file.read_text())["runs"]
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["outcomes"]["/d"], 5)


class CheckingTheDocuments(unittest.TestCase):
    def test_the_repo_as_committed_agrees_with_its_own_numbers(self):
        self.assertEqual(m.check_docs(), [])

    def test_a_page_claiming_an_unmeasured_rate_is_caught(self):
        page = m.PAGE
        original = page.read_text(encoding="utf-8")
        page.write_text(original.replace("six times out of seven",
                                         "seven times out of seven"), encoding="utf-8")
        try:
            report = m.check_docs()
        finally:
            page.write_text(original, encoding="utf-8")
        self.assertTrue(any("which no run in repeat_runs.json measured" in p for p in report))

    def test_a_doc_whose_caveat_drifted_is_caught(self):
        drifted = dict(ROW, outcomes={"/d": 5, "nothing": 2})
        report = m.check_docs(repeats=[drifted])
        self.assertTrue(any("no longer matches repeat_runs.json" in p for p in report))


class Flags(unittest.TestCase):
    def test_check_runs_nothing_so_it_stands_alone(self):
        with self.assertRaises(SystemExit):
            m.parse_args(["--check", "--record"])

    def test_recording_one_sentence_needs_a_repeat_to_be_a_rate(self):
        with self.assertRaises(SystemExit):
            m.parse_args(["--only", "resolver", "--record"])

    def test_a_repeated_run_may_be_recorded(self):
        args = m.parse_args(["--only", "resolver", "-n", "7", "--record"])
        self.assertEqual((args.repeat, args.record), (7, True))


class GeneratedDoc(unittest.TestCase):
    def test_the_table_is_led_by_what_one_row_is_worth(self):
        results = [("why is the resolver broken", "d", "ok", "invoked /d", ["Bash"],
                    {"/d": 1}, 1)]
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "doc.md"
        m.record(results, path=out, repeats=[ROW], when=date(2026, 8, 17))
        text = out.read_text()
        lead = text.index("Every row below is one session")
        self.assertLess(lead, text.index("| Sentence |"))
        self.assertIn("a session is a coin, not a rate", text)
        self.assertIn("17 August 2026", text)


if __name__ == "__main__":
    unittest.main()
