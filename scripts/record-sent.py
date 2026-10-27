#!/usr/bin/env python3
"""Record that a piece went out, in its final.md frontmatter, for a channel no publication tool reports on.

    python3 scripts/record-sent.py PIECE --platform linkedin --url URL --sent 2026-08-31            # shows the change
    python3 scripts/record-sent.py PIECE --platform linkedin --url URL --sent 2026-08-31 --confirm  # writes it

`pull-final.py` records a send from beehiiv. A post that went out on LinkedIn or Bluesky has no such source, so its
final.md carries no `sent` and `published.py` lists it as unresolved. This writes the three fields `published.py`
reads (`sent`, `platform`, `web_url`) and nothing else. The writer says what went out and where; this never guesses.

Without --confirm it prints the exact lines it would add and writes nothing. With it, the body is untouched, a field
already in the frontmatter is never overwritten (a conflict is refused), the file is replaced whole, and the result is
read back with published.py: if the piece is not then resolved, the original is put back and the exit code is 1.
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board import frontmatter_span  # noqa: E402
from paths import pieces_dirs  # noqa: E402
from published import admin_reason, read_piece  # noqa: E402

FIELDS = ("sent", "platform", "web_url")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2}( UTC)?)?$")


def find(piece):
    p = Path(piece).expanduser()
    if p.is_dir():
        return p
    hits = [d / piece for d in pieces_dirs() if (d / piece).is_dir()]
    if len(hits) != 1:
        raise SystemExit(f"record-sent: {len(hits)} piece folders named {piece!r}; nothing written")
    return hits[0]


def with_fields(text, new):
    """final.md text with `new` lines added to its frontmatter (made if there is none). The body is not touched."""
    lines = [f"{k}: {v}" for k, v in new.items()]
    span, fm = frontmatter_span(text)
    if not span:
        return "---\n" + "\n".join(lines) + "\n---\n" + text
    rows = text.split("\n")
    return "\n".join(rows[:span[1]] + lines + rows[span[1]:])


def body(text):
    span, _ = frontmatter_span(text)
    return "\n".join(text.split("\n")[span[1] + 1:]) if span else text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("piece", help="a piece folder name or path")
    ap.add_argument("--platform", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--sent", required=True, help="YYYY-MM-DD, optionally with HH:MM and UTC")
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args(argv)

    if not DATE.match(a.sent):
        raise SystemExit(f"record-sent: --sent must read YYYY-MM-DD (optionally HH:MM [UTC]), not {a.sent!r}")
    if (why := admin_reason(a.url)):
        raise SystemExit(f"record-sent: {a.url}: {why}")
    folder = find(a.piece)
    final = folder / "final.md"
    if not final.is_file():
        raise SystemExit(f"record-sent: {folder.name} has no final.md; a send needs its text on record first")
    before = final.read_text()
    _, fm = frontmatter_span(before)
    new = {"sent": a.sent, "platform": a.platform, "web_url": a.url}
    held = [k for k in FIELDS if fm.get(k)]
    if held:
        raise SystemExit(f"record-sent: {folder.name} already says {', '.join(held)}; nothing written")
    after = with_fields(before, new)
    print(f"{folder.name}: would add\n" + "\n".join(f"  {k}: {v}" for k, v in new.items()))
    if not a.confirm:
        print("nothing written; add --confirm to write it")
        return 0
    tmp = final.with_name("final.md.tmp")
    tmp.write_text(after)
    os.replace(tmp, final)
    rec = read_piece(folder)
    if rec["state"] != "resolved" or body(final.read_text()) != body(before):
        final.write_text(before)
        print(f"record-sent: read back as {rec['state']} ({rec['reason']}); the original is restored", file=sys.stderr)
        return 1
    print(f"written and read back: resolved, {rec['public_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
