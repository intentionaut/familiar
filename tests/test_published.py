"""published.py: a sent piece's stable name and public address, from final.md alone.

It never matches by title, never takes a back-office link as public, and never
lets two pieces share an address quietly.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("published", ROOT / "scripts" / "published.py")
pub = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pub)


def piece(root, name, piece_id=None, **fm):
    folder = root / name
    folder.mkdir(parents=True)
    if piece_id:
        (folder / ".piece-id").write_text(piece_id + "\n")
    if fm.pop("_no_final", False):
        return folder
    head = "".join(f'{k}: "{v}"\n' for k, v in fm.items())
    (folder / "final.md").write_text(f"---\n{head}---\n\nThe body.\n" if fm else "The body, no frontmatter.\n")
    return folder


def by_id(recs):
    return {r["id"]: r for r in recs}


def test_a_sent_piece_resolves_to_its_piece_id_and_web_url(tmp_path):
    piece(tmp_path, "2026-08-30-familiar", piece_id="41c8cfa3f12b", title="Taking a Spell",
          sent="2026-09-01 10:54 UTC", web_url="https://newsletter.intentionaut.com/p/taking-a-spell")
    [r] = pub.published([tmp_path])
    assert (r["id"], r["piece_id"], r["folder_name"], r["state"], r["public_url"]) == (
        "41c8cfa3f12b", "41c8cfa3f12b", "2026-08-30-familiar", "resolved",
        "https://newsletter.intentionaut.com/p/taking-a-spell")


def test_a_piece_without_a_piece_id_is_named_by_its_folder(tmp_path):
    piece(tmp_path, "2026-08-30-familiar", sent="2026-09-01", web_url="https://example.com/p/a")
    [r] = pub.published([tmp_path])
    assert (r["id"], r["piece_id"]) == ("2026-08-30-familiar", None)


def test_a_copied_folder_carrying_the_same_piece_id_is_a_conflict(tmp_path):
    piece(tmp_path, "2026-08-30-familiar", piece_id="41c8cfa3f12b", sent="2026-09-01", web_url="https://example.com/p/a")
    piece(tmp_path, "2026-08-30-familiar-copy", piece_id="41c8cfa3f12b", sent="2026-09-01", web_url="https://example.com/p/b")
    recs = pub.published([tmp_path])
    assert {r["state"] for r in recs} == {"conflict"} and "one is a copy" in recs[0]["reason"]


def test_two_pieces_with_the_same_title_stay_two_pieces(tmp_path):
    piece(tmp_path, "2026-08-01-notes", title="Notes", sent="2026-08-01", web_url="https://example.com/p/notes")
    piece(tmp_path, "2026-09-01-notes", title="Notes", sent="2026-09-01", web_url="https://example.com/p/notes-2")
    recs = by_id(pub.published([tmp_path]))
    assert {k: r["public_url"] for k, r in recs.items()} == {
        "2026-08-01-notes": "https://example.com/p/notes", "2026-09-01-notes": "https://example.com/p/notes-2"}


def test_two_pieces_claiming_one_address_are_a_conflict_not_a_winner(tmp_path):
    piece(tmp_path, "a", sent="2026-09-01", web_url="https://example.com/p/one/")
    piece(tmp_path, "b", sent="2026-09-02", web_url="https://www.example.com/p/one")
    recs = by_id(pub.published([tmp_path]))
    assert {r["state"] for r in recs.values()} == {"conflict"}
    assert "same public address as b" in recs["a"]["reason"]
    assert all(r["public_url"] for r in recs.values())  # kept, so she can see which to fix


def test_a_folder_without_final_md_is_not_a_sent_piece(tmp_path):
    piece(tmp_path, "2026-09-10-draft", _no_final=True)
    assert pub.published([tmp_path]) == []


@pytest.mark.parametrize("fm, reason", [
    ({}, "no frontmatter"),
    ({"title": "T", "web_url": "https://example.com/p/t"}, "does not say when it was sent"),
    ({"title": "T", "sent": "2026-09-01"}, "no web_url"),
    ({"sent": "2026-09-01", "web_url": "https://app.beehiiv.com/posts/abc/analytics"}, "working tool"),
    ({"sent": "2026-09-01", "web_url": "https://newsletter.example.com/p/t/analytics"}, "back-office"),
    ({"sent": "2026-09-01", "web_url": "newsletter.example.com/p/t"}, "not a web address"),
])
def test_unresolved_says_why_and_passes_no_address(tmp_path, fm, reason):
    piece(tmp_path, "p", **fm)
    [r] = pub.published([tmp_path])
    assert r["state"] == "unresolved" and r["public_url"] is None and reason in r["reason"]


@pytest.mark.parametrize("url", [
    "https://newsletter.intentionaut.com/p/taking-a-spell",
    "https://intentionaut.com/writing/editorial-analytics-for-teams",  # the word, not a path segment
    "https://example.substack.com/p/the-admin-trap",
])
def test_public_pages_are_not_mistaken_for_back_office(url):
    assert pub.admin_reason(url) is None


def test_every_piece_root_is_read_and_order_puts_what_needs_her_last(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    piece(one, "b-unresolved", title="x")
    piece(two, "a-resolved", sent="2026-09-01", web_url="https://example.com/p/a")
    assert [r["id"] for r in pub.published([one, two])] == ["a-resolved", "b-unresolved"]


def test_json_output_is_the_records(tmp_path, capsys):
    piece(tmp_path, "p", sent="2026-09-01", web_url="https://example.com/p/p")
    assert pub.main(["--json", "--pieces", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)[0]["id"] == "p"


def test_nothing_is_written(tmp_path):
    folder = piece(tmp_path, "p", sent="2026-09-01", web_url="https://app.beehiiv.com/x/analytics")
    before = {f: f.read_bytes() for f in folder.rglob("*")}
    pub.published([tmp_path])
    assert {f: f.read_bytes() for f in folder.rglob("*")} == before
