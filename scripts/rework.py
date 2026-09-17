#!/usr/bin/env python3
"""Comments from the board, for the agent that answers them.

On the served board the writer selects words in the draft and comments on
them, in a note or in their own wording, sometimes with an edit-report finding
attached, and sends the comments to an agent. Each waits in the piece's
edits/rework.md until it is answered. This is the agent's side: what has been
sent, and a way to hand a suggestion back. The writer accepts, edits, replies
to or rejects each suggestion on the board. Nothing here writes draft.md.

    rework.py open [--piece SLUG] [--json]      every comment waiting for an agent
    rework.py propose PIECE ID FILE [--note ""] answer one; FILE may be - for stdin
    rework.py watch [--interval N] [--timeout N]  wait until a comment is waiting

watch prints and exits as soon as something is waiting, so an agent can run it
in the background and be woken by it. With --timeout it gives up after that
many seconds and exits 3, saying nothing is waiting.
"""
import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import board_edit as E  # noqa: E402
from paths import pieces_dirs  # noqa: E402


def pieces():
    out = []
    for d in pieces_dirs():
        if d.is_dir():
            out += sorted(p for p in d.iterdir()
                          if p.is_dir() and not p.name.startswith((".", "_")))
    return out


def flag_text(folder, field):
    """The finding a comment carries, in full, so the agent need not go looking."""
    if not field:
        return None
    report, key = [x.strip() for x in field.split("·")[:2]]
    found = {f["key"]: f for f in E.findings(E.read_soft(folder / report))}
    f = found.get(key)
    return {"report": report, "label": f["label"] if f else "",
            "title": f["title"] if f else field, "body": f["body"] if f else ""}


def waiting(only=None):
    """Every comment whose newest round is waiting for an agent."""
    out = []
    for p in pieces():
        if only and only not in p.name:
            continue
        for tid, rounds in E.read_rework(p).items():
            if E.state(rounds) != "asked":
                continue
            ask, first = rounds[-1], rounds[0]["fields"]
            target = E.target_of(E.read_soft(p / "draft.md"), rounds)
            proposed = [r for r in rounds if r["kind"] == "proposed"]
            out.append({
                "piece": str(p), "slug": p.name, "id": tid, "round": ask["n"],
                "whole": first.get("Whole") == "yes",
                "quote": first.get("Quote", ""),
                "own_wording": ask["fields"].get("Own wording") == "yes",
                "asked": ask["body"],
                "flag": flag_text(p, ask["fields"].get("Flag") or first.get("Flag")),
                "last_proposal": proposed[-1]["body"] if proposed else None,
                "text": target["text"] if target else None,
            })
    return out


def indent(text, pad="    "):
    return "\n".join(pad + line if line.strip() else "" for line in text.split("\n"))


def cmd_open(only=None, as_json=False):
    items = waiting(only)
    if as_json:
        print(json.dumps(items, indent=2))
        return 0
    if not items:
        print("Nothing is waiting for an agent.")
        return 0
    for x in items:
        where = "the whole draft" if x["whole"] else "a paragraph"
        print(f"\n{x['slug']}  {x['id']}, round {x['round']}  ·  on {where}")
        print(f"  folder: {x['piece']}")
        if x["quote"]:
            print(f"  the words they selected: “{x['quote']}”")
        print(f"  {'their own wording' if x['own_wording'] else 'what they asked'}:")
        print(indent(x["asked"]))
        if x["flag"]:
            print(f"  finding from {x['flag']['report']}: {x['flag']['label']}. {x['flag']['title']}")
            if x["flag"]["body"]:
                print(indent(x["flag"]["body"]))
        if x["last_proposal"]:
            print("  what was suggested last round, and replied to:")
            print(indent(x["last_proposal"]))
        if x["text"] is None:
            print("  those words are no longer in the draft. Suggest nothing; tell the writer.")
        else:
            print(f"  {where} as it stands, which your suggestion replaces:")
            print(indent(x["text"]))
        print(f"  answer: familiar rework propose {x['slug']} {x['id']} <file>")
    print()
    return 0


def find_piece(slug):
    matches = [p for p in pieces() if p.name == slug] or [p for p in pieces() if slug in p.name]
    if len(matches) != 1:
        sys.exit(f"'{slug}' matches {len(matches)} pieces. Give the folder name.")
    return matches[0]


def cmd_propose(slug, tid, source, note=""):
    folder = find_piece(slug)
    text = sys.stdin.read() if source == "-" else pathlib.Path(source).read_text(encoding="utf-8")
    try:
        E.propose(folder, tid, text, note)
    except E.Refused as exc:
        print(exc)
        return 1
    print(f"Suggested for {folder.name} {tid}. It is on the board now; the writer accepts it, "
          "edits it, replies or rejects it.")
    return 0


def cmd_watch(interval=5, timeout=0):
    start = time.time()
    while True:
        items = waiting()
        if items:
            print(f"rework: {len(items)} waiting")
            for x in items:
                print(f"  {x['slug']} {x['id']}: {x['quote'][:60] or ('the whole draft' if x['whole'] else 'a paragraph')}")
            print("Run `familiar rework open` for what each one needs.")
            return 0
        if timeout and time.time() - start >= timeout:
            print("rework: nothing waiting")
            return 3
        time.sleep(interval)


def main():
    ap = argparse.ArgumentParser(description="Comments from the board.")
    sub = ap.add_subparsers(dest="cmd")
    o = sub.add_parser("open", help="every comment waiting for an agent")
    o.add_argument("--piece", default=None)
    o.add_argument("--json", action="store_true")
    pr = sub.add_parser("propose", help="answer a comment with a suggestion")
    pr.add_argument("piece")
    pr.add_argument("id")
    pr.add_argument("file", help="a file holding the replacement text, or - for stdin")
    pr.add_argument("--note", default="", help="one line for the writer, shown above the suggestion")
    w = sub.add_parser("watch", help="wait until a comment is waiting, then say so")
    w.add_argument("--interval", type=float, default=5)
    w.add_argument("--timeout", type=float, default=0)
    args = ap.parse_args()
    if args.cmd == "propose":
        return cmd_propose(args.piece, args.id, args.file, args.note)
    if args.cmd == "watch":
        return cmd_watch(args.interval, args.timeout)
    if args.cmd == "open":
        return cmd_open(args.piece, args.json)
    return cmd_open()


if __name__ == "__main__":
    sys.exit(main())
