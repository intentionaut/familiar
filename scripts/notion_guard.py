#!/usr/bin/env python3
"""A three-way version guard for a body Notion is the authority for.

Three digests decide what happens to a piece's body:

  agreed   the digest both sides last held (`base` in `.notion-sync.json`,
           the same one push and pull keep)
  notion   the page's body as it was when the operation started
  local    the body the stage proposes

  local changed   Notion changed   outcome
  no              no               no_change
  yes             no               apply_local     write the proposal to Notion
  no              yes              refresh_local   bring Notion's body down
  yes             yes              conflict        write nothing, ask once

If the two bodies are identical the operation is no_change even when both moved.
With no agreed digest yet, only identical bodies are no_change; anything else is
a conflict. Nothing is merged and nothing polls.

Before any PATCH, the page's body and the proposal are kept in `.versions/`,
named by piece ID, source version and operation ID, so a retry finds them and
adds nothing. A small journal beside them (`guard-<piece>-op-<op>.json`) holds
digests and file names only, so an interrupted operation resumes from what it
first saw. After a write the page is read back; only a matching readback records
the new agreed digest. Logs carry IDs and digests, never draft text.

`decide` is pure. `run` does the work and stops, with a reason and no best-effort
continuation, on: a sent piece, an unreadable body, an unavailable version
store, a stale page, a write failure or a readback mismatch.
"""
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board_edit as be  # noqa: E402
import notion_blocks as blocks  # noqa: E402
import notion_draft as nd  # noqa: E402

NO_CHANGE, APPLY_LOCAL, REFRESH_LOCAL, CONFLICT = "no_change", "apply_local", "refresh_local", "conflict"
OUTCOMES = (NO_CHANGE, APPLY_LOCAL, REFRESH_LOCAL, CONFLICT)
GATE_CONFLICT = {"gate": "choose_side", "options": ["keep_notion", "keep_local"]}
PREFIX = "guard"


def decide(agreed, notion_body, local_body, op_id=None):
    """Exactly one of OUTCOMES. Pure: bodies are compared by digest, nothing is read or written.

    `agreed` is the last-agreed digest (None when the sides never agreed). The
    bodies are the canonical text both sides are compared in. `op_id` is accepted
    so a caller can pass the whole operation; it does not change the decision.
    """
    n, l = be.digest(notion_body), be.digest(local_body)
    if n == l:
        return NO_CHANGE
    if agreed is None:
        return CONFLICT
    local_changed, notion_changed = l != agreed, n != agreed
    if local_changed and notion_changed:
        return CONFLICT
    if local_changed:
        return APPLY_LOCAL
    if notion_changed:
        return REFRESH_LOCAL
    return NO_CHANGE


# -- the version store -------------------------------------------------------

def _safe(part):
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", str(part)).strip("-.")
    if not s:
        raise ValueError("an empty ID cannot name a version")
    return s[:80]


def version_name(piece_id, source_version, op_id, side):
    """`guard-<piece>-<source version>-<op>-<notion|local>.md`, stable for a retry."""
    return f"{PREFIX}-{_safe(piece_id)}-{_safe(source_version)}-{_safe(op_id)}-{side}.md"


def journal_name(piece_id, op_id):
    return f"{PREFIX}-{_safe(piece_id)}-op-{_safe(op_id)}.json"


class StoreError(Exception):
    pass


def _replace(path, text):
    tmp = path.with_name(path.name + ".part")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(tmp, path)


def put_version(path, text):
    """Write once, whole or not at all. An existing file must already hold this text."""
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise StoreError(f"{path.name} exists with different content")
        return
    _replace(path, text)


def agreed_digest(folder):
    """The last-agreed digest push and pull keep, or None."""
    return nd.read_state(folder).get("base")


def record_agreed(folder, page_id, digest):
    """Record a new agreed digest and clear an interrupted mark. Call only after a matching readback."""
    nd.write_state(folder, page_id=page_id, base=digest)


def read_journal(folder, piece_id, op_id):
    try:
        return json.loads((Path(folder) / be.VERSIONS / journal_name(piece_id, op_id)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_journal(folder, piece_id, op_id, record):
    _replace(Path(folder) / be.VERSIONS / journal_name(piece_id, op_id),
             json.dumps(record, indent=1, sort_keys=True) + "\n")


# -- the operation -----------------------------------------------------------

def _result(outcome, piece_id, op_id, log, stopped=None, replayed=False, writes=0, **kw):
    return dict(outcome=outcome, stopped=stopped, replayed=replayed, piece_id=piece_id, op_id=op_id,
                writes=writes, log=log, **kw)


def run(folder, piece_id, page, op_id, local_body, source_version=None, write_version=put_version):
    """Guard one body update. Returns a dict with `outcome`, `stopped` (a reason or None) and `log`.

    `page` is a notion_draft.Page (read, append, update, delete). `local_body`
    is the proposed body as markdown, without front matter. `source_version` is
    what was read from Notion at operation start (its last-edited stamp); it
    defaults to a prefix of the body's digest. `write_version(path, text)` is the
    version-store write, replaceable in tests.

    Only apply_local writes to Notion. refresh_local leaves the local write to
    the caller, who then calls record_agreed with the returned `notion` digest.
    """
    folder = Path(folder)
    log = []

    def note(event, **kw):
        log.append(dict(event=event, piece=piece_id, op=op_id, **kw))

    def stop(reason, **kw):
        note("stopped", reason=reason, **kw)
        return _result(None, piece_id, op_id, log, stopped=reason, **kw)

    if (folder / "final.md").exists():
        return stop("sent")
    journal = read_journal(folder, piece_id, op_id)
    try:
        notion_md, tree, _ = nd._notion_body(page)
        new_blocks = blocks.md_to_blocks(local_body)
        local_md = blocks.blocks_to_md(new_blocks)
    except blocks.Unsupported:
        return stop("unreadable")
    except Exception as e:
        return stop("unreadable", error=type(e).__name__)
    agreed = agreed_digest(folder)
    n_dig, l_dig = be.digest(notion_md), be.digest(local_md)
    note("read", agreed=agreed, notion=n_dig, local=l_dig)

    resumed = bool(journal and journal.get("local") == l_dig)
    if resumed:
        # The same operation again: what it first saw decides, not what it left behind.
        if journal["state"] in ("done", "conflict"):
            note("replayed", outcome=journal["outcome"], state=journal["state"])
            return _result(journal["outcome"], piece_id, op_id, log, replayed=True,
                           versions=journal["versions"], agreed=journal.get("agreed_after", journal["agreed"]),
                           gate=journal.get("gate"), notion=journal["notion"], local=l_dig)
        n_dig, source_version, outcome = journal["notion"], journal["source_version"], journal["outcome"]
    else:
        outcome = decide(agreed, notion_md, local_md, op_id)
    note("decided", outcome=outcome)
    if outcome == NO_CHANGE:
        return _result(outcome, piece_id, op_id, log, notion=n_dig, local=l_dig, agreed=agreed)

    source_version = source_version or n_dig[:12]
    names = {side: version_name(piece_id, source_version, op_id, side) for side in ("notion", "local")}
    refs = {side: f"{be.VERSIONS}/{name}" for side, name in names.items()}
    if not resumed:
        try:
            (folder / be.VERSIONS).mkdir(exist_ok=True)
            write_version(folder / be.VERSIONS / names["notion"], notion_md)
            write_version(folder / be.VERSIONS / names["local"], local_md)
        except (OSError, StoreError):
            return stop("version_store")
        note("versions", notion_version=refs["notion"], local_version=refs["local"])
    record = dict(outcome=outcome, piece=piece_id, op=op_id, source_version=source_version, notion=n_dig,
                  local=l_dig, agreed=agreed, versions=refs, state="pending")

    if outcome == CONFLICT:
        _write_journal(folder, piece_id, op_id, dict(record, state="conflict", gate=dict(GATE_CONFLICT)))
        note("conflict", gate=GATE_CONFLICT["gate"])
        return _result(outcome, piece_id, op_id, log, versions=refs, gate=dict(GATE_CONFLICT),
                       agreed=agreed, notion=n_dig, local=l_dig)
    if outcome == REFRESH_LOCAL:
        _write_journal(folder, piece_id, op_id, dict(record, state="done"))
        return _result(outcome, piece_id, op_id, log, versions=refs, agreed=agreed, notion=n_dig, local=l_dig)

    # apply_local: the page must still be what the operation read, unless this is its own retry.
    if not resumed:
        _write_journal(folder, piece_id, op_id, record)
    try:
        live_md, live_tree, _ = nd._notion_body(page)
    except Exception:
        return stop("unreadable")
    if not resumed and be.digest(live_md) != n_dig:
        return stop("stale", live=be.digest(live_md))
    steps = [] if be.digest(live_md) == l_dig else nd.plan(live_tree, new_blocks)
    state = nd.read_state(folder)
    nd.write_state(folder, page_id=state.get("page_id") or page.id, base=agreed, interrupted=True)
    try:
        nd.apply(page, steps)
    except Exception as e:
        return stop("write_failed", error=type(e).__name__)
    writes = sum(1 for s in steps if s[0] != "keep")
    note("written", steps=writes)
    try:
        back_dig = be.digest(nd._notion_body(page)[0])
    except Exception:
        return stop("readback_unreadable")
    if back_dig != l_dig:
        _write_journal(folder, piece_id, op_id, dict(record, state="readback_mismatch", readback=back_dig))
        return stop("readback_mismatch", readback=back_dig, writes=writes)
    record_agreed(folder, page.id, l_dig)
    _write_journal(folder, piece_id, op_id, dict(record, state="done", agreed_after=l_dig))
    note("agreed", agreed=l_dig)
    return _result(outcome, piece_id, op_id, log, versions=refs, writes=writes, agreed=l_dig,
                   notion=n_dig, local=l_dig)
