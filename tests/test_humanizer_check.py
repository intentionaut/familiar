"""The humanizer drift report must not say "none" when it cannot know. Tested both ways:
a sign with no house rule is listed, a sign with one is left alone, and an input the
script cannot read yields "cannot tell", never an empty list.
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("humanizer_check", ROOT / "scripts" / "humanizer-check.py")
hc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hc)

SKILL = """---
version: 3.1.0
---
### 1. Not X but Y
### 2. Sayings that sound deep
### 3. Re-explaining what the reader knows
**Watch for:** none
"""
# Mirrors the real file: rule 3 below is about readers and knowledge, which is
# what fooled the old word matcher into reporting a counterpart.
RULES = """### A. Staging

1. **Not X but Y.** "not just X, but Y".
2. **Sayings that sound deep.** "the real question is".

Treating the reader as knowing nothing about a topic they chose to read.
"""


class HumanizerReport(unittest.TestCase):
    def test_sign_with_no_house_rule_is_listed(self):
        r = hc.analyse(SKILL, RULES, RULES)
        self.assertEqual(r["patterns_status"], "ok")
        self.assertEqual([n for n, _ in r["missing_patterns"]], ["3"])

    def test_covered_signs_are_not_listed(self):
        rules = RULES + '3. **Re-explaining what the reader knows.** Lead with the answer.\n'
        r = hc.analyse(SKILL, rules, rules)
        self.assertEqual(r["missing_patterns"], [])
        self.assertEqual(r["patterns_status"], "ok")

    def test_unreadable_house_rules_say_cannot_tell(self):
        r = hc.analyse(SKILL, "no numbered rules here", "")
        self.assertEqual(r["patterns_status"], "unknown")

    def test_no_patterns_parsed_says_cannot_tell(self):
        r = hc.analyse("version: 3.1.0\nnothing numbered", RULES, RULES)
        self.assertEqual(r["patterns_status"], "unknown")

    def test_report_text_never_says_none_when_unknown_or_missing(self):
        gap = hc.render(hc.analyse(SKILL, RULES, RULES), "2026-01-01")
        self.assertIn("§3 Re-explaining what the reader knows", gap)
        unk = hc.render(hc.analyse("nothing", RULES, RULES), "2026-01-01")
        self.assertIn("cannot tell", unk.lower())
        pat_section = unk.split("## Humanizer patterns")[1]
        self.assertNotIn("- none", pat_section)

    def test_summary_is_not_zero_when_unknown(self):
        s = hc.summary(hc.analyse("nothing", RULES, RULES))
        self.assertIsNone(s["missing_patterns"])
        self.assertEqual(s["patterns_status"], "unknown")


if __name__ == "__main__":
    unittest.main()
