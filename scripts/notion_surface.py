#!/usr/bin/env python3
"""Notion as the editing surface: the page body is the working draft.

Off unless the house says `- Editing surface: notion` in board-provider.md.
Any other value, or none, leaves everything as it was: nothing is read from
Notion, nothing is written, no file is made.

When on, a writing stage brackets its work:

  begin   before the stage: read the page body and its last-edited stamp, and
          write `working.md` in the piece folder, tagged with the source page
          ID, the last-agreed digest and the stamp
  finish  on stage exit: propose the exact block changes, and apply them only
          through notion_guard, which re-reads the page and refuses if it moved

`draft.md` is never touched. Only what notion_blocks carries is converted; its
`Unsupported` refusal is the fidelity result, and it stops the stage with zero
writes and names the first construct. Two changed bodies are never merged.

Every result is a dict with `status` (ok, stopped, conflict or skipped), `reason`,
`writes` and a one-line `message`. Stops: mode off, a sent piece, no stable ID,
a duplicate row, an unsupported construct, a stale page, a conflict, an earlier
write that did not finish, a working copy that no longer matches what was agreed,
a write failure and a readback mismatch.

An earlier write that did not finish leaves `interrupted` in `.notion-sync.json`.
The guard cannot tell a half-finished write from a foreign edit on a retry, so a
stage does not retry silently: it stops and says the page was mid-write and that
a Notion edit made since would be overwritten. `resume=True` is the writer's
answer, and the same output then finishes on the same operation ID, adding no
block twice.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board_edit as be  # noqa: E402
import board_provider as bp  # noqa: E402
import notion_blocks as blocks  # noqa: E402
import notion_board as nb  # noqa: E402
import notion_draft as nd  # noqa: E402
import notion_guard as ng  # noqa: E402

SETTING = "Editing surface"
WORKING = "working.md"


def surface_is_notion(knowledge):
    """True only for an explicit `- Editing surface: notion`. Unset, a template placeholder or anything else is off."""
    return (nb.read_field(knowledge, SETTING) or "").lower() == "notion"


# -- the working copy --------------------------------------------------------

def write_working(folder, page_id, agreed, source_version, body):
    text = (f"---\nsource_page: {page_id}\nagreed_digest: {agreed}\nsource_version: {source_version}\n---\n\n"
            + body.rstrip("\n") + "\n")
    ng._replace(Path(folder) / WORKING, text)


def read_working(folder):
    """(tags, body) for the working copy, or None."""
    f = Path(folder) / WORKING
    if not f.is_file():
        return None
    prefix, body, _ = nd.split_draft(f.read_text(encoding="utf-8"))
    tags = dict(re.findall(r"^(\w+):[ \t]*(.*?)[ \t]*$", prefix, re.M))
    return tags, body


# -- results -----------------------------------------------------------------

def _out(status, reason, message, **kw):
    return dict(status=status, reason=reason, message=message, writes=kw.pop("writes", 0), **kw)


def _skipped(message):
    return _out("skipped", "mode_off", message)


def _guard_stop(res):
    r = res["stopped"]
    msgs = {"sent": "This piece has been sent. Its draft is a record and nothing was changed.",
            "stale": "The page changed after the stage read it. Nothing was written. Begin the stage again.",
            "unreadable": "The page or the working copy could not be read. Nothing was written.",
            "version_store": "The before-versions could not be kept, so nothing was written.",
            "write_failed": "A write to Notion failed part way. The page may hold part of the change.",
            "readback_unreadable": "The page could not be read back after the write. The agreed digest is unchanged.",
            "readback_mismatch": "The page does not match what was written. The agreed digest is unchanged."}
    return _out("stopped", r, msgs.get(r, r), writes=res.get("writes", 0), log=res["log"])


def _unsupported(e, where):
    first = e.items[0] if e.items else "unknown"
    return _out("stopped", "unsupported", f"{where} has content Familiar cannot carry. First: {first}. "
                "Nothing was changed. Change it in place, then run it again.", construct=first, items=e.items)


def _interrupted_message():
    return ("An earlier write to this page did not finish, so it may hold part of a change. "
            "Nothing was written. If someone edited the page since, finishing the write would overwrite that edit. "
            "Look at the page, then finish with resume=True.")


# -- locating the page -------------------------------------------------------

def locate(dirs, query, knowledge, provider):
    """(folder, page_id, source_version), or a stopped result."""
    found = _find(dirs, query)
    if isinstance(found, dict):
        return found
    folder = found
    item_id = bp.read_piece_id(folder)
    if not item_id:
        return _out("stopped", "missing_id", f"{folder.name} has no stable piece ID. Nothing was read or written.")
    try:
        row = provider.read(item_id)
    except bp.BoardConflict as e:
        return _out("stopped", "duplicate_row", f"{e} Nothing was read or written.")
    except bp.BoardError as e:
        return _out("stopped", "board_error", str(e))
    if row is None:
        return _out("stopped", "no_row", f"{folder.name} has no row on the board. Nothing was read or written.")
    return folder, row.extra["page_id"], row.version


def _find(dirs, query):
    import board_sync as bs
    found = bs.find_pieces(dirs, query)
    if len(found) != 1:
        return _out("stopped", "no_piece" if not found else "ambiguous_piece",
                    f'"{query}" matches {len(found)} pieces. Name one.')
    return found[0]


# -- begin -------------------------------------------------------------------

def begin(folder, page, source_version):
    """Read the page and materialise `working.md`. Writes to Notion: never."""
    folder = Path(folder)
    if (folder / "final.md").exists():
        return _out("stopped", "sent", "This piece has been sent. Its draft is a record and nothing was changed.")
    if nd.read_state(folder).get("interrupted"):
        return _out("stopped", "interrupted_write", _interrupted_message())
    try:
        notion_md, _tree, _ = nd._notion_body(page)
    except blocks.Unsupported as e:
        return _unsupported(e, "The Notion page")
    n_dig = be.digest(notion_md)
    have = read_working(folder)
    if have is None:
        # First time on this surface: the page is the authority, so it is what both sides now hold.
        write_working(folder, page.id, n_dig, source_version, notion_md)
        ng.record_agreed(folder, page.id, n_dig)
        return _out("ok", "materialised", "Working copy written from the Notion page.",
                    notion=n_dig, agreed=n_dig, source_version=source_version)
    tags, body = have
    try:
        local_md = blocks.canon(body)
    except blocks.Unsupported as e:
        return _unsupported(e, "The working copy")
    agreed = ng.agreed_digest(folder)
    if tags.get("source_page") != page.id:
        return _out("stopped", "wrong_page", "The working copy came from a different page. Nothing was changed.")
    o = ng.decide(agreed, notion_md, local_md)   # pure: a stage start never writes to Notion
    if o == ng.CONFLICT:
        return _out("conflict", "conflict", "Both the page and the working copy changed since they last agreed. "
                    "Nothing was changed. Keep the page or keep the working copy.",
                    gate=dict(ng.GATE_CONFLICT), notion=n_dig, local=be.digest(local_md))
    if o == ng.REFRESH_LOCAL:
        write_working(folder, page.id, n_dig, source_version, notion_md)
        ng.record_agreed(folder, page.id, n_dig)
        return _out("ok", "refreshed", "Working copy replaced with the Notion page's newer text.",
                    notion=n_dig, agreed=n_dig, source_version=source_version)
    if o == ng.APPLY_LOCAL:
        return _out("ok", "local_pending", "The working copy holds changes not yet sent to Notion; the page is unchanged.",
                    notion=n_dig, agreed=agreed, source_version=tags.get("source_version", source_version))
    return _out("ok", "unchanged", "The working copy already matches the page.", notion=n_dig, agreed=agreed,
                source_version=source_version)


def _piece(folder):
    return bp.read_piece_id(folder) or Path(folder).name


# -- finish ------------------------------------------------------------------

def _steps(steps):
    """The proposal as data: what would change, with no draft text."""
    out = []
    for s in steps:
        if s[0] == "insert":
            out.append({"op": "insert", "blocks": len(s[1])})
        elif s[0] == "keep":
            continue
        else:
            out.append({"op": s[0], "block": s[1]})
    return out


def finish(folder, page, op_id=None, resume=False):
    """Propose the working copy's block changes and apply them through the guard."""
    folder = Path(folder)
    if (folder / "final.md").exists():
        return _out("stopped", "sent", "This piece has been sent. Its draft is a record and nothing was changed.")
    have = read_working(folder)
    if have is None:
        return _out("stopped", "no_working_copy", "There is no working copy to send. Begin the stage first.")
    tags, body = have
    if tags.get("source_page") != page.id:
        return _out("stopped", "wrong_page", "The working copy came from a different page. Nothing was changed.")
    if tags.get("agreed_digest") != ng.agreed_digest(folder):
        return _out("stopped", "tag_mismatch", "The working copy was made against a version the page and Familiar "
                    "no longer agree on. Nothing was written. Begin the stage again.")
    state = nd.read_state(folder)
    if state.get("interrupted") and not resume:
        return _out("stopped", "interrupted_write", _interrupted_message())
    try:
        new_blocks = blocks.md_to_blocks(body)
        local_md = blocks.blocks_to_md(new_blocks)
    except blocks.Unsupported as e:
        return _unsupported(e, "The working copy")
    try:
        _, tree, _ = nd._notion_body(page)
    except blocks.Unsupported as e:
        return _unsupported(e, "The Notion page")
    except Exception:
        return _out("stopped", "unreadable", "The page could not be read. Nothing was written.")
    proposal = _steps(nd.plan(tree, new_blocks))
    op = op_id or f"stage-{be.digest(local_md)[:12]}-{str(tags.get('source_version', ''))[:24]}"
    res = ng.run(folder, _piece(folder), page, op, local_md, source_version=tags.get("source_version") or None)
    if res["stopped"]:
        out = _guard_stop(res)
        out["proposal"] = proposal
        return out
    o = res["outcome"]
    if o == ng.CONFLICT:
        return _out("conflict", "conflict", "Both the page and the working copy changed since they last agreed. "
                    "Nothing was written. Keep the page or keep the working copy.",
                    gate=res["gate"], versions=res["versions"], proposal=proposal)
    if o == ng.REFRESH_LOCAL:
        write_working(folder, page.id, res["notion"], tags.get("source_version", ""),
                      blocks.blocks_to_md(page.read()))
        ng.record_agreed(folder, page.id, res["notion"])
        return _out("ok", "refreshed", "The stage changed nothing and the page moved; working copy refreshed.",
                    versions=res["versions"])
    if o == ng.APPLY_LOCAL:
        write_working(folder, page.id, res["agreed"], tags.get("source_version", ""), local_md)
        return _out("ok", "applied", "Notion updated and read back; the agreed digest is recorded.",
                    writes=res["writes"], agreed=res["agreed"], proposal=proposal, replayed=res["replayed"],
                    versions=res["versions"])
    return _out("ok", "unchanged", "The stage changed nothing.", agreed=res["agreed"])


# -- the stage's entry points ------------------------------------------------

def stage_begin(dirs, query, knowledge, provider):
    if not surface_is_notion(knowledge):
        return _skipped("Editing surface is not notion. Nothing was read or written.")
    loc = locate(dirs, query, knowledge, provider)
    if isinstance(loc, dict):
        return loc
    folder, page_id, version = loc
    return begin(folder, nd.Page(provider.client, page_id), version)


def stage_finish(dirs, query, knowledge, provider, resume=False):
    if not surface_is_notion(knowledge):
        return _skipped("Editing surface is not notion. Nothing was read or written.")
    loc = locate(dirs, query, knowledge, provider)
    if isinstance(loc, dict):
        return loc
    folder, page_id, _ = loc
    return finish(folder, nd.Page(provider.client, page_id), resume=resume)
