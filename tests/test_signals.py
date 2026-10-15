"""signals.py hands the outline at most five research signals, or says why not.

It refuses a file whole and never trims one, because choosing which signals
survive is the writer's call. Examples are invented; no writer's material here.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("signals", ROOT / "scripts" / "signals.py")
signals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signals)


def one(**over):
    return {"signal": "Three teams report the same handover gap", "sources": ["https://example.com/a"],
            "changes": "Supports the claim in the second section", **over}


class Read(unittest.TestCase):
    def read(self, content=None, raw=None):
        with tempfile.TemporaryDirectory() as home:
            piece = Path(home) / "2026-01-01-example"
            piece.mkdir()
            if raw is not None:
                (piece / "signals.json").write_text(raw)
            elif content is not None:
                (piece / "signals.json").write_text(json.dumps(content))
            return signals.read(piece)

    def test_no_file_is_none_and_the_outline_carries_on(self):
        result = self.read()
        self.assertEqual("none", result["state"])
        self.assertEqual(0, signals.main([str(Path(tempfile.gettempdir()) / "no-such-piece")]))

    def test_signals_come_back_numbered_with_their_own_addresses(self):
        result = self.read({"lead": "Handover", "distilled": "2026-01-01",
                            "signals": [one(), one(sources=["https://example.com/b", "https://example.org/c"])]})
        self.assertEqual("ok", result["state"])
        self.assertEqual(["S1", "S2"], [s["id"] for s in result["signals"]])
        self.assertEqual(["https://example.com/b", "https://example.org/c"], result["signals"][1]["sources"])

    def test_six_signals_are_refused_whole_not_trimmed(self):
        result = self.read({"signals": [one()] * 6})
        self.assertEqual("refused", result["state"])
        self.assertIn("6 signals; the limit is 5", result["reason"])
        self.assertNotIn("signals", result)

    def test_five_signals_pass(self):
        self.assertEqual(5, len(self.read({"signals": [one()] * 5})["signals"]))

    def test_one_bad_signal_refuses_the_file(self):
        for bad, why in ((one(signal="first\nsecond"), "more than one line"),
                         (one(changes=""), "no what-it-changes line"),
                         (one(sources=[]), "no source address"),
                         (one(sources=["not a link"]), "not a web address"),
                         ("a string", "is not a signal")):
            result = self.read({"signals": [one(), bad]})
            self.assertEqual("refused", result["state"], why)
            self.assertIn(why, result["reason"])

    def test_an_unreadable_file_is_refused_with_the_reason(self):
        self.assertIn("cannot be read", self.read(raw="{")["reason"])
        self.assertIn("no list of signals", self.read({"signals": "five"})["reason"])
        self.assertIn("no list of signals", self.read(["not", "a", "dict"])["reason"])

    def test_unresolved_and_held_items_are_shown_apart_from_the_signals(self):
        result = self.read({"signals": [one()], "unresolved": [{"what": "A fourth signal", "reason": "over one line"}],
                            "held": [{"url": "https://example.com/held", "reason": "spoke to the tool"}]})
        text = signals.render(result)
        self.assertIn("Shown to the writer, never used:", text)
        self.assertLess(text.index("S1."), text.index("unresolved: A fourth signal"))
        self.assertIn("held back: https://example.com/held", text)

    def test_a_refused_file_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as home:
            (Path(home) / "signals.json").write_text("{")
            self.assertEqual(1, signals.main([home]))


if __name__ == "__main__":
    unittest.main()
