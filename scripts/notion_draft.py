#!/usr/bin/env python3
"""A draft, copied to a Notion page and back.

  familiar push <piece>    draft.md to the piece's Notion page
  familiar pull <piece>    the page's text back into draft.md

The two sides take turns. A push or a pull only goes ahead when exactly one side
has changed since the last time they agreed, and it stops, changing nothing, when
both have. Nothing is merged.

  base      the hash of the draft as both sides last held it, kept in
            `.notion-sync.json` in the piece folder
  push      refused when the page has edits that were never pulled
  pull      refused when draft.md has edits that were never pushed
  --force   the writer's answer to "both changed": one side wins. What it
            replaces is kept first in `.versions/`, so nothing is lost

Before draft.md is replaced, its text is kept in `.versions/`. A sent piece's
draft is never written, because `learn diff` reads it. Front matter stays in
draft.md and never leaves; a pull replaces the body only.

A page is edited in place: blocks that did not change are not touched, so the
comment threads on them stay where they are. A block removed from the page goes
to Notion's trash, which Notion keeps.

Off unless the house says `- Draft copy: on` in board-provider.md.
"""
import datetime
import difflib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board_edit as be  # noqa: E402
import board_provider as bp  # noqa: E402
import board_sync as bs  # noqa: E402
import notion_blocks as blocks  # noqa: E402
import notion_board as nb  # noqa: E402

STATE_FILE = ".notion-sync.json"
NOTION_VERSIONS = "notion"          # kept as .versions/notion-<stamp>.md
IN_PLACE = {"paragraph", "heading_1", "heading_2", "heading_3", "quote", "code",
            "to_do", "bulleted_list_item", "numbered_list_item"}


# -- the page ----------------------------------------------------------------

class Page:
    """One Notion page's body, as blocks."""

    def __init__(self, client, page_id):
        self.client, self.id = client, page_id

    def read(self):
        return self._list(self.id)

    def _list(self, block_id):
        out, cursor = [], None
        while True:
            q = f"?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
            res = self.client.request("GET", f"/blocks/{block_id}/children{q}")
            for b in res.get("results", []):
                if b.get("has_children"):
                    b["children"] = self._list(b["id"])
                out.append(b)
            if not res.get("has_more"):
                return out
            cursor = res.get("next_cursor")

    def append(self, children, after=None):
        """Insert after a block (the start when None). Returns the new blocks' IDs."""
        made, anchor = [], after
        for i in range(0, len(children), 100):
            position = {"type": "after_block", "after_block": {"id": anchor}} if anchor else {"type": "start"}
            res = self.client.request("PATCH", f"/blocks/{self.id}/children",
                                      {"children": children[i:i + 100], "position": position})
            ids = [b["id"] for b in res.get("results", [])]
            made += ids
            anchor = ids[-1] if ids else anchor
        return made

    def update(self, block_id, new):
        t = new["type"]
        body = {"rich_text": new[t].get("rich_text", [])}
        if t == "code":
            body["language"] = new[t].get("language", "plain text")
            body["caption"] = new[t].get("caption", [])
        if t == "to_do":
            body["checked"] = bool(new[t].get("checked"))
        self.client.request("PATCH", f"/blocks/{block_id}", {t: body})

    def delete(self, block_id):
        self.client.request("DELETE", f"/blocks/{block_id}")


def _has_kids(b):
    return bool(blocks._children(b))


def _updatable(old, new):
    t = old["type"]
    return t == new["type"] and t in IN_PLACE and not _has_kids(old) and not _has_kids(new)


def plan(old, new):
    """The steps that turn the page's blocks into the draft's, touching only what differs.

    keep, update (in place), insert (after the previous block), delete.
    """
    old_sigs = [blocks.signature(b) for b in old]
    new_sigs = [blocks.signature(b) for b in new]
    steps = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_sigs, new_sigs, autojunk=False).get_opcodes():
        if tag == "equal":
            steps += [("keep", old[i]["id"]) for i in range(i1, i2)]
        elif tag == "delete":
            steps += [("delete", old[i]["id"]) for i in range(i1, i2)]
        elif tag == "insert":
            steps.append(("insert", new[j1:j2]))
        else:
            for k in range(max(i2 - i1, j2 - j1)):
                o = old[i1 + k] if i1 + k < i2 else None
                n = new[j1 + k] if j1 + k < j2 else None
                if o and n and _updatable(o, n):
                    steps.append(("update", o["id"], n))
                else:
                    if n:
                        steps.append(("insert", [n]))
                    if o:
                        steps.append(("delete", o["id"]))
    return steps


def summary(steps):
    c = {"kept": 0, "updated": 0, "added": 0, "removed": 0}
    for s in steps:
        if s[0] == "keep":
            c["kept"] += 1
        elif s[0] == "update":
            c["updated"] += 1
        elif s[0] == "insert":
            c["added"] += len(s[1])
        else:
            c["removed"] += 1
    return c


def apply(page, steps):
    anchor = None
    for s in steps:
        if s[0] in ("keep",):
            anchor = s[1]
        elif s[0] == "update":
            page.update(s[1], s[2])
            anchor = s[1]
        elif s[0] == "insert":
            ids = page.append(s[1], anchor)
            anchor = ids[-1] if ids else anchor
        else:
            page.delete(s[1])


# -- the draft ---------------------------------------------------------------

def split_draft(text):
    """(prefix, body, tail): the front matter and the gap after it, the body, and its final newline."""
    import board
    span, _ = board.frontmatter_span(text)
    if span:
        lines = text.split("\n")
        rest = lines[span[1] + 1:]
        gap = 0
        while gap < len(rest) and not rest[gap].strip():
            gap += 1
        prefix = "\n".join(lines[:span[1] + 1]) + "\n" + "\n" * gap
        body = "\n".join(rest[gap:])
    else:
        prefix, body = "", text
    tail = "\n" if body.endswith("\n") else ""
    return prefix, body.rstrip("\n"), tail


def read_state(folder):
    f = Path(folder) / STATE_FILE
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_state(folder, **kw):
    f = Path(folder) / STATE_FILE
    f.write_text(json.dumps(kw, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def stamp():
    return datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")


def keep_notion_copy(folder, text):
    d = Path(folder) / be.VERSIONS
    d.mkdir(exist_ok=True)
    dest = d / f"{NOTION_VERSIONS}-{stamp()}.md"
    n = 2
    while dest.exists():
        dest = d / f"{NOTION_VERSIONS}-{stamp()}-{n}.md"
        n += 1
    dest.write_text(text, encoding="utf-8")
    return dest


def draft_copy_on(knowledge):
    return (nb.read_field(knowledge, "Draft copy") or "").lower() == "on"


# -- push and pull -----------------------------------------------------------

def _setup(dirs, query, knowledge, env, transport, provider):
    """(provider, folder) or (None, (status, message))."""
    try:
        if knowledge is None:
            import paths
            knowledge, _ = paths.knowledge_dir()
        provider = provider or bp.resolve_provider(dirs, knowledge, env=env, transport=transport)
    except bp.BoardError as e:
        return None, ("failed", str(e))
    if not isinstance(provider, nb.NotionProvider):
        return None, ("skipped", "Draft copy needs a Notion board provider, and none is set.")
    if not draft_copy_on(knowledge):
        return None, ("skipped", "Draft copy is off. Set Draft copy to on in board-provider.md to use it.")
    found = bs.find_pieces(dirs, query)
    if not found:
        return None, ("failed", f'No piece matches "{query}". Name its folder, or part of it.')
    if len(found) > 1:
        return None, ("failed", f'"{query}" matches {len(found)} pieces ({", ".join(f.name for f in found[:5])}). Name one.')
    return provider, found[0]


def _read_local(folder):
    raw = be.read_exact(folder / "draft.md")
    if not raw.strip():
        return None
    return raw, *split_draft(raw)


def _notion_body(page):
    """(canonical markdown, blocks, notes) for the page as it is now."""
    tree = page.read()
    notes = {}
    return blocks.blocks_to_md(tree, notes), tree, notes


def _refuse_unsupported(e, where):
    return "failed", (f"{where} has content Familiar cannot carry: {e}. "
                      "Nothing was changed. Change it in place, then run it again.")


def push(dirs, query, knowledge=None, env=None, transport=None, provider=None, check=False, force=False):
    """(status, message). Copies draft.md to the piece's page when Notion has nothing newer."""
    provider, folder = _setup(dirs, query, knowledge, env, transport, provider)
    if provider is None:
        return folder
    try:
        local = _read_local(folder)
        if local is None:
            return "failed", f"{folder.name} has no draft.md to copy."
        raw, prefix, body, tail = local
        try:
            new_blocks = blocks.md_to_blocks(body)
            canon_local = blocks.blocks_to_md(new_blocks)
        except blocks.Unsupported as e:
            return _refuse_unsupported(e, "The draft")
        state = read_state(folder)
        item_id = bp.read_piece_id(folder)
        row = provider.read(item_id) if item_id else None
        if row is None:
            if check:
                return "check", f"Would add the piece to the board, then copy {len(new_blocks)} blocks."
            status, message = bs.sync_piece(dirs, folder.name, provider=provider)
            if status == "failed":
                return status, message
            row = provider.read(bp.read_piece_id(folder))
        page = Page(provider.client, row.extra["page_id"])
        try:
            notion_md, tree, _ = _notion_body(page)
        except blocks.Unsupported as e:
            return _refuse_unsupported(e, "The Notion page")
        base = state.get("base")
        if base is None and tree:
            return "failed", ("The Notion page already has content Familiar did not put there. "
                              "Nothing was changed. Empty the page, or use a new row.")
        changed_in_notion = base is not None and be.digest(notion_md) != base and not state.get("interrupted")
        if changed_in_notion and not force:
            return "failed", ("The Notion page has edits that were never pulled. Nothing was changed. "
                              f"Pull them first with `familiar pull {folder.name}`, or replace the page with "
                              "`--force` (the page's text is kept in .versions/ first).")
        if canon_local == notion_md and not state.get("interrupted"):
            if not check:
                write_state(folder, page_id=page.id, base=be.digest(canon_local))
            return "unchanged", f"{folder.name}: the Notion page already matches draft.md."
        steps = plan(tree, new_blocks)
        c = summary(steps)
        text = (f"{c['updated']} updated, {c['added']} added, {c['removed']} removed, "
                f"{c['kept']} unchanged")
        if check:
            return "check", f"Would copy to Notion: {text}."
        kept = None
        if tree and (changed_in_notion or state.get("interrupted")):
            kept = keep_notion_copy(folder, notion_md)
        write_state(folder, page_id=page.id, base=state.get("base") or be.digest(canon_local),
                    interrupted=True)                 # cleared below, once every step has gone through
        apply(page, steps)
        write_state(folder, page_id=page.id, base=be.digest(canon_local))
        return "pushed", (f"{folder.name}: copied to Notion ({text})."
                          + (f" The page's earlier text is in {kept.relative_to(folder)}." if kept else ""))
    except bp.BoardError as e:
        return "failed", str(e)


def pull(dirs, query, knowledge=None, env=None, transport=None, provider=None, check=False, force=False):
    """(status, message). Brings the page's text into draft.md when draft.md has nothing newer."""
    provider, folder = _setup(dirs, query, knowledge, env, transport, provider)
    if provider is None:
        return folder
    try:
        if (folder / "final.md").exists():
            return "failed", (f"{folder.name} has been sent. draft.md is what learn diff compares with what "
                              "went out, so a pull leaves it as it is.")
        local = _read_local(folder)
        if local is None:
            return "failed", f"{folder.name} has no draft.md. Push first."
        raw, prefix, body, tail = local
        state = read_state(folder)
        if not state.get("base") or not state.get("page_id"):
            return "failed", f"Nothing has been pushed for {folder.name}. Push it first: `familiar push {folder.name}`."
        if state.get("interrupted"):
            return "failed", (f"The last push for {folder.name} did not finish, so the page holds part of it. "
                              f"Nothing was changed. Push again: `familiar push {folder.name}`.")
        try:
            canon_local = blocks.canon(body)
        except blocks.Unsupported as e:
            return _refuse_unsupported(e, "The draft")
        page = Page(provider.client, state["page_id"])
        try:
            notion_md, tree, notes = _notion_body(page)
        except blocks.Unsupported as e:
            return _refuse_unsupported(e, "The Notion page")
        local_changed = be.digest(canon_local) != state["base"]
        notion_changed = be.digest(notion_md) != state["base"]
        if local_changed and notion_changed and not force:
            return "failed", (f"Both draft.md and the Notion page changed since the last sync. Nothing was changed. "
                              f"draft.md is {blocks.words(canon_local)} words and the page is {blocks.words(notion_md)}. "
                              f"Keep the page with `familiar pull {folder.name} --force` (draft.md is kept in "
                              f".versions/ first), or keep draft.md with `familiar push {folder.name} --force`.")
        if local_changed and not notion_changed:
            return "unchanged", (f"{folder.name}: only draft.md changed. There is nothing to pull; "
                                 f"push it with `familiar push {folder.name}`.")
        if not notion_changed:
            return "unchanged", f"{folder.name}: the Notion page has no edits since the last sync."
        if not notion_md.strip() and body.strip():
            return "failed", ("The Notion page is empty, and an empty page does not replace a draft. "
                              "Nothing was changed.")
        drop = ", ".join(f"{k} x{v}" for k, v in sorted(notes.items()))
        delta = blocks.words(notion_md) - blocks.words(canon_local)
        if check:
            return "check", (f"Would replace the draft body with the page's text ({delta:+d} words)."
                             + (f" Formatting with no markdown form would be dropped: {drop}." if drop else ""))
        new_full = prefix + notion_md + tail
        try:
            result = be.save_draft(folder, be.digest(raw), new_full)
        except be.Refused as e:
            return "failed", str(e)
        except be.Conflict:
            return "failed", "draft.md changed while the pull was running. Nothing was changed. Run it again."
        write_state(folder, page_id=page.id, base=be.digest(notion_md))
        kept = result.get("kept")
        return "pulled", (f"{folder.name}: draft.md now matches the Notion page ({delta:+d} words)."
                          + (f" The earlier draft is in {kept.relative_to(folder)}." if kept else "")
                          + (f" Dropped formatting with no markdown form: {drop}." if drop else ""))
    except bp.BoardError as e:
        return "failed", str(e)
