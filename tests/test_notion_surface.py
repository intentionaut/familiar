"""Notion as the editing surface, against a fake Notion.

Every piece and page is synthetic. Nothing here reaches Notion or reads a real
house. The rules under test:
  - off unless the house sets `Editing surface: notion`; off reads and writes nothing
  - begin materialises a working copy tagged with page ID and agreed digest
  - finish applies only through the guard: exact patch, readback, agreed digest
  - both sides changed, an unsupported construct, a sent piece: zero writes
  - an interrupted write is never retried silently
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_edit as be  # noqa: E402
import board_provider as bp  # noqa: E402
import notion_blocks as blocks  # noqa: E402
import notion_draft as nd  # noqa: E402
import notion_guard as ng  # noqa: E402
import notion_surface as ns  # noqa: E402
import test_notion_draft as td  # noqa: E402

BODY = blocks.canon(nd.split_draft(td.DRAFT)[1])
NOTION_EDIT = "Edited in Notion."


class Surface(td.Base):
    house_text = "- Draft copy: on\n- Editing surface: notion\n"

    def setUp(self):
        super().setUp()
        self.ids = self.synced()

    def begin(self):
        return ns.stage_begin([self.root], "gamma", self.house, self.prov)

    def finish(self, **kw):
        return ns.stage_finish([self.root], "gamma", self.house, self.prov, **kw)

    def work(self):
        return ns.read_working(self.folder)

    def stage_writes(self, old, new):
        """What a writing stage does: change the working copy, keeping its tags."""
        tags, body = self.work()
        ns.write_working(self.folder, tags["source_page"], tags["agreed_digest"], tags["source_version"],
                         body.replace(old, new))


class Mode(Surface):
    def test_the_setting_reads_only_an_explicit_notion(self):
        for text, want in (("- Editing surface: notion\n", True), ("- Editing surface: [notion / off]\n", False),
                           ("- Editing surface: off\n", False), ("- Draft copy: on\n", False)):
            (self.house / bp.SETTINGS_FILE).write_text(text)
            self.assertEqual(want, ns.surface_is_notion(self.house), text)

    def test_the_shipped_template_leaves_it_off(self):
        self.assertFalse(ns.surface_is_notion(ROOT / "knowledge"))

    def test_mode_off_reads_nothing_writes_nothing_and_changes_no_file(self):
        (self.house / bp.SETTINGS_FILE).write_text("- Draft copy: on\n")
        self.fake.edit_text(self.ids[0], NOTION_EDIT)
        files, calls = self.files(), len(self.fake.calls)
        for res in (self.begin(), self.finish()):
            self.assertEqual(("skipped", "mode_off", 0), (res["status"], res["reason"], res["writes"]))
        self.assertEqual(files, self.files())
        self.assertEqual(calls, len(self.fake.calls), "not one Notion call")
        self.assertEqual(td.DRAFT, self.draft.read_text())
        self.assertEqual("pulled", self.pull()[0], "pull behaves as before")

    def test_draft_md_is_never_touched_with_the_mode_on(self):
        self.begin()
        self.stage_writes("Opening paragraph.", "Local line.")
        self.finish()
        self.assertEqual(td.DRAFT, self.draft.read_text())


class Flow(Surface):
    def test_begin_writes_a_tagged_working_copy_matching_the_page(self):
        res = self.begin()
        self.assertEqual(("ok", "materialised"), (res["status"], res["reason"]))
        tags, body = self.work()
        self.assertEqual(BODY, body)
        self.assertEqual("page-1", tags["source_page"])
        self.assertEqual(be.digest(BODY), tags["agreed_digest"])
        self.assertTrue(tags["source_version"])
        self.assertEqual([], self.fake.mutations)

    def test_a_notion_only_change_refreshes_the_working_copy(self):
        self.begin()
        self.fake.edit_text(self.ids[0], NOTION_EDIT)
        res = self.begin()
        self.assertEqual("refreshed", res["reason"])
        self.assertEqual(self.fake.md(), self.work()[1])
        self.assertIn(NOTION_EDIT, self.work()[1])
        self.assertEqual(be.digest(self.fake.md()), ng.agreed_digest(self.folder))
        self.assertEqual(be.digest(self.fake.md()), self.work()[0]["agreed_digest"])
        self.assertEqual([], self.fake.mutations)

    def test_local_only_output_gives_an_exact_patch_and_a_matching_readback(self):
        self.begin()
        self.stage_writes("Opening paragraph.", "A better opening.")
        res = self.finish()
        self.assertEqual(("ok", "applied"), (res["status"], res["reason"]))
        self.assertEqual([{"op": "update", "block": self.ids[0]}], res["proposal"])
        self.assertEqual([("PATCH", f"/blocks/{self.ids[0]}")], [(m, p) for m, p, _ in self.fake.mutations])
        self.assertEqual(self.ids, self.fake.ids())
        self.assertEqual(self.work()[1], self.fake.md())
        self.assertEqual(be.digest(self.fake.md()), ng.agreed_digest(self.folder))
        self.assertEqual(ng.agreed_digest(self.folder), self.work()[0]["agreed_digest"])

    def test_the_whole_loop_notion_edit_then_stage_then_guarded_update(self):
        self.begin()
        self.fake.edit_text(self.ids[0], NOTION_EDIT)
        self.begin()
        self.stage_writes("Closing line.", "Closing line, edited by the stage.")
        res = self.finish()
        self.assertEqual("applied", res["reason"])
        self.assertIn(NOTION_EDIT, self.fake.md())
        self.assertIn("edited by the stage", self.fake.md())
        self.assertEqual(self.work()[1], self.fake.md())

    def test_a_stage_that_changes_nothing_writes_nothing(self):
        self.begin()
        res = self.finish()
        self.assertEqual("unchanged", res["reason"])
        self.assertEqual([], self.fake.mutations)

    def test_a_pending_local_change_survives_the_next_begin(self):
        self.begin()
        self.stage_writes("Opening paragraph.", "Pending.")
        self.assertEqual("local_pending", self.begin()["reason"])
        self.assertIn("Pending.", self.work()[1])
        self.assertEqual([], self.fake.mutations, "a stage start never writes to Notion")


class Stops(Surface):
    def test_both_changed_is_one_conflict_and_zero_writes(self):
        self.begin()
        self.stage_writes("Opening paragraph.", "Local.")
        self.fake.edit_text(self.ids[0], NOTION_EDIT)
        before = self.work()
        for res in (self.begin(), self.finish()):
            self.assertEqual(("conflict", "conflict", 0), (res["status"], res["reason"], res["writes"]))
            self.assertEqual("choose_side", res["gate"]["gate"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual(before, self.work(), "neither body was merged or replaced")
        self.assertIn(NOTION_EDIT, self.fake.md())

    def test_an_unsupported_notion_construct_stops_with_zero_writes_and_names_it(self):
        self.begin()
        self.fake.blocks[self.ids[0]]["type"] = "synced_block"
        before = self.work()
        for res in (self.begin(), self.finish()):
            self.assertEqual(("stopped", "unsupported", 0), (res["status"], res["reason"], res["writes"]))
            self.assertIn("synced_block", res["construct"])
            self.assertIn(res["construct"], res["message"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual(before, self.work())

    def test_an_unsupported_construct_in_the_working_copy_is_named_and_not_written(self):
        self.begin()
        self.stage_writes("Opening paragraph.", "#### Too deep")
        res = self.finish()
        self.assertEqual(("stopped", "unsupported", 0), (res["status"], res["reason"], res["writes"]))
        self.assertEqual("a level 4 heading", res["construct"])
        self.assertEqual([], self.fake.mutations)

    def test_the_first_of_several_unsupported_constructs_is_named(self):
        self.begin()
        self.stage_writes("Opening paragraph.", "#### Deep\n\n##### Deeper")
        res = self.finish()
        self.assertEqual(sorted(res["items"])[0], res["construct"])
        self.assertEqual(2, len(res["items"]))

    def test_a_sent_piece_changes_no_working_draft(self):
        self.begin()
        self.stage_writes("Opening paragraph.", "Local.")
        (self.folder / "final.md").write_text("Sent.\n")
        self.fake.edit_text(self.ids[0], NOTION_EDIT)
        before, draft = self.work(), self.draft.read_text()
        for res in (self.begin(), self.finish()):
            self.assertEqual(("stopped", "sent"), (res["status"], res["reason"]))
        self.assertEqual([], self.fake.mutations)
        self.assertEqual(before, self.work())
        self.assertEqual(draft, self.draft.read_text())

    def test_a_missing_piece_id_stops_before_any_read(self):
        (self.folder / bp.ID_FILE).unlink()
        calls = len(self.fake.calls)
        res = self.begin()
        self.assertEqual("missing_id", res["reason"])
        self.assertEqual(calls, len(self.fake.calls))

    def test_a_duplicate_row_stops_with_no_write(self):
        pid = bp.read_piece_id(self.folder)
        self.fake.add(title="Dup", state="writing", extra={"Piece ID": {"rich_text": [{"plain_text": pid}]}})
        res = self.begin()
        self.assertEqual(("stopped", "duplicate_row"), (res["status"], res["reason"]))
        self.assertEqual([], self.fake.mutations)
        self.assertIsNone(self.work())

    def test_a_page_that_moved_after_the_read_is_stale_and_not_written(self):
        self.begin()
        self.stage_writes("Opening paragraph.", "Local.")
        original = nd.Page.read
        state = {"n": 0}

        def moving(page):
            state["n"] += 1
            if state["n"] == 3:                    # after finish's own read, inside the guard
                self.fake.edit_text(self.ids[0], NOTION_EDIT)
            return original(page)

        nd.Page.read = moving
        self.addCleanup(setattr, nd.Page, "read", original)
        res = self.finish()
        self.assertEqual(("stopped", "stale", 0), (res["status"], res["reason"], res["writes"]))
        self.assertEqual([], self.fake.mutations)

    def test_a_mismatched_working_copy_tag_is_refused(self):
        self.begin()
        tags, body = self.work()
        ns.write_working(self.folder, tags["source_page"], "0" * 64, tags["source_version"], body + "\n\nMore.")
        res = self.finish()
        self.assertEqual("tag_mismatch", res["reason"])
        self.assertEqual([], self.fake.mutations)


class Interrupted(Surface):
    LOCAL = ("Opening paragraph.", "A new opening.\n\nAnd one more.")

    def interrupted_run(self):
        self.begin()
        self.stage_writes(*self.LOCAL)
        self.fake.fail_after = 1
        res = self.finish()
        self.assertEqual("write_failed", res["reason"])
        self.fake.fail_after = None
        self.fake.mutations.clear()

    def test_a_rerun_does_not_retry_silently(self):
        self.interrupted_run()
        res = self.finish()
        self.assertEqual(("stopped", "interrupted_write", 0), (res["status"], res["reason"], res["writes"]))
        self.assertIn("did not finish", res["message"])
        self.assertIn("overwrite", res["message"])
        self.assertEqual([], self.fake.mutations)
        self.assertEqual("interrupted_write", self.begin()["reason"], "nor is the page pulled down over it")
        self.assertEqual([], self.fake.mutations)

    def test_resume_reads_live_state_and_never_duplicates_blocks(self):
        self.interrupted_run()
        res = self.finish(resume=True)
        self.assertEqual(("ok", "applied"), (res["status"], res["reason"]))
        self.assertEqual(self.work()[1], self.fake.md())
        self.assertEqual(1, self.fake.md().count("A new opening."))
        self.assertEqual(1, self.fake.md().count("And one more."))
        self.assertEqual(be.digest(self.fake.md()), ng.agreed_digest(self.folder))
        self.assertFalse(nd.read_state(self.folder).get("interrupted"))

    def test_the_result_log_carries_no_draft_text(self):
        self.begin()
        self.stage_writes(*self.LOCAL)
        res = self.finish()
        self.assertNotIn("A new opening", json.dumps(res.get("log", [])))


if __name__ == "__main__":
    unittest.main()
