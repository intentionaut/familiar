"""beehiiv-reconcile.py: proposals only. It matches cards to live posts and writes nothing."""
import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("reconcile", ROOT / "scripts" / "beehiiv-reconcile.py")
rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rec)


def post(title, slug, status="confirmed", date=1760000000):
    return {"id": "post_" + slug, "title": title, "slug": slug, "status": status,
            "web_url": f"https://letter.example.com/p/{slug}", "publish_date": date}


def card(title, state="sent", links=()):
    return {"title": title, "state": state, "links": list(links)}


class Matching(unittest.TestCase):
    def test_an_address_on_the_card_wins(self):
        posts = [post("Impact can't bypass politics", "impact-cant-bypass-politics"),
                 post("Another", "another")]
        r = rec.rows([card("A different draft title",
                           links=["https://letter.example.com/p/impact-cant-bypass-politics"])], posts)[0]
        self.assertEqual((r["rule"], r["confidence"]), ("address", "high"))
        self.assertEqual(r["proposal"]["title"], "Impact can't bypass politics")
        self.assertTrue(r["proposal"]["title_differs"])
        self.assertFalse(r["proposal"]["url_missing"])

    def test_the_same_slug_on_another_address_is_flagged_not_called_current(self):
        posts = [post("One", "one")]
        old = "https://old.example.com/p/one"
        r = rec.rows([card("One", links=[old])], posts)[0]
        self.assertTrue(r["proposal"]["url_differs"])
        self.assertIn("different address", rec.table([r]))
        same = rec.rows([card("One", links=["https://letter.example.com/p/one"])], posts)[0]
        self.assertFalse(same["proposal"]["url_differs"])
        self.assertIn("already on the card", rec.table([same]))

    def test_a_title_match_ignores_case_quotes_and_punctuation(self):
        posts = [post("Impact can’t bypass politics", "impact")]
        r = rec.rows([card("IMPACT CAN'T BYPASS POLITICS!")], posts)[0]
        self.assertEqual((r["rule"], r["confidence"]), ("title", "medium"))
        self.assertTrue(r["proposal"]["url_missing"])
        self.assertFalse(r["proposal"]["title_differs"])

    def test_most_of_the_same_words_is_a_candidate_never_a_match(self):
        posts = [post("Why the roadmap is a promise you cannot keep", "roadmap")]
        r = rec.rows([card("The roadmap is a promise you cannot keep")], posts)[0]
        self.assertEqual((r["rule"], r["confidence"]), ("close", "low"))
        self.assertNotIn("proposal", r)
        self.assertEqual(len(r["candidates"]), 1)

    def test_no_live_post_is_reported_as_none(self):
        r = rec.rows([card("Never sent")], [post("Something else entirely", "x")])[0]
        self.assertEqual((r["rule"], r["confidence"]), ("none", "none"))
        self.assertEqual(r["candidates"], [])
        self.assertNotIn("proposal", r)

    def test_two_equal_candidates_are_listed_and_none_is_picked(self):
        posts = [post("Same title", "same-1"), post("Same title", "same-2")]
        r = rec.rows([card("Same title")], posts)[0]
        self.assertEqual(r["confidence"], "pick one")
        self.assertEqual(len(r["candidates"]), 2)
        self.assertNotIn("proposal", r)


class Reading(unittest.TestCase):
    def fake_get(self, pages):
        calls = []

        def get(url, k):
            calls.append(url)
            if url.endswith("/publications"):
                return {"data": [{"id": "pub_1", "name": "Letter"}]}
            q = dict(p.split("=") for p in url.split("?")[1].split("&"))
            return pages[(q["status"], int(q["page"]))]
        get.calls = calls
        return get

    def test_every_page_and_archived_posts_are_read(self):
        pages = {("confirmed", 1): {"data": [post("One", "one")], "total_pages": 2},
                 ("confirmed", 2): {"data": [post("Two", "two")], "total_pages": 2},
                 ("archived", 1): {"data": [post("Three", "three", status="archived")], "total_pages": 1}}
        got = rec.fetch_posts(self.fake_get(pages), "k", "pub_1")
        self.assertEqual([p["slug"] for p in got], ["one", "two", "three"])

    def test_more_than_one_publication_needs_a_name(self):
        pubs = [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]
        with self.assertRaises(SystemExit) as cm:
            rec.choose_publication(pubs)
        self.assertIn("--publication", str(cm.exception))
        self.assertEqual(rec.choose_publication(pubs, "b")["id"], "b")

    def test_a_read_that_cannot_finish_is_exit_2_and_prints_no_table(self):
        def get(url, k):
            raise OSError("network down")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"BEEHIIV_API_KEY": "k"}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = rec.main([], get=get, cards=[card("x")])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("Nothing was changed", err.getvalue())

    def test_no_key_reads_nothing(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(Path, "cwd", return_value=Path(d)), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(rec.main([], get=lambda *a: 1 / 0, cards=[]), 2)


class CardsFile(unittest.TestCase):
    def test_cards_come_from_a_file_filtered_by_state(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "cards.json"
            f.write_text('[{"title": "A", "state": "sent", "links": ["https://x.example/p/a"]},'
                         ' {"title": "B", "state": "thinking"}]')
            got = rec.cards_from_file(str(f), "sent")
            self.assertEqual(got, [{"title": "A", "state": "sent", "links": ["https://x.example/p/a"]}])

    def test_a_card_with_no_title_is_refused_not_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "cards.json"
            f.write_text('[{"state": "sent"}]')
            with self.assertRaises(ValueError):
                rec.cards_from_file(str(f), "sent")


class WritesNothing(unittest.TestCase):
    def test_a_full_run_leaves_the_folder_exactly_as_it_was(self):
        pages = {("confirmed", 1): {"data": [post("One", "one")], "total_pages": 1},
                 ("archived", 1): {"data": [], "total_pages": 1}}

        def get(url, k):
            if url.endswith("/publications"):
                return {"data": [{"id": "pub_1", "name": "Letter"}]}
            q = dict(p.split("=") for p in url.split("?")[1].split("&"))
            return pages[(q["status"], int(q["page"]))]
        with tempfile.TemporaryDirectory() as d:
            before = sorted(p.name for p in Path(d).rglob("*"))
            with mock.patch.dict(os.environ, {"BEEHIIV_API_KEY": "k"}), \
                    mock.patch.object(Path, "cwd", return_value=Path(d)), \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                code = rec.main([], get=get, cards=[card("One")])
            self.assertEqual(code, 0)
            self.assertEqual(sorted(p.name for p in Path(d).rglob("*")), before)
        self.assertIn("Nothing was changed", out.getvalue())
        self.assertIn("https://letter.example.com/p/one", out.getvalue())


if __name__ == "__main__":
    unittest.main()
