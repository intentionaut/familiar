#!/usr/bin/env python3
"""What Familiar can see, and what it still needs.

Leads with what works. Mentions what needs filling in only when it matters.
Run it any time:

    python3 scripts/doctor.py
"""
import argparse
import os
import re
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import knowledge_dir, pieces_dirs  # noqa: E402

ESSENTIAL = ["positioning.md", "voice-guide.md"]
# The two are not needed at the same moment, and saying so is the difference
# between one question and thirty-nine. positioning.md is what the interview
# needs to start; voice-guide.md is what the draft needs to sound like you.
# A writer can begin a piece today with the first alone.
NEEDED_TO_START = "positioning.md"
NEEDED_TO_DRAFT = "voice-guide.md"
OPTIONAL = ["social-schedule.md", "links.md", "reflection.md",
            "longform-channels.md", "examples/canonical.md"]
SHIPS_COMPLETE = ["style-rules.md"]

PLACEHOLDER = re.compile(r"\[[^\]\n]{3,}\](?!\()")

OK, TEMPLATE, MISSING = "ready", "still a template", "not there yet"


def short_path(path):
    """A path a person can read. Home becomes ~, and a path under the folder
    they are standing in is shown from there."""
    path = Path(path)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        pass
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def state(path, shipped=None):
    if not path.is_file():
        return MISSING, 0
    text = path.read_text()
    found = set(PLACEHOLDER.findall(text))
    if shipped is not None and shipped.is_file() and shipped.resolve() != path.resolve():
        found &= set(PLACEHOLDER.findall(shipped.read_text()))
    return (TEMPLATE if found else OK), len(found)


def count_pieces():
    """Count piece folders and surface what's in flight."""
    total = 0
    with_notes = 0
    with_draft = 0
    for d in pieces_dirs():
        if not d.is_dir():
            continue
        for piece in d.iterdir():
            if not piece.is_dir() or piece.name.startswith(".") or piece.name.startswith("_"):
                continue
            if (piece / "notes.md").is_file():
                total += 1
                with_notes += 1
                if (piece / "draft.md").is_file() or (piece / "final.md").is_file():
                    with_draft += 1
    return total, with_notes, with_draft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="a knowledge folder to check instead")
    args = ap.parse_args()

    cfg, whose = knowledge_dir(args.config)

    # Check knowledge files
    unfilled = []
    filled = []
    for name in ESSENTIAL:
        st, n = state(cfg / name, HOME / "knowledge" / name)
        if st == OK:
            filled.append(name)
        else:
            unfilled.append((name, n))

    # Check pieces
    total, with_notes, with_draft = count_pieces()

    # --- Output ---
    print()

    blanks_for = dict(unfilled)

    def line(name, when):
        """One file, its state, and the stage it is needed by."""
        if name in filled:
            print(f"    {name}  ready")
            return
        n = blanks_for.get(name)
        count = f", {n} blank{'s' if n != 1 else ''}" if n else ""
        print(f"    {name}  {when}{count}")

    if filled and not unfilled:
        print("  Voice: ready")
        for name in filled:
            print(f"    {name}")
    elif NEEDED_TO_START in filled:
        # The gate that matters is open. Whatever else is still a template can
        # be filled in later, so it is reported as pending rather than missing.
        print("  Voice: ready to interview")
        line(NEEDED_TO_START, "needed to start")
        line(NEEDED_TO_DRAFT, "fill in before the draft sounds like you")
    else:
        print("  Voice: one file to go before you can start")
        line(NEEDED_TO_START, "needed to start")
        line(NEEDED_TO_DRAFT, "not needed yet")

    print()

    if total == 0:
        print("  Pieces: none in flight")
    elif total == 1:
        piece_word = "piece"
        print(f"  Pieces: 1 in flight")
    else:
        print(f"  Pieces: {total} in flight")

    if with_notes and with_draft:
        ready = with_notes - with_draft
        if ready > 0:
            print(f"    {ready} waiting for a draft")
        if with_draft > 0:
            print(f"    {with_draft} drafted")

    print()

    # Social schedule
    sched = cfg / "social-schedule.md"
    if sched.is_file():
        st, _ = state(sched, HOME / "knowledge" / "social-schedule.md")
        if st == OK:
            print("  Social schedule: configured")
        else:
            print("  Social schedule: template (fill in when you want posts)")

    # Reflection
    refl = cfg / "reflection.md"
    if refl.is_file():
        text = refl.read_text()
        on_off = re.search(r"Reflection:\s*\[?(on|off)", text, re.IGNORECASE)
        if on_off and on_off.group(1).lower() == "on":
            print("  Reflection: on")
        else:
            print("  Reflection: off (edit knowledge/reflection.md to turn on)")

    print()

    # What to do next
    if unfilled and NEEDED_TO_START not in filled:
        # One next action, not a reading list. The other template is real work
        # but it is not this moment's work, and putting it here is what makes
        # a first run feel like a form to complete before anything can happen.
        print("  Start here:")
        print()
        print("    Open this and answer what you can:")
        print(f"      {short_path(cfg / NEEDED_TO_START)}")
        print("    Short answers are fine. The name, who reads it, and what it")
        print("    covers is enough to begin; the rest can wait.")
        print()
        print("    Then start a piece:  /familiar-new-piece <slug>")
        print()
        print("    If you have published before, this is the faster way in:")
        print("      Ask your agent:  learn ingest <folder of your past writing>")
        print("      It drafts both voice files from evidence, and you accept")
        print("      or reject each section.")
    elif unfilled:
        print("  To fill in the remaining templates:")
        for name, _ in unfilled:
            print(f"    {cfg / name}")
    else:
        if total == 0:
            print("  Ready. Start with:")
            print("    /familiar-new-piece <slug>")
            print("    or point your agent at a build log:  case-study LOG.md")
        else:
            print("  Ready. Pick up where you left off:")
            print("    /familiar-board")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
