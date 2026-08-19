"""The vocabulary check: does your own wording still buy anything?

hooks/vocabulary.json is read only by the hook, which is Claude Code only. A
phrase in it that the descriptions already resolve costs Codex and Cursor that
wording and returns nothing, so the check exists to catch exactly that.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "hooks"))

import check_phrasings as checker  # noqa: E402
import resolve as resolver  # noqa: E402


class VocabularyEarnsItsKeep(unittest.TestCase):
    def setUp(self):
        self.phrases = resolver.load_phrases()

    def test_every_committed_phrase_reaches_where_no_description_does(self):
        redundant = [r for r in checker.check_vocabulary(self.phrases) if r[3] != "ok"]
        self.assertEqual(redundant, [], "widen the description and drop the phrase")

    def test_a_phrase_lifted_from_a_description_is_reported(self):
        lifted = resolver.Phrase("u", "while keeping the tests green", "vocabulary")
        results = checker.check_vocabulary(self.phrases + [lifted])
        verdicts = {(r[1], r[3]) for r in results}
        self.assertIn(("while keeping the tests green", "redundant"), verdicts)

    def test_the_table_names_what_the_descriptions_do_instead(self):
        for trigger, _text, landed, verdict, _detail in checker.check_vocabulary(self.phrases):
            if verdict == "ok":
                self.assertNotEqual(landed, f"/{trigger}")


if __name__ == "__main__":
    unittest.main()
