#!/usr/bin/env python3
"""Every question waiting on you, in one place, answerable in one sitting.

Every stage stops at a gate and asks the writer something. That is the design.
What the design did not account for is what a fortnight of it looks like: nine
pieces, nine folders, nine questions, and answering one of them means opening a
terminal, naming a piece and starting a stage. The questions were visible and
the answering was not, so pieces sat.

This is the other half. It reads the decision gate out of every piece's context
log, prints them as one list, and records an answer against the piece it
belongs to in the same format every stage writes.

    decisions.py                     every open gate, newest first
    decisions.py --piece SLUG        just that one
    decisions.py answer SLUG "..."   record the writer's answer

Recording an answer is not advancing the piece. The next stage still waits to
be asked, because the answer is the writer's and what to do with it is theirs.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board import last_context_entry  # noqa: E402
from paths import pieces_dirs  # noqa: E402

WAITING = ("waiting on the writer", "waiting on you", "blocked")


def pieces():
    """Every piece folder, in date order, newest last."""
    out = []
    for d in pieces_dirs():
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if p.is_dir() and not p.name.startswith((".", "_")):
                out.append(p)
    return out


def open_gates():
    """(piece, gate, status, next stage, when) for everything holding a question.

    A gate is open when the last context entry has one and the piece has not
    been sent. "Decision gate: none" is a stage saying explicitly that it needs
    nothing, which is different from a piece that never wrote one.
    """
    out = []
    for p in pieces():
        if (p / "final.md").is_file():
            continue
        ctx = last_context_entry(p)
        gate = (ctx.get("Decision gate") or "").strip()
        if not gate or gate.lower().startswith(("none", "n/a")):
            continue
        out.append({
            "piece": p,
            "gate": gate,
            "status": ctx.get("Status", ""),
            "next": ctx.get("Next stage", ""),
            "when": ctx.get("when", ""),
            "stage": ctx.get("stage", ""),
        })
    out.sort(key=lambda g: g["when"], reverse=True)
    return out


def wrap(text, width=74, indent="      "):
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(line)
    return f"\n{indent}".join(lines)


def cmd_list(only=None):
    gates = open_gates()
    if only:
        gates = [g for g in gates if only in g["piece"].name]
    if not gates:
        print("\n  Nothing is waiting on you.\n")
        return 0

    print(f"\n  {len(gates)} waiting on you\n")
    for i, g in enumerate(gates, 1):
        waiting = any(w in g["status"].lower() for w in WAITING)
        mark = "*" if waiting else " "
        print(f"  {mark}{i}. {g['piece'].name}   ({g['stage'] or 'no stage'}, {g['when'] or 'undated'})")
        print(f"      {wrap(g['gate'])}")
        if g["next"]:
            print(f"      next: {g['next']}")
        print()
    print("  Answer one:  familiar decisions answer <piece> \"...\"")
    print("  A starred piece is one a stage stopped at and is holding.\n")
    return 0


def cmd_answer(slug, answer):
    """Append the writer's answer to the piece's context log, verbatim.

    Their words, not a summary of them. `learn decisions` reads exactly these
    for the reasoning behind a choice, and a paraphrase is worth nothing to it.
    """
    matches = [p for p in pieces() if slug in p.name and not (p / "final.md").is_file()]
    if not matches:
        print(f"No piece matching '{slug}'.")
        return 1
    if len(matches) > 1:
        print(f"'{slug}' matches {len(matches)} pieces:")
        for p in matches:
            print(f"  {p.name}")
        return 1

    piece = matches[0]
    ctx = last_context_entry(piece)
    gate = (ctx.get("Decision gate") or "").strip()
    log = piece / "SESSION-CONTEXT.md"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = (
        f"\n## {stamp}  decision  {piece.name}\n\n"
        f"Status: answered, waiting on the writer to start the next stage\n"
        f"Files: none\n"
        f"What changed: the open gate was answered. Nothing else was touched and\n"
        f"  no stage was run.\n"
        f"Gate: {gate or '(none recorded)'}\n"
        f"Answer: {answer}\n"
        f"Decision gate: none, until the next stage sets one\n"
        f"Next stage: {ctx.get('Next stage') or 'the writer decides'}\n"
    )
    with open(log, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"\n  Recorded against {piece.name}.")
    if ctx.get("Next stage"):
        print(f"  That piece was waiting on: {ctx['Next stage']}")
    print("  Nothing was run. Start the stage when you want it.\n")
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == "answer":
        if len(args) < 3:
            sys.exit('usage: decisions.py answer <piece> "your answer"')
        return cmd_answer(args[1], " ".join(args[2:]))
    if args and args[0] == "--piece":
        if len(args) < 2:
            sys.exit("usage: decisions.py --piece <slug>")
        return cmd_list(args[1])
    if args:
        sys.exit(__doc__)
    return cmd_list()


if __name__ == "__main__":
    sys.exit(main())
