"""Markdown to Notion blocks and back.

Every input is synthetic. Nothing here reaches Notion.

The rules under test:
  - what a draft uses comes back identical, and a second trip changes nothing
  - what cannot make the trip is refused, and named, never dropped
  - a text over Notion's 2,000-character limit is split and rejoined whole
  - a block read from Notion renders the way a block made here does
  - formatting with no markdown form is dropped and counted; the text stays
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import notion_blocks as nb  # noqa: E402

IDENTICAL = {
    "paragraphs": "First paragraph.\n\nSecond paragraph, with a soft\nwrapped line.",
    "headings 1 to 3": "# One\n\n## Two\n\n### Three\n\nBody.",
    "emphasis": "**bold**, *italic*, ~~gone~~ and `code` in one line.",
    "nested emphasis": "**bold with *italic* inside** and more.",
    "links": "See [the guide](https://example.com/a?b=1) now.",
    "link with formatting": "See [**the** guide](https://example.com) now.",
    "bullets": "- one\n- two\n- three",
    "nested bullets": "- one\n  - two\n    - three\n- four",
    "numbered": "1. one\n2. two\n3. three",
    "numbered with nested bullets": "1. a\n   - b\n2. c",
    "task list": "- [ ] open\n- [x] done",
    "wrapped list item": "- one\n  continues here\n- two",
    "list then paragraph": "- a\n- b\n\nAfter the list.",
    "a bullet list then a numbered one": "- a\n- b\n\n1. one\n2. two",
    "block quote": "> a quote\n> on two lines",
    "code fence": "```python\ndef f():\n    return 1\n```",
    "code with an unknown language": "```weirdlang\nx\n```",
    "code with no language": "```\na\n\n\nb\n```",
    "code with an alias": "```js\nlet a = 1\n```",
    "divider": "Above.\n\n---\n\nBelow.",
    "table": "| A | B |\n| --- | --- |\n| 1 | 2 |\n| **x** | `y` |",
    "image": "![A chart](https://example.com/c.png)",
    "footnote text": "A claim.[^1]\n\n[^1]: The source.",
    "html comment": "Text.\n\n<!-- a note -->\n\nMore.",
    "open brackets": "It grew 40%. [NEEDS SOURCE: the survey]\n\nAsk here. [ASK THE WRITER: the date]",
    "bracket then parens": "[NEEDS SOURCE: x](see y) and (a) [b].",
    "snake case and stars": "use snake_case_names and 2 * 3 * 4 here",
    "a paragraph that looks like a list": "1\\. not a list\n\n\\- not a bullet",
    "hard break": "line one  \nline two",
    "unicode": "Café — “quoted” 🙂 日本語",
    "long paragraph": ("word " * 700).strip(),
}

COSMETIC = {
    "star and plus bullets": ("* one\n* two", "- one\n- two"),
    "underscore emphasis": ("_italic_ and __bold__", "*italic* and **bold**"),
    "numbers are counted up": ("1. a\n1. b\n1. c", "1. a\n2. b\n3. c"),
    "table alignment": ("| A | B |\n| :--- | ---: |\n| 1 | 2 |", "| A | B |\n| --- | --- |\n| 1 | 2 |"),
    "a loose list is tight": ("- a\n\n- b", "- a\n- b"),
    "an escaped mark mid-line": ("see 1\\. here", "see 1. here"),
}

REFUSED = {
    "a heading deeper than 3": ("#### Four\n\nBody.", "level 4 heading"),
    "a numbered list starting above 1": ("3. three\n4. four", "starts at 3"),
    "lists nested four levels": ("- a\n  - b\n    - c\n      - d", "more than three levels"),
}


class Trip(unittest.TestCase):
    def test_what_a_draft_uses_comes_back_identical(self):
        for name, md in IDENTICAL.items():
            self.assertEqual(md, nb.canon(md), name)

    def test_a_second_trip_changes_nothing(self):
        for name, md in {**IDENTICAL, **{k: v[0] for k, v in COSMETIC.items()}}.items():
            once = nb.canon(md)
            self.assertEqual(once, nb.canon(once), name)

    def test_cosmetic_differences_are_only_these(self):
        for name, (md, want) in COSMETIC.items():
            self.assertEqual(want, nb.canon(md), name)

    def test_what_cannot_make_the_trip_is_refused_and_named(self):
        for name, (md, fragment) in REFUSED.items():
            with self.assertRaises(nb.Unsupported, msg=name) as cm:
                nb.md_to_blocks(md)
            self.assertIn(fragment, str(cm.exception), name)

    def test_an_empty_body_is_no_blocks(self):
        self.assertEqual([], nb.md_to_blocks(""))
        self.assertEqual("", nb.blocks_to_md([]))


class Shapes(unittest.TestCase):
    def test_a_long_paragraph_is_split_at_2000_characters_and_rejoined(self):
        text = "x" * 4500
        (b,) = nb.md_to_blocks(text)
        parts = [e["text"]["content"] for e in b["paragraph"]["rich_text"]]
        self.assertEqual([2000, 2000, 500], [len(p) for p in parts])
        self.assertEqual(text, nb.canon(text))

    def test_code_keeps_what_was_written_when_notion_has_no_such_language(self):
        (b,) = nb.md_to_blocks("```weirdlang\nx\n```")
        self.assertEqual("plain text", b["code"]["language"])
        self.assertEqual("weirdlang", b["code"]["caption"][0]["text"]["content"])
        (b,) = nb.md_to_blocks("```py\nx\n```")
        self.assertEqual("python", b["code"]["language"])

    def test_a_table_has_a_header_row_and_a_width(self):
        (b,) = nb.md_to_blocks("| A | B |\n| --- | --- |\n| 1 | 2 |")
        self.assertEqual({"table_width": 2, "has_column_header": True, "has_row_header": False},
                         {k: b["table"][k] for k in ("table_width", "has_column_header", "has_row_header")})
        self.assertEqual(2, len(b["table"]["children"]))

    def test_children_are_nested_inside_their_parent_as_the_api_takes_them(self):
        (b,) = nb.md_to_blocks("- a\n  - b")
        (kid,) = b["bulleted_list_item"]["children"]
        self.assertEqual("bulleted_list_item", kid["type"])

    def test_every_block_is_a_dict_the_api_would_accept(self):
        for md in IDENTICAL.values():
            for b in nb.md_to_blocks(md):
                self.assertEqual("block", b["object"])
                self.assertIn(b["type"], b)


def read_shape(text, **ann):
    """A rich-text element as Notion returns it."""
    return {"type": "text", "plain_text": text, "text": {"content": text, "link": None},
            "annotations": {"bold": False, "italic": False, "strikethrough": False, "underline": False,
                            "code": False, "color": "default", **ann}, "href": None}


class Reading(unittest.TestCase):
    def test_a_block_read_from_notion_renders_as_markdown(self):
        tree = [{"id": "1", "type": "heading_2", "has_children": False,
                 "heading_2": {"rich_text": [read_shape("Title")], "is_toggleable": False}},
                {"id": "2", "type": "paragraph", "has_children": False,
                 "paragraph": {"rich_text": [read_shape("Some "), read_shape("bold", bold=True), read_shape(" text")]}}]
        self.assertEqual("## Title\n\nSome **bold** text", nb.blocks_to_md(tree))

    def test_a_link_read_from_notion_uses_href(self):
        el = read_shape("guide")
        el["href"] = "https://example.com"
        tree = [{"id": "1", "type": "paragraph", "paragraph": {"rich_text": [el]}}]
        self.assertEqual("[guide](https://example.com)", nb.blocks_to_md(tree))

    def test_underline_and_colour_are_dropped_counted_and_the_text_kept(self):
        tree = [{"id": "1", "type": "paragraph", "paragraph": {"rich_text": [
            read_shape("kept", underline=True), read_shape(" also", color="red")]}}]
        notes = {}
        self.assertEqual("kept also", nb.blocks_to_md(tree, notes))
        self.assertEqual({"underline": 1, "colour": 1}, notes)

    def test_a_block_the_draft_has_no_form_for_is_refused_and_named(self):
        for kind in ("callout", "toggle", "column_list", "child_page", "embed", "bookmark", "file"):
            tree = [{"id": "1", "type": kind, kind: {}}]
            with self.assertRaises(nb.Unsupported) as cm:
                nb.blocks_to_md(tree)
            self.assertIn(kind, str(cm.exception))

    def test_an_image_uploaded_to_notion_is_refused_because_its_link_expires(self):
        tree = [{"id": "1", "type": "image", "image": {"type": "file", "file": {"url": "https://s3/x"}}}]
        with self.assertRaises(nb.Unsupported) as cm:
            nb.blocks_to_md(tree)
        self.assertIn("uploaded to Notion", str(cm.exception))

    def test_a_toggle_heading_is_refused(self):
        tree = [{"id": "1", "type": "heading_1", "heading_1": {"rich_text": [read_shape("x")], "is_toggleable": True}}]
        with self.assertRaises(nb.Unsupported):
            nb.blocks_to_md(tree)

    def test_empty_spacer_paragraphs_from_editing_are_ignored(self):
        p = lambda t: {"id": t or "e", "type": "paragraph", "paragraph": {"rich_text": [read_shape(t)] if t else []}}
        self.assertEqual("a\n\nb", nb.blocks_to_md([p("a"), p(""), p(""), p("b")]))

    def test_a_number_list_is_counted_up_and_restarts_after_a_break(self):
        n = lambda t: {"id": t, "type": "numbered_list_item", "numbered_list_item": {"rich_text": [read_shape(t)]}}
        para = {"id": "p", "type": "paragraph", "paragraph": {"rich_text": [read_shape("between")]}}
        self.assertEqual("1. a\n2. b\n\nbetween\n\n1. c", nb.blocks_to_md([n("a"), n("b"), para, n("c")]))

    def test_signatures_are_equal_for_equal_blocks_and_differ_for_changed_ones(self):
        a, = nb.md_to_blocks("Same text.")
        b, = nb.md_to_blocks("Same text.")
        c, = nb.md_to_blocks("Other text.")
        self.assertEqual(nb.signature(a), nb.signature(b))
        self.assertNotEqual(nb.signature(a), nb.signature(c))


if __name__ == "__main__":
    unittest.main()
