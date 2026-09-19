"""The public-repo check: it refuses a writer's own material, and only that.

Both directions, because a guard that blocks ordinary work gets switched off.
No test reads a real house: every terms source is passed in.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("public_check", ROOT / "scripts" / "public-check.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


class ThisRepo(unittest.TestCase):
    def test_the_repo_as_it_stands_is_clean(self):
        tracked = pc.git("ls-files").splitlines()
        manifest = (ROOT / pc.MANIFEST).read_text()
        self.assertEqual([], pc.check_templates(tracked, manifest))
        files = {f: (ROOT / f).read_text() for f in tracked
                 if f.startswith("knowledge/") and f.endswith(".md") and (ROOT / f).is_file()}
        self.assertEqual([], pc.check_filled(files))


class Templates(unittest.TestCase):
    def test_a_file_the_manifest_does_not_name_is_refused(self):
        out = pc.check_templates(["knowledge/stubs.md"], "knowledge/themes.md\n")
        self.assertEqual(1, len(out))
        self.assertIn("knowledge/stubs.md", out[0])

    def test_a_listed_file_and_files_outside_knowledge_pass(self):
        self.assertEqual([], pc.check_templates(
            ["knowledge/themes.md", "scripts/board.py", pc.MANIFEST],
            "# comment\nknowledge/themes.md\n"))


class Filled(unittest.TestCase):
    def test_a_dated_or_attributed_declaration_is_refused(self):
        for line in ("- Dry and direct. `source: declared, 14 September 2026`",
                     "  approved in chat. `source: declared`\n  (approved in chat, 2026-09-16)".replace("`\n  (", "` (")):
            self.assertEqual(1, len(pc.check_filled({"knowledge/p.md": line})), line)

    def test_the_template_form_passes(self):
        text = "- **Job:** [thought-leadership] `source: declared`\n  source: declared\n"
        self.assertEqual([], pc.check_filled({"knowledge/themes.md": text}))

    def test_a_row_in_a_table_that_ships_empty_is_refused(self):
        table = "| Date | Rule |\n|------|------|\n| 2026-09-17 | x |\n"
        self.assertEqual(1, len(pc.check_filled({"knowledge/metrics.md": table})))
        self.assertEqual([], pc.check_filled({"knowledge/metrics.md": table.rsplit("| 2026", 1)[0]}))


class Replaced(unittest.TestCase):
    """A blank template that loses its placeholders has been filled in."""
    LISTED = "knowledge/longform-channels.md\nknowledge/themes.md\n"
    PH = ["- **Job:** [what this channel is for]", "- **Audience:** [who reads it]",
          "- **Length:** [words]", "- **Form:** [what shape it rewards]"]

    def test_placeholders_swapped_for_content_are_refused(self):
        out = pc.check_replaced({"knowledge/longform-channels.md":
                                 (self.PH, ["- **Job:** reach.", "- **Length:** 600 words."])},
                                self.LISTED)
        self.assertEqual(1, len(out))
        self.assertIn("knowledge/longform-channels.md", out[0])

    def test_a_reworded_placeholder_passes(self):
        self.assertEqual([], pc.check_replaced({"knowledge/themes.md":
                         (self.PH[:1], ["- **Job:** [one sentence on its job]"])}, self.LISTED))

    def test_a_rewrite_that_keeps_placeholders_passes(self):
        self.assertEqual([], pc.check_replaced({"knowledge/themes.md":
                         (self.PH, ["- **Job:** [what it is for]", "Some new guidance."])}, self.LISTED))

    def test_a_removal_with_nothing_added_passes(self):
        self.assertEqual([], pc.check_replaced({"knowledge/themes.md": (self.PH, [])}, self.LISTED))

    def test_a_link_is_not_a_placeholder(self):
        links = ["See [the guide](docs/a.md)", "See [the rules](docs/b.md)", "See [the map](docs/c.md)"]
        self.assertEqual([], pc.check_replaced({"knowledge/themes.md": (links, ["prose only"])},
                                               self.LISTED))

    def test_a_file_outside_the_manifest_or_not_markdown_is_left_to_other_checks(self):
        self.assertEqual([], pc.check_replaced({"docs/plan.md": (self.PH, ["content"]),
                                                "knowledge/TEMPLATES": (self.PH, ["x"])}, self.LISTED))

    def test_a_diff_is_read_into_removed_and_added_lines(self):
        diff = ("--- a/knowledge/themes.md\n+++ b/knowledge/themes.md\n"
                "-[a]  \n-[bb]\n+content\n")
        orig = pc.git
        pc.git = lambda *a: "abc\n" if a[0] == "merge-base" else diff
        try:
            got = pc.removed_and_added("origin/main")
        finally:
            pc.git = orig
        self.assertEqual((["[a]  ", "[bb]"], ["content"]), got["knowledge/themes.md"])


class Terms(unittest.TestCase):
    def test_terms_come_from_the_secret_and_the_house_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("# a comment\nJane Example\n\n")
        terms = pc.load_terms({"FAMILIAR_PRIVATE_TERMS": "Acme Corp\n"}, f.name)
        Path(f.name).unlink()
        self.assertEqual(["Acme Corp", "Jane Example"], terms)

    def test_no_terms_means_nothing_found_and_the_caller_decides(self):
        self.assertEqual([], pc.load_terms({}, "/nonexistent/terms.txt"))
        self.assertEqual([], pc.find_terms([("x", "Jane Example")], [], True))

    def test_a_term_in_an_added_line_or_a_pr_description_is_refused(self):
        sources = [("a.md (added lines)", "ok\nI read jane example weekly"),
                   ("PR description", "Approved by Jane Example")]
        out = pc.find_terms(sources, ["Jane Example"], show_term=True)
        self.assertEqual(2, len(out))
        self.assertIn("line 2", out[0])

    def test_whole_words_only(self):
        self.assertEqual([], pc.find_terms([("a", "brisket, Brisklands")], ["Brisk"], True))
        self.assertEqual(1, len(pc.find_terms([("a", "at Brisk.")], ["Brisk"], True)))

    def test_a_public_log_never_prints_the_term(self):
        out = pc.find_terms([("a", "Jane Example")], ["Jane Example"], show_term=False)
        self.assertNotIn("Jane", out[0])
        self.assertIn("a private term", out[0])


if __name__ == "__main__":
    unittest.main()
