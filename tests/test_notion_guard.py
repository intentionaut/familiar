"""The three-way version guard, against a fake Notion.

Every piece and page is synthetic. Nothing here reaches Notion or reads a real
house. The rules under test:
  - the decision is a truth table over local changed x Notion changed
  - a conflict writes nothing to Notion and records both versions and one gate
  - every replacing write has two readable pre-change versions first
  - retrying an operation adds no versions and no blocks
  - only a matching readback records a new agreed digest
  - logs and the journal carry IDs and digests, never draft text
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_edit as be  # noqa: E402
import notion_blocks as blocks  # noqa: E402
import notion_draft as nd  # noqa: E402
import notion_guard as ng  # noqa: E402
import test_notion_draft as td  # noqa: E402

PID = "piece-abc"
BODY = blocks.canon(nd.split_draft(td.DRAFT)[1])
LOCAL_EDIT = BODY.replace("Opening paragraph.", "Local opening line.")
NOTION_EDIT = "Notion opening line."
SECRETS = ("Local opening line.", NOTION_EDIT, "Closing line.", "Opening paragraph.")


class Guard(td.Base):
    def setUp(self):
        super().setUp()
        self.ids = self.synced()
        self.page = nd.Page(self.prov.client, "page-1")
        self.agreed = be.digest(BODY)

    def run_guard(self, local, op="op-1", **kw):
        return ng.run(self.folder, PID, self.page, op, local, source_version="v1", **kw)

    def versions(self):
        d = self.folder / be.VERSIONS
        return sorted(p.name for p in d.glob("guard-*")) if d.exists() else []

    def assert_no_text(self, res):
        blob = json.dumps(res["log"])
        for f in (self.folder / be.VERSIONS).glob("guard-*.json"):
            blob += f.read_text()
        for s in SECRETS:
            self.assertNotIn(s, blob)


class TruthTable(Guard):
    def scene(self, local_changed, notion_changed):
        if notion_changed:
            self.fake.edit_text(self.ids[0], NOTION_EDIT)
        return LOCAL_EDIT if local_changed else BODY

    def test_decide_covers_all_four_cells(self):
        n2, l2 = "notion changed", "local changed"
        self.assertEqual("no_change", ng.decide(self.agreed, BODY, BODY, "o"))
        self.assertEqual("apply_local", ng.decide(self.agreed, BODY, l2, "o"))
        self.assertEqual("refresh_local", ng.decide(self.agreed, n2, BODY, "o"))
        self.assertEqual("conflict", ng.decide(self.agreed, n2, l2, "o"))

    def test_both_sides_landing_on_the_same_text_is_no_change(self):
        self.assertEqual("no_change", ng.decide(self.agreed, "same", "same"))

    def test_no_agreed_digest_conflicts_unless_the_bodies_match(self):
        self.assertEqual("conflict", ng.decide(None, "a", "b"))
        self.assertEqual("no_change", ng.decide(None, "a", "a"))

    def test_neither_changed(self):
        res = self.run_guard(self.scene(False, False))
        self.assertEqual("no_change", res["outcome"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual([], self.versions())

    def test_local_only_applies_and_reads_back(self):
        res = self.run_guard(self.scene(True, False))
        self.assertEqual("apply_local", res["outcome"])
        self.assertIsNone(res["stopped"])
        self.assertEqual(LOCAL_EDIT, self.fake.md())
        self.assertEqual(be.digest(LOCAL_EDIT), ng.agreed_digest(self.folder))
        self.assertEqual(be.digest(LOCAL_EDIT), res["agreed"])
        self.assertFalse(nd.read_state(self.folder).get("interrupted"))

    def test_apply_keeps_two_readable_versions_first(self):
        self.run_guard(self.scene(True, False))
        names = self.versions()
        self.assertEqual(2, len([n for n in names if n.endswith(".md")]))
        notion_v = self.folder / be.VERSIONS / ng.version_name(PID, "v1", "op-1", "notion")
        local_v = self.folder / be.VERSIONS / ng.version_name(PID, "v1", "op-1", "local")
        self.assertEqual(BODY, notion_v.read_text())
        self.assertEqual(LOCAL_EDIT, local_v.read_text())

    def test_notion_only_refreshes_and_writes_nothing(self):
        res = self.run_guard(self.scene(False, True))
        self.assertEqual("refresh_local", res["outcome"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual(self.agreed, ng.agreed_digest(self.folder), "the caller records it after its own write")
        self.assertEqual(be.digest(self.fake.md()), res["notion"])
        self.assertEqual(2, len([n for n in self.versions() if n.endswith(".md")]))
        self.assertEqual(td.DRAFT, self.draft.read_text(), "the guard never writes draft.md")

    def test_both_changed_is_a_conflict_with_zero_writes_and_one_gate(self):
        res = self.run_guard(self.scene(True, True))
        self.assertEqual("conflict", res["outcome"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual("choose_side", res["gate"]["gate"])
        self.assertEqual({"notion", "local"}, set(res["versions"]))
        for ref in res["versions"].values():
            self.assertTrue((self.folder / ref).read_text())
        self.assertEqual(self.agreed, ng.agreed_digest(self.folder))
        j = ng.read_journal(self.folder, PID, "op-1")
        self.assertEqual(res["versions"], j["versions"])
        self.assertEqual(res["gate"], j["gate"])
        self.assert_no_text(res)


class Retries(Guard):
    def test_a_duplicate_operation_id_adds_no_versions_and_no_blocks(self):
        self.run_guard(LOCAL_EDIT)
        names, ids, mutations = self.versions(), self.fake.ids(), len(self.fake.mutations)
        again = self.run_guard(LOCAL_EDIT)
        self.assertTrue(again["replayed"])
        self.assertEqual("apply_local", again["outcome"])
        self.assertEqual(names, self.versions())
        self.assertEqual(ids, self.fake.ids())
        self.assertEqual(mutations, len(self.fake.mutations))

    def test_a_duplicate_conflict_is_replayed_and_still_writes_nothing(self):
        self.fake.edit_text(self.ids[0], NOTION_EDIT)
        first = self.run_guard(LOCAL_EDIT)
        names = self.versions()
        again = self.run_guard(LOCAL_EDIT)
        self.assertTrue(again["replayed"])
        self.assertEqual(first["versions"], again["versions"])
        self.assertEqual(names, self.versions())
        self.assertEqual([], self.fake.mutations)

    def test_an_interrupted_version_write_stops_before_any_patch_and_a_retry_completes(self):
        calls = []

        def flaky(path, text):
            calls.append(path.name)
            if len(calls) == 2:
                raise OSError("disk full")
            ng.put_version(path, text)

        res = self.run_guard(LOCAL_EDIT, write_version=flaky)
        self.assertEqual("version_store", res["stopped"])
        self.assertIsNone(res["outcome"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual(self.agreed, ng.agreed_digest(self.folder))
        retry = self.run_guard(LOCAL_EDIT)
        self.assertIsNone(retry["stopped"])
        self.assertEqual(2, len([n for n in self.versions() if n.endswith(".md")]))
        self.assertEqual(LOCAL_EDIT, self.fake.md())

    def test_an_unavailable_version_store_stops_with_no_write(self):
        (self.folder / be.VERSIONS).write_text("a file where the folder should be")
        res = self.run_guard(LOCAL_EDIT)
        self.assertEqual("version_store", res["stopped"])
        self.assertEqual([], self.fake.mutations)

    def test_an_interrupted_patch_leaves_the_agreed_digest_and_a_retry_finishes_without_duplicates(self):
        local = LOCAL_EDIT.replace("Closing line.", "A new closing line.\n\nAnd one more.")
        self.fake.fail_after = 1                      # the first step goes through, the second fails
        res = self.run_guard(local)
        self.assertEqual("write_failed", res["stopped"])
        self.assertEqual(self.agreed, ng.agreed_digest(self.folder))
        self.assertTrue(nd.read_state(self.folder)["interrupted"])
        names = self.versions()
        self.fake.fail_after = None
        retry = self.run_guard(local)
        self.assertIsNone(retry["stopped"], retry)
        self.assertEqual("apply_local", retry["outcome"])
        self.assertEqual(blocks.canon(local), self.fake.md())
        self.assertEqual(names, self.versions(), "the retry made no extra versions")
        self.assertEqual(blocks.canon(local).count("A new closing line."), self.fake.md().count("A new closing line."))
        self.assertEqual(be.digest(blocks.canon(local)), ng.agreed_digest(self.folder))
        self.assertFalse(nd.read_state(self.folder).get("interrupted"))


HUMAN_EDIT = "A person rewrote this line."
HUMAN_ADD = "A person added this paragraph."
PARTIAL = LOCAL_EDIT.replace("Closing line.", "A new closing line.\n\nAnd one more.")


class Resumes(Guard):
    """A retry continues only from states the operation's own writes explain."""

    def interrupt(self):
        self.fake.fail_after = 1                      # the first step goes through, the second fails
        res = self.run_guard(PARTIAL)
        self.assertEqual("write_failed", res["stopped"])
        self.fake.fail_after = None
        return len(self.fake.mutations)

    def assert_held(self, retry, before, human):
        self.assertEqual("conflict", retry["outcome"], retry)
        self.assertEqual(before, len(self.fake.mutations), "nothing written after the human edit")
        self.assertEqual("choose_side", retry["gate"]["gate"])
        self.assertIn(human, self.fake.md())
        self.assertEqual({"notion", "local", "live"}, set(retry["versions"]))
        self.assertIn(human, (self.folder / retry["versions"]["live"]).read_text())
        self.assertEqual(BODY, (self.folder / retry["versions"]["notion"]).read_text())
        self.assertEqual(blocks.canon(PARTIAL), (self.folder / retry["versions"]["local"]).read_text())
        self.assertEqual(self.agreed, ng.agreed_digest(self.folder))
        self.assertTrue(nd.read_state(self.folder)["interrupted"])
        self.assertEqual("conflict", ng.read_journal(self.folder, PID, "op-1")["state"])
        blob = json.dumps(retry["log"]) + "".join(
            f.read_text() for f in (self.folder / be.VERSIONS).glob("guard-*.json"))
        for s in SECRETS + (HUMAN_EDIT, HUMAN_ADD):
            self.assertNotIn(s, blob)
        again = self.run_guard(PARTIAL)
        self.assertTrue(again["replayed"])
        self.assertEqual(before, len(self.fake.mutations))

    def test_a_human_edit_to_an_existing_block_after_a_partial_write_holds_the_retry(self):
        before = self.interrupt()
        self.fake.edit_text(self.fake.ids()[-1], HUMAN_EDIT)
        self.assert_held(self.run_guard(PARTIAL), before, HUMAN_EDIT)

    def test_a_human_added_block_after_a_partial_write_holds_the_retry(self):
        before = self.interrupt()
        self.fake.add_after("page-1", self.fake.ids()[0],
                            {"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": HUMAN_ADD}}]}})
        self.assert_held(self.run_guard(PARTIAL), before, HUMAN_ADD)

    def test_a_human_deletion_after_a_partial_write_holds_the_retry(self):
        before = self.interrupt()
        heading = next(b for b in self.fake.body() if b["type"] == "heading_2")
        self.fake.kids["page-1"].remove(heading["id"])
        retry = self.run_guard(PARTIAL)
        self.assertEqual("conflict", retry["outcome"], retry)
        self.assertEqual(before, len(self.fake.mutations))
        self.assertNotIn("## A heading", self.fake.md())

    def test_a_stale_stop_then_a_retry_does_not_overwrite_the_human_edit(self):
        original = self.page.read
        state = {"n": 0}

        def moving():
            state["n"] += 1
            if state["n"] == 2:
                self.fake.edit_text(self.ids[0], HUMAN_EDIT)
            return original()

        self.page.read = moving
        self.assertEqual("stale", self.run_guard(LOCAL_EDIT)["stopped"])
        self.page.read = original
        retry = self.run_guard(LOCAL_EDIT)
        self.assertEqual("conflict", retry["outcome"], retry)
        self.assertEqual([], self.fake.mutations)
        self.assertIn(HUMAN_EDIT, self.fake.md())

    def test_a_timeout_after_an_applied_insert_is_reconciled_without_a_second_append(self):
        fake = self.fake
        original = fake.__call__
        armed = {"on": True}

        class LostReply(type(fake)):
            def __call__(s, method, url, headers, body):
                out = original(method, url, headers, body)
                if armed["on"] and method == "PATCH" and url.endswith("/children"):
                    armed["on"] = False
                    raise TimeoutError("the reply was lost after Notion applied the insert")
                return out

        fake.__class__ = LostReply
        local = BODY.replace("Closing line.", "Closing line.\n\nAn added line.")
        res = self.run_guard(local)
        self.assertEqual("write_failed", res["stopped"])
        self.assertEqual(1, fake.md().count("An added line."), "the insert landed")
        retry = self.run_guard(local)
        self.assertIsNone(retry["stopped"], retry)
        self.assertEqual("apply_local", retry["outcome"])
        self.assertEqual(blocks.canon(local), fake.md())
        self.assertEqual(1, fake.md().count("An added line."))
        self.assertEqual(len(fake.ids()), len(set(fake.ids())))

    def test_a_completed_replay_after_a_later_remote_edit_reports_the_page_moved(self):
        done = self.run_guard(LOCAL_EDIT)
        self.assertEqual("apply_local", done["outcome"])
        mutations = len(self.fake.mutations)
        self.fake.edit_text(self.fake.ids()[0], HUMAN_EDIT)
        again = self.run_guard(LOCAL_EDIT)
        self.assertTrue(again["replayed"])
        self.assertEqual("apply_local", again["outcome"], "the historical outcome is kept")
        self.assertEqual(be.digest(LOCAL_EDIT), again["agreed"], "what was agreed then")
        self.assertTrue(again["page_moved"])
        self.assertEqual(be.digest(self.fake.md()), again["live"])
        self.assertNotEqual(again["agreed"], again["live"])
        self.assertEqual(mutations, len(self.fake.mutations))
        self.assertEqual(be.digest(LOCAL_EDIT), ng.agreed_digest(self.folder))

    def test_a_completed_replay_with_no_later_edit_reports_the_page_unmoved(self):
        self.run_guard(LOCAL_EDIT)
        again = self.run_guard(LOCAL_EDIT)
        self.assertTrue(again["replayed"])
        self.assertFalse(again["page_moved"])
        self.assertEqual(be.digest(LOCAL_EDIT), again["live"])


class Stops(Guard):
    def test_a_mismatched_readback_leaves_the_prior_agreed_digest(self):
        fake = self.fake
        original = fake.__call__

        class Mangle(type(fake)):
            def __call__(s, method, url, headers, body):
                out = original(method, url, headers, body)
                if method == "PATCH" and "/blocks/" in url and s.blocks:
                    for b in s.blocks.values():
                        if b["type"] == "paragraph":
                            b["paragraph"]["rich_text"] = s._read_rich([{"text": {"content": "Mangled by Notion."}}])
                            break
                return out

        fake.__class__ = Mangle
        res = self.run_guard(LOCAL_EDIT)
        self.assertEqual("readback_mismatch", res["stopped"])
        self.assertEqual(self.agreed, ng.agreed_digest(self.folder))
        self.assertTrue(nd.read_state(self.folder)["interrupted"])
        self.assertEqual("readback_mismatch", ng.read_journal(self.folder, PID, "op-1")["state"])
        self.assertEqual(2, len([n for n in self.versions() if n.endswith(".md")]))

    def test_a_sent_piece_is_never_written_or_versioned(self):
        (self.folder / "final.md").write_text("Sent text.\n")
        for local in (LOCAL_EDIT, BODY):
            res = self.run_guard(local)
            self.assertEqual("sent", res["stopped"])
            self.assertIsNone(res["outcome"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual([], self.versions())
        self.assertEqual(td.DRAFT, self.draft.read_text())

    def test_a_page_that_moved_since_the_read_is_stale_and_not_written(self):
        original = self.page.read
        state = {"n": 0}

        def moving():
            state["n"] += 1
            if state["n"] == 2:                       # between the operation's read and its write
                self.fake.edit_text(self.ids[0], NOTION_EDIT)
            return original()

        self.page.read = moving
        res = self.run_guard(LOCAL_EDIT)
        self.assertEqual("stale", res["stopped"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual(self.agreed, ng.agreed_digest(self.folder))

    def test_an_unsupported_page_is_unreadable_and_not_written(self):
        self.fake.blocks[self.ids[0]]["type"] = "synced_block"
        res = self.run_guard(LOCAL_EDIT)
        self.assertEqual("unreadable", res["stopped"])
        self.assertEqual([], self.fake.mutations)

    def test_logs_carry_ids_and_digests_never_text(self):
        res = self.run_guard(LOCAL_EDIT)
        self.assert_no_text(res)
        events = {e["event"] for e in res["log"]}
        self.assertTrue({"read", "decided", "versions", "written", "agreed"} <= events)
        for e in res["log"]:
            self.assertEqual(PID, e["piece"])
            self.assertEqual("op-1", e["op"])


if __name__ == "__main__":
    unittest.main()
