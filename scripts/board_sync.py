#!/usr/bin/env python3
"""The commands that read and write the board through its provider.

  familiar board            show the board (the built-in one opens as it always has;
                            a provider's board is printed)
  familiar board sync <p>   bring one piece's row up to date, after a stage exit
  familiar next [piece]     where a piece is and what it needs next

Two rules hold here.

  A sync never blocks a stage. A failure prints one line saying what happened
  and what to do, and the stage carries on. Nothing is retried in a loop.

  `next` reads and names. It says where the piece is and what it needs, and it
  does not start anything; starting is the stage's own command.

The built-in board is unchanged. With no provider set, `sync` has nothing to
do and says so, and `board` opens the page it always did.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board_provider as bp  # noqa: E402

STATES = ("thinking", "writing", "editing", "ready", "sent")


def find_pieces(dirs, query):
    """Folders whose name is the query or contains it, exact match first."""
    q = (query or "").strip().rstrip("/")
    if not q:
        return []
    direct = Path(q).expanduser()
    if direct.is_dir() and any(direct.parent.resolve() == Path(d).resolve() for d in dirs):
        return [direct]
    folders = [f for d in dirs for f in Path(d).iterdir()
               if f.is_dir() and not f.name.startswith(".")]
    exact = [f for f in folders if f.name == q]
    return exact or sorted((f for f in folders if q.lower() in f.name.lower()), key=lambda f: f.name)


def piece_here(dirs, cwd):
    """The piece folder `cwd` is inside, if any."""
    here = Path(cwd).resolve()
    roots = [Path(d).resolve() for d in dirs]
    for p in [here, *here.parents]:
        if p.parent in roots and not p.name.startswith("."):
            return p
    return None


def sync_piece(dirs, query, knowledge=None, env=None, transport=None, provider=None):
    """(status, message). Never raises: a board that cannot be written is a line, not a stop."""
    try:
        provider = provider or bp.resolve_provider(dirs, knowledge, env=env, transport=transport)
        if isinstance(provider, bp.LocalProvider):
            return "skipped", "No board provider is set, so there is nothing to sync."
        found = find_pieces(dirs, query)
        if not found:
            return "failed", f'No piece matches "{query}". Name its folder, or part of it.'
        if len(found) > 1:
            names = ", ".join(f.name for f in found[:5])
            return "failed", f'"{query}" matches {len(found)} pieces ({names}). Name one.'
        folder = found[0]
        # This is the one moment a piece gets its ID file: it is the piece being worked on.
        bp.ensure_piece_id(folder)
        local = bp.LocalProvider(dirs)
        item = local.item_for(folder)
        dupes = bp.duplicate_ids(local.read_all())
        if item.id in dupes:
            raise bp.BoardConflict(
                f"{len(dupes[item.id])} piece folders carry the ID {item.id}.",
                "One is a copy. Delete the .piece-id file in the copy, and sync again.")
        did = bp.push(provider, item)
        return did, f"{item.title}: {did} on the {provider.name} board."
    except bp.BoardError as e:
        return "failed", str(e)


def show_board(provider):
    """The board as text, grouped by state, with the count from the provider."""
    items = provider.read_all()
    by = {}
    for i in items:
        by.setdefault(i.state or "no state", []).append(i)
    n = len(items)
    lines = [f"board: {provider.name}, {n} piece{'s' if n != 1 else ''}"]
    order = [s for s in STATES if s in by] + sorted(s for s in by if s not in STATES)
    for state in order:
        rows = sorted(by[state], key=lambda i: i.last_activity, reverse=True)
        lines += ["", f"{state} ({len(rows)})"]
        for i in rows:
            lines.append(f"  {i.title or i.id}" + (f" - {i.next_decision}" if i.next_decision else ""))
    return "\n".join(lines)


def _matches(item, query):
    q = query.lower()
    hay = [item.id, item.title, str(item.extra.get("slug", ""))]
    return q in " ".join(hay).lower()


def next_text(provider, query=None, here=None):
    """(exit code, text). Names the piece and what it needs; starts nothing."""
    import board
    items = provider.read_all()
    open_ = [i for i in items if i.state != "sent"]
    if query:
        picked = [i for i in items if _matches(i, query)]
        exact = [i for i in picked if query in (i.id, i.title, i.extra.get("slug"))]
        picked = exact or picked
        if not picked:
            return 1, f'No piece matches "{query}".'
        if len(picked) > 1:
            return 1, f'"{query}" matches {len(picked)} pieces. Name one:\n' + "\n".join(
                f"  {i.extra.get('slug') or i.title or i.id}" for i in picked[:8])
        item = picked[0]
    elif here is not None:
        item = next((i for i in items if here.name in (i.id, i.extra.get("slug"))), None)
        if item is None:
            return 1, "This folder is a piece the board has no row for."
    elif len(open_) == 1:
        item = open_[0]
    elif not open_:
        return 0, "Nothing is open. Every piece is sent."
    else:
        rows = sorted(open_, key=lambda i: i.last_activity, reverse=True)[:8]
        return 1, "More than one piece is open. Name one:\n" + "\n".join(
            f"  {i.extra.get('slug') or i.title or i.id} ({i.state})" for i in rows)
    lines = [f"{item.title or item.id} ({item.state or 'no state'})"]
    if item.next_decision:
        lines.append(f"Next: {item.next_decision}")
    if item.blockers:
        lines.append("In the way: " + "; ".join(item.blockers))
    cmd = board.NEXT_COMMAND.get(item.state, "")
    if cmd:
        lines.append(f"Command: {cmd}")
    return 0, "\n".join(lines)
