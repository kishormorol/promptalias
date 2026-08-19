#!/usr/bin/env python3
"""Tests for scripts/validate.py.

The validator is the only thing standing between a typo and a prompt that
installs, lists, and silently never fires. So it gets tests of its own.

    ./scripts/test_validate.py        # or: python3 -m unittest discover scripts
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

VALIDATE = Path(__file__).resolve().parent / "validate.py"

GOOD = """---
name: x
description: Do the thing. Use when the user asks for the thing.
---

Body of the prompt.
"""


class ValidatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def prompt(self, trigger, text=GOOD):
        folder = self.root / trigger
        folder.mkdir(parents=True, exist_ok=True)
        if text is not None:
            (folder / "SKILL.md").write_text(text, encoding="utf-8")
        return folder

    def run_validator(self, *args):
        result = subprocess.run(
            [sys.executable, str(VALIDATE), str(self.root), *args],
            capture_output=True, text=True,
        )
        return result.returncode, result.stdout + result.stderr

    def assertOk(self, *args):
        code, out = self.run_validator(*args)
        self.assertEqual(code, 0, out)
        return out

    def assertFails(self, fragment, *args):
        code, out = self.run_validator(*args)
        self.assertEqual(code, 1, out)
        self.assertIn(fragment, out)
        return out

    # A well-formed prompt passes, in both modes.

    def test_valid_prompt_passes(self):
        self.prompt("x")
        self.assertIn("ok  1 prompt(s) valid: /x", self.assertOk())
        self.assertOk("--strict")

    def test_lists_every_trigger(self):
        self.prompt("x")
        self.prompt("rv", GOOD.replace("name: x", "name: rv"))
        self.assertIn("/rv /x", self.assertOk())

    def test_folded_description_is_read_whole(self):
        self.prompt("x", "---\nname: x\ndescription: Do the thing.\n  Use when asked.\n---\n\nBody.\n")
        self.assertOk()

    # The failure this validator exists for.

    def test_description_without_use_when_is_an_error(self):
        self.prompt("x", GOOD.replace("Use when the user asks for the thing.", "Nothing else."))
        self.assertFails("never auto-invoke")

    # Frontmatter shape.

    def test_missing_skill_file(self):
        self.prompt("x", text=None)
        self.assertFails("no SKILL.md")

    def test_no_frontmatter(self):
        self.prompt("x", "Just a body.\n")
        self.assertFails("no YAML frontmatter")

    def test_unterminated_frontmatter(self):
        self.prompt("x", "---\nname: x\ndescription: Do it. Use when asked.\n")
        self.assertFails("no YAML frontmatter")

    def test_line_that_is_not_key_value(self):
        self.prompt("x", GOOD.replace("name: x", "name: x\nstray line"))
        self.assertFails("not `key: value`")

    def test_duplicate_key(self):
        self.prompt("x", GOOD.replace("name: x", "name: x\nname: x"))
        self.assertFails("duplicate key")

    def test_indented_line_with_no_key_above(self):
        self.prompt("x", "---\n  orphan\nname: x\ndescription: Do it. Use when asked.\n---\n\nBody.\n")
        self.assertFails("indented line with no key above it")

    # name and description fields.

    def test_missing_name(self):
        self.prompt("x", GOOD.replace("name: x\n", ""))
        self.assertFails("missing `name`")

    def test_name_must_match_folder(self):
        self.prompt("x", GOOD.replace("name: x", "name: y"))
        self.assertFails("does not match folder name")

    def test_name_must_be_lowercase_kebab(self):
        self.prompt("X_y", GOOD.replace("name: x", "name: X_y"))
        self.assertFails("lowercase letters, digits, and single hyphens")

    def test_name_length_limit(self):
        long = "a" * 65
        self.prompt(long, GOOD.replace("name: x", f"name: {long}"))
        self.assertFails("limit is 64")

    def test_missing_description(self):
        self.prompt("x", GOOD.replace("description: Do the thing. Use when the user asks for the thing.\n", ""))
        self.assertFails("missing `description`")

    def test_description_length_limit(self):
        self.prompt("x", GOOD.replace("Do the thing.", "Do it. " + "long " * 250))
        self.assertFails("limit is 1024")

    def test_empty_body(self):
        self.prompt("x", "---\nname: x\ndescription: Do it. Use when asked.\n---\n\n\n")
        self.assertFails("no body")

    # Warnings: printed always, fatal only under --strict.

    def test_long_body_warns_and_fails_only_under_strict(self):
        self.prompt("x", GOOD + "\n".join(f"line {i}" for i in range(70)))
        self.assertIn("convention is one screen", self.assertOk())
        self.assertFails("--strict", "--strict")

    def test_long_trigger_warns(self):
        long = "averylongtrigger"
        self.prompt(long, GOOD.replace("name: x", f"name: {long}"))
        self.assertIn("short triggers are the point", self.assertOk())

    # What counts as a prompt folder.

    def test_skips_hidden_and_non_prompt_directories(self):
        self.prompt("x")
        for name in (".github", "docs", "hooks", "scripts", "node_modules"):
            (self.root / name).mkdir()
        self.assertIn("1 prompt(s) valid", self.assertOk())

    def test_no_prompt_folders_at_all(self):
        self.assertFails("no prompt folders found")

    def test_missing_directory(self):
        self.tmp.cleanup()
        self.assertFails("not a directory")

    # The hook's vocabulary, checked against the prompts that exist.

    def vocabulary(self, data):
        hooks = self.root / "hooks"
        hooks.mkdir(exist_ok=True)
        (hooks / "vocabulary.json").write_text(
            data if isinstance(data, str) else json.dumps(data), encoding="utf-8")

    def test_vocabulary_naming_a_real_prompt_passes(self):
        self.prompt("x")
        self.vocabulary({"prompts": {"x": ["do the thing"]}})
        self.assertOk()

    def test_vocabulary_naming_a_missing_prompt_fails(self):
        self.prompt("x")
        self.vocabulary({"prompts": {"gone": ["do the thing"]}})
        self.assertFails("not a prompt folder")

    # Phrasings in other languages. The matcher splits on whitespace, so a script
    # that does not use spaces can never match; one that does works untouched.

    def test_vocabulary_accepts_a_script_that_uses_spaces(self):
        self.prompt("x")
        self.vocabulary({"prompts": {"x": ["X কেন কাজ করছে না", "añade pruebas para X",
                                           "напиши скрипт который Y"]}})
        self.assertOk("--strict")

    def test_vocabulary_rejects_a_script_without_spaces(self):
        self.prompt("x")
        self.vocabulary({"prompts": {"x": ["Xの仕組みを教えて"]}})
        out = self.assertFails("can never fire")
        self.assertIn("Japanese kana", out)

    def test_vocabulary_rejects_han_and_thai_too(self):
        self.prompt("x")
        self.vocabulary({"prompts": {"x": ["解释一下X"]}})
        self.assertIn("Han", self.assertFails("can never fire"))
        self.vocabulary({"prompts": {"x": ["Xはどう動くの"]}})
        self.assertFails("can never fire")

    def test_description_example_without_spaces_warns_but_does_not_fail(self):
        # The agent reads the description itself, so this is worth keeping and
        # worth flagging — only the hook is blind to it.
        self.prompt("x", GOOD.replace("Use when the user asks for the thing.",
                                      'Use when the user says "Xの仕組みを教えて".'))
        out = self.assertOk()
        self.assertIn("the hook will not back it up", out)
        self.assertFails("the hook will not back it up", "--strict")

    def test_description_example_in_a_spaced_script_is_silent(self):
        self.prompt("x", GOOD.replace("Use when the user asks for the thing.",
                                      'Use when the user says "X কেন কাজ করছে না".'))
        self.assertOk("--strict")

    def test_vocabulary_must_be_json(self):
        self.prompt("x")
        self.vocabulary("{not json")
        self.assertFails("not valid JSON")

    def test_vocabulary_needs_a_prompts_object(self):
        self.prompt("x")
        self.vocabulary({"phrases": []})
        self.assertFails("missing a `prompts` object")

    def test_vocabulary_phrases_must_be_strings(self):
        self.prompt("x")
        self.vocabulary({"prompts": {"x": [1, 2]}})
        self.assertFails("must be a list of strings")

    def test_vocabulary_empty_phrase_list_warns(self):
        self.prompt("x")
        self.vocabulary({"prompts": {"x": []}})
        self.assertIn("adds nothing", self.assertOk())


if __name__ == "__main__":
    unittest.main(verbosity=2)
