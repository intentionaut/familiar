"""The live check, run against a fake Notion.

It is the tool the owner runs once against a real workspace, so its own rules
are tested here: read only unless told otherwise, one test row and no more, no
deletes, a token that is never printed, and honest reports of what it found.
"""
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import notion_check as nc  # noqa: E402
import test_notion_board as tn  # noqa: E402
import test_notion_draft as td  # noqa: E402


def run(fake, write=False, token=tn.TOKEN, database=tn.DB):
    out = io.StringIO()
    fails = nc.run(database, token, write=write, out=out, transport=fake, sleep=lambda s: None,
                   clock=lambda: 0.0)
    return fails, out.getvalue()


class ReadOnly(unittest.TestCase):
    def test_it_checks_the_connection_and_the_properties_and_writes_nothing(self):
        fake = td.FakePages()
        fails, text = run(fake)
        self.assertEqual(0, fails, text)
        self.assertIn("Nothing was written", text)
        self.assertEqual([], [c for c in fake.calls if c[0] in ("POST", "PATCH", "DELETE") and "/query" not in c[1]])
        self.assertEqual([], fake.pages)

    def test_a_missing_token_is_a_failure_that_says_where_it_goes(self):
        fails, text = run(td.FakePages(), token="")
        self.assertEqual(1, fails)
        self.assertIn(nc.nb.TOKEN_ENV, text)

    def test_the_token_is_never_printed(self):
        for write in (False, True):
            _, text = run(td.FakePages(), write=write)
            self.assertNotIn(tn.TOKEN, text)

    def test_a_database_that_is_not_an_id_is_named(self):
        fails, text = run(td.FakePages(), database="[database ID or URL]")
        self.assertEqual(1, fails)
        self.assertIn("ID or its URL", text)

    def test_a_drifted_board_lists_what_is_wrong_and_how_to_fix_it(self):
        fake = td.FakePages(schema={"Name": {"type": "title"}, "State": {"type": "status"}})
        fails, text = run(fake)
        self.assertEqual(1, fails)
        self.assertIn('"Piece ID" is missing', text)
        self.assertIn("board-provider.md", text)

    def test_a_board_the_integration_cannot_see_is_a_failure_with_what_to_do(self):
        fake = td.FakePages()
        fake.script = [(404, {}, {"code": "object_not_found"})]
        fails, text = run(fake)
        self.assertEqual(1, fails)
        self.assertIn("Share the database", text)


class Write(unittest.TestCase):
    def test_a_full_round_trip_passes_and_leaves_exactly_one_row(self):
        fake = td.FakePages()
        fails, text = run(fake, write=True)
        self.assertEqual(0, fails, text)
        self.assertEqual(1, len(fake.pages))
        self.assertIn("Familiar live check", fake.pages[0]["properties"]["Name"]["title"][0]["plain_text"])
        for line in ("row created", "stale write refused", "draft copied",
                     "what came back matches what went in", "an edit changed one block in place"):
            self.assertIn(line, text)

    def test_it_never_deletes_the_row_and_says_to_delete_it_yourself(self):
        fake = td.FakePages()
        _, text = run(fake, write=True)
        self.assertEqual([], [c for c in fake.calls if c[0] == "DELETE" and "/pages/" in c[1]])
        self.assertIn("Delete the row", text)
        self.assertIn("left in place", text)

    def test_the_sample_carries_every_kind_of_content_a_draft_uses(self):
        kinds = {b["type"] for b in nc.blocks.md_to_blocks(nc.SAMPLE)}
        for k in ("paragraph", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item",
                  "to_do", "quote", "code", "table", "divider", "image"):
            self.assertIn(k, kinds)
        self.assertGreater(max(len(p) for p in nc.SAMPLE.split("\n\n")), 2000)

    def test_a_difference_notion_introduces_is_shown_not_hidden(self):
        fake = td.FakePages()
        real = fake._read_rich

        def trimming(els):
            out = real(els)
            for e in out:                                   # Notion trims trailing spaces
                e["plain_text"] = e["plain_text"].replace("  \n", "\n")
                e["text"]["content"] = e["plain_text"]
            return out
        fake._read_rich = trimming
        fails, text = run(fake, write=True)
        self.assertGreaterEqual(fails, 1)
        self.assertIn("differs from what went in", text)
        self.assertIn("returned", text)

    def test_the_limits_probe_reports_both_outcomes(self):
        accepting = td.FakePages()
        _, yes = run(accepting, write=True)
        self.assertIn("accepted: a level 4 heading", yes)

        class Refusing(td.FakePages):
            def __call__(self, method, url, headers, body):
                if method == "PATCH" and b"heading_4" in (body or b"") or b"list_start_index" in (body or b""):
                    return 400, {}, {"code": "validation_error"}
                return super().__call__(method, url, headers, body)
        _, no = run(Refusing(), write=True)
        self.assertIn("refused by Notion: a level 4 heading", no)
        self.assertIn("refused by Notion: a numbered list that starts above 1", no)


class Command(unittest.TestCase):
    def test_help_names_write_and_says_it_never_deletes(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "notion_check.py"), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(0, r.returncode)
        self.assertIn("--write", r.stdout)
        self.assertIn("never deletes", r.stdout)

    def test_with_no_token_the_command_exits_one_and_names_the_variable(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("FAMILIAR", "NOTION"))}
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "notion_check.py"), "--database", tn.DB],
                           capture_output=True, text=True, env=env)
        self.assertEqual(1, r.returncode)
        self.assertIn(nc.nb.TOKEN_ENV, r.stdout)


if __name__ == "__main__":
    unittest.main()
