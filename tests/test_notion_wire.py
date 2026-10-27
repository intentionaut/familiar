"""The caller for the Notion editing surface and the wider schema map, against fakes.

Every piece and page is synthetic. No test reaches Notion or reads a token from
the environment: the transport is a fake, and a spy sink records every request
the fake is asked to make. The rules under test:
  - dry-run (the default) prints the exact requests and sends no write
  - --apply without the confirm token sends no write
  - --apply with a token from an earlier plan, or a wrong one, sends no write
  - --apply with the token of the current plan sends exactly the planned requests
  - begin never writes to Notion; the schema action is gated the same way
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_provider as bp  # noqa: E402
import notion_wire as nw  # noqa: E402
import test_notion_draft as td  # noqa: E402
import test_notion_schema as tsch  # noqa: E402
import test_notion_surface as tsur  # noqa: E402


def writes(fake):
    return list(fake.mutations)


class Stage(tsur.Surface):
    """A piece in sync with its page, a working copy edited by the stage."""

    def setUp(self):
        super().setUp()
        self.begin()
        self.stage_writes("Opening paragraph.", "Local line.")
        self.fake.mutations.clear()

    def run_wire(self, action="finish", **kw):
        return nw.run(action, [self.root], "gamma", self.house, provider=self.prov, **kw)

    def plan_token(self):
        res = self.run_wire()
        self.assertEqual(0, res["code"], res["text"])
        return res["token"]


class DryRun(Stage):
    def test_default_prints_the_exact_request_and_writes_nothing(self):
        res = self.run_wire()
        self.assertEqual((0, "dry_run"), (res["code"], res["status"]))
        self.assertEqual([], writes(self.fake), "not one write reached Notion")
        self.assertEqual([("PATCH", f"/blocks/{self.ids[0]}")], [(r["method"], r["path"]) for r in res["requests"]])
        self.assertIn("Local line.", json.dumps(res["requests"][0]["body"]))
        self.assertIn(f"PATCH /blocks/{self.ids[0]}", res["text"])
        self.assertIn(res["token"], res["text"])
        self.assertEqual(td.DRAFT, self.draft.read_text())

    def test_default_leaves_every_local_file_alone(self):
        files = self.files()
        self.run_wire()
        self.assertEqual(files, self.files(), "no .versions, no journal: a dry run is read-only")

    def test_the_plan_is_the_same_every_time_so_its_token_is_stable(self):
        self.assertEqual(self.plan_token(), self.plan_token())

    def test_a_dry_run_with_nothing_to_send_plans_no_request(self):
        self.stage_writes("Local line.", "Opening paragraph.")
        res = self.run_wire()
        self.assertEqual([], res["requests"])
        self.assertEqual([], writes(self.fake))

    def test_mode_off_reads_nothing(self):
        (self.house / bp.SETTINGS_FILE).write_text("- Draft copy: on\n")
        n = len(self.fake.calls)
        res = self.run_wire()
        self.assertEqual("skipped", res["status"])
        self.assertEqual(n, len(self.fake.calls))


class Gate(Stage):
    def test_apply_without_a_token_sends_nothing(self):
        res = self.run_wire(apply=True)
        self.assertEqual((1, "refused"), (res["code"], res["status"]))
        self.assertEqual([], writes(self.fake))
        self.assertIn(self.plan_token(), res["text"], "it shows the token to confirm with")

    def test_apply_with_a_wrong_token_sends_nothing(self):
        res = self.run_wire(apply=True, confirm="0" * 12)
        self.assertEqual("refused", res["status"])
        self.assertEqual([], writes(self.fake))

    def test_a_token_alone_is_not_apply(self):
        res = self.run_wire(confirm=self.plan_token())
        self.assertEqual("dry_run", res["status"])
        self.assertEqual([], writes(self.fake))

    def test_a_token_for_an_earlier_plan_is_refused_when_the_plan_moved(self):
        token = self.plan_token()
        self.stage_writes("Local line.", "A different line.")
        res = self.run_wire(apply=True, confirm=token)
        self.assertEqual("refused", res["status"])
        self.assertEqual([], writes(self.fake))

    def test_with_the_gate_open_the_spy_sees_exactly_the_planned_request(self):
        planned = self.run_wire()
        res = self.run_wire(apply=True, confirm=planned["token"])
        self.assertEqual((0, "applied"), (res["code"], res["status"]), res["text"])
        sent = writes(self.fake)
        self.assertEqual([(r["method"], r["path"], r["body"]) for r in planned["requests"]], sent)
        self.assertEqual(1, len(sent))
        self.assertIn("Local line.", self.fake.md())

    def test_the_client_itself_refuses_a_write_when_the_gate_is_shut(self):
        gated = nw.Gated(self.prov.client, "refuse", [])
        with self.assertRaises(nw.WriteRefused):
            gated.request("PATCH", "/blocks/x", {"a": 1}, replay_safe=True)
        with self.assertRaises(nw.WriteRefused):
            gated.request("DELETE", "/blocks/x", replay_safe=True)
        with self.assertRaises(nw.WriteRefused):
            gated.request("POST", "/pages", {}, replay_safe=False)
        self.assertEqual([], writes(self.fake))

    def test_a_query_post_is_a_read_and_passes(self):
        self.assertTrue(nw.is_read("POST", "/data_sources/x/query"))
        self.assertTrue(nw.is_read("GET", "/blocks/x/children?page_size=100"))
        self.assertFalse(nw.is_read("POST", "/pages"))
        self.assertFalse(nw.is_read("PATCH", "/blocks/x"))


class Begin(Stage):
    def test_begin_never_writes_to_notion(self):
        res = self.run_wire("begin", apply=True, confirm="x")
        self.assertEqual("ok", res["status"], res["text"])
        self.assertEqual([], writes(self.fake))


class Spy:
    """Wraps a fake transport and records every request that is not a read."""

    def __init__(self, inner):
        self.inner, self.sink = inner, []

    def __call__(self, method, url, headers, body):
        if method in ("PATCH", "DELETE") or (method == "POST" and not url.endswith("/query")):
            self.sink.append((method, url, body))
        return self.inner(method, url, headers, body)


class Schema(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "pieces"
        self.folder = self.root / "2026-02-01-gamma"
        self.folder.mkdir(parents=True)
        (self.folder / "draft.md").write_text("---\ntitle: Gamma\n---\n\nBody.\n", encoding="utf-8")
        (self.folder / bp.ID_FILE).write_text("pid-gamma\n", encoding="utf-8")
        self.house = Path(self.tmp.name) / "house"
        self.house.mkdir()
        (self.house / bp.SETTINGS_FILE).write_text("- Provider: notion\n", encoding="utf-8")
        self.fake = tsch.FakeNotion()
        # a row whose lifecycle can only differ from the piece's real stage
        self.fake.add("pid-gamma", body_state="sent", lifecycle="05 Live")
        self.spy = Spy(self.fake)
        self.sp = tsch.provider(self.spy)

    def run_wire(self, **kw):
        return nw.run("schema", [self.root], "gamma", self.house, schema=self.sp, **kw)

    def test_dry_run_shows_the_patch_and_sends_nothing(self):
        res = self.run_wire()
        self.assertEqual("dry_run", res["status"], res["text"])
        self.assertEqual([], self.spy.sink)
        self.assertEqual("PATCH", res["requests"][0]["method"])
        self.assertTrue(res["requests"][0]["path"].startswith("/pages/"))
        self.assertNotIn("Piece ID", json.dumps(res["requests"][0]["body"]), "only changed fields are sent")

    def test_apply_without_the_token_sends_nothing(self):
        res = self.run_wire(apply=True)
        self.assertEqual("refused", res["status"])
        self.assertEqual([], self.spy.sink)

    def test_apply_with_a_wrong_token_sends_nothing(self):
        res = self.run_wire(apply=True, confirm="0" * 12)
        self.assertEqual("refused", res["status"])
        self.assertEqual([], self.spy.sink)

    def test_apply_with_the_token_sends_exactly_the_planned_patch(self):
        planned = self.run_wire()
        res = self.run_wire(apply=True, confirm=planned["token"])
        self.assertEqual("applied", res["status"], res["text"])
        self.assertEqual([(r["method"], r["path"], r["body"]) for r in planned["requests"]],
                         [(m, u[len(tsch.nb.API):], json.loads(b)) for m, u, b in self.spy.sink])

    def test_not_notion_is_skipped_and_reads_nothing(self):
        (self.house / bp.SETTINGS_FILE).write_text("- Provider: local\n", encoding="utf-8")
        res = self.run_wire()
        self.assertEqual("skipped", res["status"])
        self.assertEqual([], self.fake.calls)


if __name__ == "__main__":
    unittest.main()
