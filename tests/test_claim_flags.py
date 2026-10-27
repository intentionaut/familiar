"""claim-flags.py shows finalise the claims still open, or says why it cannot.

It refuses a file whole rather than show part of it, because a half-read list
looks like a short one. Examples are invented; no writer's material here.
"""
import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("claim_flags", ROOT / "scripts" / "claim-flags.py")
claim_flags = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claim_flags)


def entry(n, claim, route="search"):
    return (f"## F-{n:03d}\n- claim: \"{claim}\"\n- in: draft.md\n- reason: a number with no source\n"
            f"- route: {route}\n- status: proposed\n- sweep:\n\n")


HEAD = "# Claim flags\n\nSuggestions only: mark each Keep or Drop.\n\n"


class Read(unittest.TestCase):
    def read(self, text=None):
        with tempfile.TemporaryDirectory() as home:
            piece = Path(home) / "2026-01-01-example"
            piece.mkdir()
            if text is not None:
                (piece / "flags.md").write_text(text)
            return claim_flags.read(piece)

    # -- keep-cases -------------------------------------------------------------------------------

    def test_no_file_is_none_and_finalise_carries_on(self):
        self.assertEqual("none", self.read()["state"])
        with redirect_stdout(StringIO()):
            self.assertEqual(0, claim_flags.main([str(Path(tempfile.gettempdir()) / "no-such-piece")]))

    def test_a_flag_with_no_decision_is_still_to_decide(self):
        r = self.read(HEAD + entry(1, "Most teams ship weekly"))
        self.assertEqual("ok", r["state"])
        self.assertEqual(["F-001"], [f["id"] for f in r["to_decide"]])
        self.assertEqual("Most teams ship weekly", r["to_decide"][0]["claim"])

    def test_the_newest_decision_stands_and_a_dropped_flag_is_not_open(self):
        text = (HEAD + entry(1, "A") + entry(2, "B") + entry(3, "C")
                + "\n## Decisions\n\n- F-001: kept (2026-01-01)\n- F-002: kept (2026-01-01)\n"
                  "- F-002: dropped (2026-01-02)\n- F-001: swept in 2026-01-02-preview (2026-01-02)\n")
        r = self.read(text)
        self.assertEqual(["F-003"], [f["id"] for f in r["to_decide"]])
        self.assertEqual(["F-001"], [f["id"] for f in r["kept"]])
        self.assertEqual(["2026-01-02-preview"], r["kept"][0]["swept"])
        self.assertEqual(1, r["dropped"])
        self.assertEqual(3, r["total"])

    def test_every_flag_dropped_is_ok_with_nothing_open(self):
        r = self.read(HEAD + entry(1, "A") + "\n## Decisions\n\n- F-001: dropped (2026-01-01)\n")
        self.assertEqual(("ok", [], []), (r["state"], r["to_decide"], r["kept"]))
        self.assertIn("0 open of 1", claim_flags.render(r))

    def test_render_names_each_open_claim_in_its_own_words(self):
        r = self.read(HEAD + entry(1, "Most teams ship weekly") + entry(2, "I ran it for a year", "ask the writer")
                      + "\n## Decisions\n\n- F-002: kept (2026-01-01)\n")
        out = claim_flags.render(r)
        self.assertIn("2 open of 2", out)
        self.assertIn('F-001  "Most teams ship weekly"', out)
        self.assertIn('F-002  "I ran it for a year"', out)

    def test_json_is_the_same_result(self):
        with tempfile.TemporaryDirectory() as home:
            piece = Path(home) / "p"
            piece.mkdir()
            (piece / "flags.md").write_text(HEAD + entry(1, "A"))
            buf = StringIO()
            with redirect_stdout(buf):
                self.assertEqual(0, claim_flags.main([str(piece), "--json"]))
            self.assertEqual(claim_flags.read(piece), json.loads(buf.getvalue()))

    def test_nothing_is_written(self):
        with tempfile.TemporaryDirectory() as home:
            piece = Path(home) / "p"
            piece.mkdir()
            (piece / "flags.md").write_text(HEAD + entry(1, "A"))
            before = {p.name: p.read_bytes() for p in piece.iterdir()}
            with redirect_stdout(StringIO()):
                claim_flags.main([str(piece)])
            self.assertEqual(before, {p.name: p.read_bytes() for p in piece.iterdir()})

    # -- refuse-cases -----------------------------------------------------------------------------

    def test_a_decision_for_an_unknown_flag_refuses_the_file(self):
        r = self.read(HEAD + entry(1, "A") + "\n## Decisions\n\n- F-009: kept (2026-01-01)\n")
        self.assertEqual("refused", r["state"])
        self.assertIn("F-009", r["reason"])

    def test_a_decision_line_out_of_shape_refuses_the_file(self):
        r = self.read(HEAD + entry(1, "A") + "\n## Decisions\n\n- F-001: kept\n")
        self.assertEqual("refused", r["state"])

    def test_a_flag_with_no_claim_refuses_the_file(self):
        r = self.read(HEAD + "## F-001\n- reason: x\n\n")
        self.assertEqual("refused", r["state"])

    def test_a_flag_heading_out_of_shape_refuses_the_file(self):
        r = self.read(HEAD + entry(1, "A") + "## F-2\n- claim: \"B\"\n\n")
        self.assertEqual("refused", r["state"])

    def test_refused_exits_1(self):
        with tempfile.TemporaryDirectory() as home:
            piece = Path(home) / "p"
            piece.mkdir()
            (piece / "flags.md").write_text(HEAD + entry(1, "A") + "\n## Decisions\n\n- F-009: kept (2026-01-01)\n")
            with redirect_stdout(StringIO()):
                self.assertEqual(1, claim_flags.main([str(piece)]))


if __name__ == "__main__":
    unittest.main()
