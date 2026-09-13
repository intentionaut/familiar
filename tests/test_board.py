"""The served board: what it writes, and the rules it writes by.

Every test builds its piece in a temporary folder. Nothing here reads or
writes a real piece.

The rules under test, in the order they matter:
  - draft.md changes only by the writer, typed on the board or a suggestion
    accepted, and a version of what is replaced is kept first
  - a save or an accept made against text that has since changed is refused,
    and nothing is written
  - an agent answers a comment with a suggestion and never touches draft.md
  - a sent piece's draft is never written, because learn diff reads it
  - nothing in rework.md is removed; a comment only gains rounds
"""
import datetime
import http.client
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import board  # noqa: E402
import board_edit as E  # noqa: E402

spec = importlib.util.spec_from_file_location("rework", ROOT / "scripts" / "rework.py")
rework = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rework)

DRAFT = """---
title: "A working title"
title_settled: false
date: 2026-09-13
---

The opening paragraph, which says the thing.

## A heading

- one
- two

> a quote
> over two lines

The closing paragraph.
"""

BODY = ["The opening paragraph, which says the thing.", "## A heading", "- one\n- two",
        "> a quote\n> over two lines", "The closing paragraph."]

DEV = """# Dev-edit report

## 1. Spark assessment

Spark is buried.

## 3. Critical fixes

### 3a. The opening hides the point

Move it up.

### 3b. A claim with nothing under it

Source it.

## 4. Line-level refinement map

- a bullet, not a finding
"""

LINE = '''# Line-edit report

## Findings

**1. Unsourced timing.**

```
[line 35] "within the same week"
Issue: unsourced specific
Fix: cut it
```

[line 7] "Recent studies show"
Issue: announcing evidence without naming it
Fix: name it

## Summary

| Category | Count |
'''

OUTLINE = """# Outline

## Option set: opening move        [stage: outline · 2026-09-13]

### A. Start with the scene
The scene, written out.
Buys: a human frame
Costs: slower

### B. Start with the claim
The claim, written out.
Buys: fast
Costs: cold

## Chosen structure

Nothing yet.
"""

BOLD_OPTIONS = """## 3. Critical fixes

### Option set: opening move [stage: dev-edit · 2026-09-03]

**A. Keep the problem-led opening.**
Buys: useful from sentence one
Costs: opens on a claim

**B. Open inside the scene.**
> Someone opened the app and pressed the wrong button.

Buys: the house default
Costs: delays the framing

**A specific with no source, needs a bracket.**

> a line nobody can back up
"""

LOG = """## 2026-09-13 10:00  outline  {name}

Status: waiting on the writer
Files: outline.md
What changed: three structures offered.
Decision gate: Pick A or B for the opening.
Next stage: draft, when asked.
"""


class Piece(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pieces = Path(self.tmp.name) / "pieces"
        self.folder = self.pieces / "2026-09-13-test-piece"
        (self.folder / "edits").mkdir(parents=True)
        (self.folder / "draft.md").write_text(DRAFT, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def draft(self):
        return (self.folder / "draft.md").read_text(encoding="utf-8")

    def texts(self):
        return [b["text"] for b in E.blocks(self.draft())[1]]

    def gather(self):
        return board.gather(self.folder, datetime.datetime.now().timestamp(), 7)

    def comment(self, quote="The closing paragraph", text="Tighten this.",
                block="The closing paragraph.", **kw):
        return E.comment(self.folder, text, quote=quote, block=block, **kw)


class TheDocument(Piece):
    def test_the_body_is_blocks_and_the_frontmatter_is_none_of_them(self):
        self.assertEqual(BODY, self.texts())

    def test_putting_the_blocks_back_as_they_were_changes_nothing(self):
        self.assertEqual(DRAFT, E.compose(DRAFT, self.texts()))

    def test_a_code_block_with_blank_lines_in_it_is_one_block(self):
        (self.folder / "draft.md").write_text(DRAFT + "\n```\nfirst\n\nsecond\n```\n")
        self.assertEqual("```\nfirst\n\nsecond\n```", self.texts()[-1])

    def test_typing_saves_the_body_and_keeps_the_frontmatter_and_the_old_version(self):
        raw = self.draft()
        E.save_blocks(self.folder, E.digest(raw), BODY[:4] + ["Closed.", "A new last line."])
        new = self.draft()
        self.assertTrue(new.startswith('---\ntitle: "A working title"'))
        self.assertTrue(new.endswith("\n\nClosed.\n\nA new last line.\n"))
        self.assertEqual(raw, E.versions(self.folder)[0].read_text(encoding="utf-8"))

    def test_an_emptied_block_is_left_out_rather_than_saved_as_a_gap(self):
        E.save_blocks(self.folder, E.digest(self.draft()), BODY[:3] + ["   ", BODY[4]])
        self.assertEqual(BODY[:3] + [BODY[4]], self.texts())

    def test_a_save_against_a_changed_file_is_refused_and_writes_nothing(self):
        raw = self.draft()
        changed = raw.replace("The closing paragraph.", "Closed in Obsidian.")
        (self.folder / "draft.md").write_text(changed, encoding="utf-8")
        with self.assertRaises(E.Conflict):
            E.save_blocks(self.folder, E.digest(raw), BODY[:4] + ["Mine."])
        self.assertEqual(changed, self.draft())
        self.assertEqual([], E.versions(self.folder))

    def test_an_afternoon_of_saves_keeps_a_handful_of_versions_not_one_per_pause(self):
        for n in range(4):
            E.save_blocks(self.folder, E.digest(self.draft()), BODY[:4] + [f"Closed, take {n}."])
        self.assertEqual(1, len(E.versions(self.folder)))
        self.assertIn("take 3", self.draft())

    def test_a_sent_piece_is_left_as_it_is(self):
        (self.folder / "final.md").write_text("sent\n")
        raw = self.draft()
        with self.assertRaises(E.Refused):
            E.save_blocks(self.folder, E.digest(raw), ["Mine."])
        self.assertEqual(raw, self.draft())

    def test_kept_versions_are_not_listed_as_the_piece_files(self):
        E.save_blocks(self.folder, E.digest(self.draft()), BODY + ["One more line."])
        self.assertFalse([f for f in self.gather()["files"] if ".versions" in f])


class Comments(Piece):
    def rounds(self, tid):
        return E.read_rework(self.folder)[tid]

    def test_a_comment_waits_until_it_is_sent(self):
        tid = self.comment()
        self.assertEqual("noted", E.state(self.rounds(tid)))
        self.assertEqual([tid], E.send(self.folder))
        self.assertEqual("asked", E.state(self.rounds(tid)))
        self.assertEqual(DRAFT, self.draft())

    def test_a_comment_can_go_straight_to_the_agent(self):
        tid = self.comment(send=True)
        self.assertEqual("asked", E.state(self.rounds(tid)))

    def test_accepting_changes_only_that_paragraph_and_keeps_the_old_version(self):
        raw = self.draft()
        tid = self.comment(send=True)
        E.propose(self.folder, tid, "Closed, tighter.")
        self.assertEqual(DRAFT, self.draft())            # an agent never touches the draft
        E.accept(self.folder, tid)
        self.assertEqual(BODY[:4] + ["Closed, tighter."], self.texts())
        self.assertEqual(raw, E.versions(self.folder)[0].read_text(encoding="utf-8"))
        self.assertEqual("closed", E.state(self.rounds(tid)))
        self.assertIn("a suggestion was accepted on the board",
                      (self.folder / "SESSION-CONTEXT.md").read_text())

    def test_a_comment_follows_its_words_when_the_paragraph_moves(self):
        tid = self.comment(send=True)
        E.save_blocks(self.folder, E.digest(self.draft()), ["A new first paragraph."] + BODY)
        E.propose(self.folder, tid, "Closed, tighter.")
        E.accept(self.folder, tid)
        self.assertEqual("A new first paragraph.", self.texts()[0])
        self.assertEqual("Closed, tighter.", self.texts()[-1])

    def test_accept_is_refused_when_the_paragraph_changed_since_the_suggestion(self):
        tid = self.comment(send=True)
        E.propose(self.folder, tid, "Closed, tighter.")
        E.save_blocks(self.folder, E.digest(self.draft()), BODY[:4] + ["The closing paragraph, edited."])
        before = self.draft()
        with self.assertRaises(E.Refused):
            E.accept(self.folder, tid)
        self.assertEqual(before, self.draft())

    def test_an_edit_elsewhere_does_not_block_the_accept(self):
        tid = self.comment(send=True)
        E.propose(self.folder, tid, "Closed, tighter.")
        E.save_blocks(self.folder, E.digest(self.draft()), ["The opening, edited."] + BODY[1:])
        E.accept(self.folder, tid)
        self.assertEqual(["The opening, edited."] + BODY[1:4] + ["Closed, tighter."], self.texts())

    def test_the_writer_can_edit_a_suggestion_before_accepting_it(self):
        tid = self.comment(send=True)
        E.propose(self.folder, tid, "Closed, tighter.")
        E.accept(self.folder, tid, "Mine, after all.")
        self.assertEqual("Mine, after all.", self.texts()[-1])
        self.assertEqual("yes", self.rounds(tid)[-1]["fields"]["Edited"])

    def test_a_reply_opens_the_next_round_with_the_writers_words(self):
        tid = self.comment(send=True)
        E.propose(self.folder, tid, "Closed, tighter.")
        E.again(self.folder, tid, "Still too long.")
        rounds = self.rounds(tid)
        self.assertEqual(["noted", "asked", "proposed", "asked"], [r["kind"] for r in rounds])
        self.assertEqual((2, "Still too long."), (rounds[-1]["n"], rounds[-1]["body"]))
        E.propose(self.folder, tid, "Closed.")
        E.accept(self.folder, tid)
        self.assertEqual("Closed.", self.texts()[-1])

    def test_the_writers_words_are_kept_as_written_and_nothing_is_removed(self):
        tid = self.comment(text="First line.\n\nSecond, with: a colon.", own=True)
        E.drop(self.folder, tid)
        rounds = self.rounds(tid)
        self.assertEqual("First line.\n\nSecond, with: a colon.", rounds[0]["body"])
        self.assertEqual("yes", rounds[0]["fields"]["Own wording"])
        self.assertEqual(["noted", "dropped"], [r["kind"] for r in rounds])

    def test_what_is_out_of_turn_is_refused(self):
        with self.assertRaises(E.Refused):
            self.comment(text="   ")
        with self.assertRaises(E.Refused):
            E.comment(self.folder, "x", quote="words that are nowhere in it", block="Not here.")
        tid = self.comment()
        with self.assertRaises(E.Refused):
            E.propose(self.folder, tid, "Before it was sent.")
        E.send(self.folder)
        with self.assertRaises(E.Refused):
            E.accept(self.folder, tid)                 # nothing suggested yet
        E.propose(self.folder, tid, "Closed.")
        with self.assertRaises(E.Refused):
            E.propose(self.folder, tid, "Again.")      # already answered

    def test_a_comment_on_the_whole_draft_replaces_the_body_and_keeps_the_frontmatter(self):
        tid = E.comment(self.folder, "Make it one argument.", is_whole=True, send=True)
        E.propose(self.folder, tid, "One paragraph now.\n\n## A heading\n\nAnd one here.")
        E.accept(self.folder, tid)
        new = self.draft()
        self.assertTrue(new.startswith('---\ntitle: "A working title"'))
        self.assertEqual(["One paragraph now.", "## A heading", "And one here."], self.texts())

    def test_a_sent_piece_takes_no_comments(self):
        (self.folder / "final.md").write_text("sent\n")
        with self.assertRaises(E.Refused):
            self.comment()

    def test_open_comments_keep_the_piece_in_editing_and_say_whose_move_it_is(self):
        r = self.folder / "edits" / "line-edit-report.md"
        r.write_text(LINE)
        past = time.time() - 3600
        os.utime(r, (past, past))
        self.assertEqual("ready", self.gather()["stage"])
        tid = self.comment()
        p = self.gather()
        self.assertEqual("editing", p["stage"])
        self.assertIn("1 comment not sent to your agent yet", p["action"])
        E.send(self.folder)
        p = self.gather()
        self.assertIn("1 comment with your agent", p["action"])
        self.assertEqual("familiar rework watch", p["cmd"])
        E.propose(self.folder, tid, "Closed.")
        self.assertIn("1 suggestion came back for you", self.gather()["action"])


class Findings(Piece):
    def test_all_three_shapes_of_finding_are_read(self):
        dev = E.findings(DEV)
        self.assertEqual(["3a", "3b"], [f["label"] for f in dev])
        self.assertNotIn("4. Line-level", dev[1]["body"])
        line = E.findings(LINE)
        self.assertEqual(["1", "line 7"], [f["label"] for f in line])
        self.assertIn("[line 35]", line[0]["body"])
        self.assertTrue(line[1]["title"].startswith("announcing evidence"))

    def test_dotted_numbers_are_findings_and_bare_numbers_are_not(self):
        text = ("## 3. Critical fixes\n\n### 3.1 The piece contradicts itself\n\nFix it.\n\n"
                "### 3.2 A buried line\n\nMove it.\n\n## 2026 plans\n\nNot a finding.\n")
        got = E.findings(text)
        self.assertEqual(["3.1", "3.2"], [f["label"] for f in got])
        self.assertNotIn("Not a finding", got[1]["body"])

    def test_a_line_block_under_a_numbered_heading_is_that_findings_body(self):
        text = ('## Findings\n\n### 1. Em dash\n\n[line 3] "a thing—another"\n'
                'Issue: em dash\nFix: split it\n\n### 2. Spelling\n\n[line 9] "color"\n'
                'Issue: American spelling\n\n## Summary\n\n[line 1] "not a finding"\n')
        self.assertEqual(["1", "2", "line 1"], [f["label"] for f in E.findings(text)])

    def test_a_finding_keeps_its_key_when_a_later_look_is_added(self):
        before = {f["label"]: f["key"] for f in E.findings(LINE)}
        after = {f["label"]: f["key"] for f in E.findings(
            LINE + "\n## Third look\n\n[line 9] \"another\"\nIssue: spelling\n")}
        self.assertEqual(before, {k: after[k] for k in before})

    def test_a_finding_sits_beside_the_block_it_quotes_or_else_the_line_it_names(self):
        bl = E.blocks(self.draft())[1]
        quoted = {"label": "1", "title": "x",
                  "body": '[line 16] "The opening paragraph, which says the thing."'}
        self.assertEqual(0, E.flag_block(quoted, bl))
        by_line = {"label": "line 17", "title": "x", "body": "no quote here"}
        self.assertEqual(4, E.flag_block(by_line, bl))
        lost = {"label": "2", "title": "x", "body": '"words no longer in the draft at all"'}
        self.assertIsNone(E.flag_block(lost, bl))

    def test_a_finding_sent_to_the_agent_travels_with_the_comment(self):
        (self.folder / "edits" / "line-edit-report.md").write_text(LINE)
        key = E.findings(LINE)[1]["key"]
        flag = E.flag_field(self.folder, "edits/line-edit-report.md", key)
        tid = E.comment(self.folder, "", block="The closing paragraph.", flag=flag, send=True)
        first = E.read_rework(self.folder)[tid][0]
        self.assertEqual("Work this flag in.", first["body"])
        self.assertTrue(first["fields"]["Flag"].startswith("edits/line-edit-report.md"))
        with self.assertRaises(E.Refused):
            E.flag_field(self.folder, "../draft.md", key)


class Options(Piece):
    def setUp(self):
        super().setUp()
        (self.folder / "outline.md").write_text(OUTLINE, encoding="utf-8")
        (self.folder / "SESSION-CONTEXT.md").write_text(LOG.format(name=self.folder.name))

    def test_an_open_set_is_found_and_both_shapes_read(self):
        found = E.open_option_sets(self.folder)
        self.assertEqual([("outline.md", 0, "opening move")],
                         [(f, i, s["title"]) for f, i, s in found])
        bold = E.option_sets(BOLD_OPTIONS)[0]
        self.assertEqual(["A", "B"], [o["letter"] for o in bold["options"]])
        self.assertIn("pressed the wrong button", bold["options"][1]["body"])
        self.assertNotIn("no source", bold["options"][1]["body"])

    def test_a_pick_goes_under_the_options_with_its_reason_and_into_the_log(self):
        E.choose(self.folder, "outline.md", "opening move", 0, "A", "people first")
        text = (self.folder / "outline.md").read_text()
        self.assertIn("Costs: cold\n\nChosen: A\nBecause: people first\n\n## Chosen structure",
                      text)
        self.assertEqual([], E.open_option_sets(self.folder))
        ctx = board.last_context_entry(self.folder)
        self.assertEqual("Pick A or B for the opening.", ctx["Decision gate"])

    def test_a_pick_without_a_reason_or_twice_is_refused(self):
        with self.assertRaises(E.Refused):
            E.choose(self.folder, "outline.md", "opening move", 0, "A", "  ")
        E.choose(self.folder, "outline.md", "opening move", 0, "B", "not given")
        with self.assertRaises(E.Refused):
            E.choose(self.folder, "outline.md", "opening move", 0, "A", "changed my mind")
        with self.assertRaises(E.Refused):
            E.choose(self.folder, "../elsewhere.md", "opening move", 0, "A", "x")


class Answers(Piece):
    def test_an_answer_is_logged_verbatim_and_closes_the_gate(self):
        (self.folder / "SESSION-CONTEXT.md").write_text(LOG.format(name=self.folder.name))
        E.record_answer(self.folder, "B, because the scene is mine")
        ctx = board.last_context_entry(self.folder)
        self.assertTrue(ctx["Decision gate"].startswith("none"))
        log = (self.folder / "SESSION-CONTEXT.md").read_text()
        self.assertIn("Answer: B, because the scene is mine", log)


class TheAgentsSide(Piece):
    """rework.py, pointed at this folder only, so no real piece is read."""

    def setUp(self):
        super().setUp()
        rework.pieces_dirs = lambda: [self.pieces]

    def test_only_sent_comments_are_waiting_and_each_carries_what_is_needed(self):
        self.comment(text="Not sent yet.", quote="The opening paragraph",
                     block="The opening paragraph, which says the thing.")
        tid = self.comment(text="Shorter, please.", send=True)
        [item] = rework.waiting()
        self.assertEqual((tid, "The closing paragraph", "Shorter, please.", "The closing paragraph."),
                         (item["id"], item["quote"], item["asked"], item["text"]))
        self.assertIsNone(item["last_proposal"])

    def test_a_suggestion_handed_back_is_on_the_board_and_nothing_is_waiting(self):
        tid = self.comment(send=True)
        f = Path(self.tmp.name) / "suggestion.md"
        f.write_text("Closed, tighter.\n")
        self.assertEqual(0, rework.cmd_propose(self.folder.name, tid, str(f), "Cut a clause."))
        self.assertEqual([], rework.waiting())
        last = E.read_rework(self.folder)[tid][-1]
        self.assertEqual(("proposed", "Cut a clause."), (last["kind"], last["fields"]["Note"]))

    def test_watch_says_when_something_is_waiting_and_gives_up_when_told(self):
        self.assertEqual(3, rework.cmd_watch(interval=0.01, timeout=0.05))
        self.comment(send=True)
        self.assertEqual(0, rework.cmd_watch(interval=0.01, timeout=1))


class Server(Piece):
    def setUp(self):
        super().setUp()
        self.httpd, self.token = board.make_server([self.pieces], self.pieces / ".board", 7, "")
        self.port = self.httpd.server_port
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.pid = board.safe_name(self.folder.name)
        self.auth = {"X-Familiar-Token": self.token}

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        super().tearDown()

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        data = json.dumps(body).encode() if body is not None else None
        h = {"Content-Type": "application/json"}
        h.update(headers or {})
        conn.request(method, path, body=data, headers=h)
        r = conn.getresponse()
        out = (r.status, r.read().decode())
        conn.close()
        return out

    def test_a_request_addressed_to_another_host_is_refused(self):
        status, _ = self.call("GET", "/", headers={"Host": f"evil.example:{self.port}"})
        self.assertEqual(403, status)
        status, _ = self.call("GET", "/")
        self.assertEqual(200, status)

    def test_a_write_without_the_token_is_refused(self):
        raw = self.draft()
        status, _ = self.call("POST", "/api/save", {"id": self.pid, "base": E.digest(raw),
                                                    "blocks": ["gone"]})
        self.assertEqual(403, status)
        self.assertEqual(raw, self.draft())

    def test_the_piece_page_is_a_document_read_from_disk(self):
        status, page = self.call("GET", f"/{self.pid}.html")
        self.assertEqual(200, status)
        self.assertEqual(5, page.count('<div class="blk" data-src='))
        self.assertIn('class="blk composer"', page)
        self.assertIn("Comment on the Whole Draft", page)
        (self.folder / "draft.md").write_text(DRAFT.replace("closing", "final"))
        _, page = self.call("GET", f"/{self.pid}.html")
        self.assertIn("The final paragraph.", page)

    def test_typing_saves_and_a_stale_save_gets_the_conflict(self):
        raw = self.draft()
        status, body = self.call("POST", "/api/save", {
            "id": self.pid, "base": E.digest(raw), "blocks": BODY[:4] + ["Closed **now**."]},
            self.auth)
        self.assertEqual(200, status, body)
        got = json.loads(body)
        self.assertEqual(E.digest(self.draft()), got["hash"])
        self.assertIn("<strong>now</strong>", got["html"][-1])
        status, body = self.call("POST", "/api/save", {
            "id": self.pid, "base": E.digest(raw), "blocks": ["From a stale page."]}, self.auth)
        self.assertEqual(409, status)
        self.assertTrue(json.loads(body)["conflict"])
        self.assertNotIn("From a stale page.", self.draft())

    def test_a_comment_round_trips_and_the_page_can_tell_it_is_behind(self):
        _, before = self.call("GET", f"/api/version/{self.pid}")
        status, body = self.call("POST", "/api/comment", {
            "id": self.pid, "text": "Shorter.", "quote": "The closing paragraph",
            "block": "The closing paragraph.", "send": True}, self.auth)
        self.assertEqual(200, status, body)
        tid = json.loads(body)["thread"]
        E.propose(self.folder, tid, "Closed.")
        _, after = self.call("GET", f"/api/version/{self.pid}")
        self.assertNotEqual(json.loads(before)["rework"], json.loads(after)["rework"])
        _, page = self.call("GET", f"/{self.pid}.html")
        self.assertIn(f'data-accept="{tid}"', page)
        status, body = self.call("POST", "/api/accept", {"id": self.pid, "thread": tid}, self.auth)
        self.assertEqual(200, status, body)
        self.assertEqual("Closed.", self.texts()[-1])

    def test_a_change_names_a_piece_by_its_board_id_never_a_path(self):
        status, _ = self.call("POST", "/api/answer", {"id": "../../etc", "answer": "x"}, self.auth)
        self.assertEqual(404, status)


class Theme(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "board.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_settings_are_read_and_a_value_that_could_break_the_page_is_not(self):
        self.path.write_text("Scheme: light\nPaper: #f6f4ef\nInk: red;}body{display:none\n"
                             "Font: Jost, sans-serif\n    Accent: #000\n")
        self.assertEqual({"scheme": "light", "paper": "#f6f4ef", "font": "Jost, sans-serif"},
                         board.read_theme(self.path))

    def test_light_keeps_the_page_light_in_dark_mode(self):
        css = board.theme_css({"scheme": "light", "paper": "#f6f4ef"})
        self.assertIn("color-scheme:light", css)
        self.assertIn("--card:#fff", css)
        self.assertNotIn("@media", css)

    def test_system_leaves_dark_mode_to_the_board(self):
        self.assertTrue(board.theme_css({"paper": "#f6f4ef"}).startswith(
            "@media(prefers-color-scheme:light)"))

    def test_a_google_font_is_loaded_only_when_named(self):
        self.path.write_text("Google fonts: Literata, Inter:wght@400;700\nText size: 18px\n"
                             "Font: Literata, Georgia, serif\n")
        theme = board.read_theme(self.path)
        self.assertEqual(["Literata", "Inter:wght@400;700"], theme["google fonts"])
        link = board.fonts_link(theme)
        self.assertIn("family=Literata&family=Inter:wght@400;700&display=swap", link)
        self.assertIn("font-size:18px", board.theme_css(theme))
        self.assertEqual("", board.fonts_link({}))

    def test_a_font_name_that_could_reach_elsewhere_is_ignored(self):
        self.path.write_text('Google fonts: Inter"><script>x</script>\nText size: huge\n')
        self.assertEqual({}, board.read_theme(self.path))

    def test_no_file_changes_nothing(self):
        self.assertEqual({}, board.read_theme(self.path))
        self.assertEqual("", board.theme_css({}))

    def test_the_shipped_template_sets_nothing(self):
        self.assertEqual({}, board.read_theme(ROOT / "knowledge" / "board.md"))


if __name__ == "__main__":
    unittest.main()
