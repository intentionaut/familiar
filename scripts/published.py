#!/usr/bin/env python3
"""Which pieces went out, under what stable name, at what public address.

    python3 scripts/published.py          # a table: resolved first, then what needs you
    python3 scripts/published.py --json   # the same, for another tool to read

A piece's stable name is its piece ID, the one in its `.piece-id` file, which
the board sync writes into the board's "Piece ID" and which survives a renamed
folder. A piece that has never had one falls back to its folder name. Either
way two pieces with the same title still have two names.
Its public address comes from `final.md`, the record of a send, and from
nowhere else: not a title match, not a board row, not a guess.

Each piece with a `final.md` comes back in one of three states:

  resolved     sent, with a public web_url that no other piece claims
  unresolved   something is missing or unusable; the reason says what
  conflict     two pieces claim the same public address, or carry the same
               piece ID (a copied folder); neither wins

An address inside a publishing tool (an analytics page, an editor, a
dashboard) is where the writer works, not where a reader goes. It is reported
as unresolved and never passed on as the public link.

Nothing here writes: not to a piece, not to a board, not to a platform.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board import frontmatter_span  # noqa: E402
from board_provider import read_piece_id  # noqa: E402
from paths import pieces_dirs  # noqa: E402

# Hosts that are a publishing tool's own back office, never a reader's page.
ADMIN_HOSTS = {"app.beehiiv.com", "dashboard.beehiiv.com",
               "app.buffer.com", "publish.buffer.com", "www.notion.so", "app.notion.com"}
# Path segments that mark a back-office page on any host.
ADMIN_PATHS = {"analytics", "admin", "edit", "dashboard", "settings", "stats"}


def admin_reason(url):
    """Why a URL is not a public page, or None when it may be one."""
    try:
        u = urlparse(url)
    except ValueError:
        return "not a URL"
    if u.scheme not in ("http", "https") or not u.hostname:
        return "not a web address"
    host = u.hostname.lower()
    if host in ADMIN_HOSTS or host in ("localhost", "127.0.0.1"):
        return f"{host} is a working tool, not a public page"
    segments = {s.lower() for s in u.path.split("/") if s}
    if segments & ADMIN_PATHS:
        return f"/{sorted(segments & ADMIN_PATHS)[0]} is a back-office page, not a public one"
    return None


def _normal(url):
    u = urlparse(url)
    return f"{u.hostname.lower().removeprefix('www.')}{u.path.rstrip('/')}"


def read_piece(folder):
    """One piece's record, from its final.md alone."""
    pid = read_piece_id(folder) or None
    rec = {"id": pid or folder.name, "piece_id": pid, "folder_name": folder.name,
           "folder": str(folder), "title": None, "sent": None,
           "platform": None, "public_url": None, "state": "unresolved", "reason": None}
    final = folder / "final.md"
    span, fm = frontmatter_span(final.read_text(errors="replace"))
    if not span:
        rec["reason"] = "final.md has no frontmatter"
        return rec
    rec.update(title=fm.get("title") or None, sent=fm.get("sent") or None,
               platform=fm.get("platform") or None)
    url = (fm.get("web_url") or "").strip()
    if not rec["sent"]:
        rec["reason"] = "final.md does not say when it was sent"
    elif not url:
        rec["reason"] = "final.md has no web_url"
    elif (why := admin_reason(url)):
        rec["reason"] = f"web_url {url}: {why}"
    else:
        rec.update(public_url=url, state="resolved")
    return rec


def published(dirs=None):
    """Every piece with a final.md, across the writer's piece folders."""
    recs = [read_piece(f.parent)
            for d in (dirs or pieces_dirs()) if d.is_dir()
            for f in sorted(d.glob("*/final.md"))]
    claims = {}
    for r in recs:
        if r["public_url"]:
            claims.setdefault(_normal(r["public_url"]), []).append(r)
    for same in claims.values():
        if len(same) > 1:
            for r in same:
                others = ", ".join(o["folder_name"] for o in same if o is not r)
                r.update(state="conflict", reason=f"same public address as {others}")
    ids = {}
    for r in recs:
        ids.setdefault(r["id"], []).append(r)
    for same in ids.values():
        if len(same) > 1:
            for r in same:
                others = ", ".join(o["folder_name"] for o in same if o is not r)
                r.update(state="conflict", reason=f"same piece ID as {others}; one is a copy")
    order = {"resolved": 0, "conflict": 1, "unresolved": 2}
    return sorted(recs, key=lambda r: (order[r["state"]], r["id"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pieces", action="append", help="a piece folder root (repeatable)")
    a = ap.parse_args(argv)
    recs = published([Path(p).expanduser() for p in a.pieces] if a.pieces else None)
    if a.json:
        print(json.dumps(recs, indent=2))
        return 0
    if not recs:
        print("published: no piece has a final.md yet")
        return 0
    for r in recs:
        tail = r["public_url"] if r["state"] == "resolved" else r["reason"]
        print(f"{r['state']:<10} {r['folder_name']:<40} {tail}")
    n = sum(r["state"] == "resolved" for r in recs)
    print(f"\n{n} of {len(recs)} sent pieces have a public address you can link to.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
