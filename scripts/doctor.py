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
OPTIONAL = ["social-schedule.md", "themes.md", "links.md", "reflection.md",
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


def started(piece):
    """Has anything been written into this piece, or is it still the scaffold?

    `new-piece` writes notes.md with empty sections, so a folder made and never
    worked counts as a piece in flight and inflates the one number a writer
    uses to decide whether they have room to start something else. A scaffold
    is headings and nothing under them.
    """
    for name in ("draft.md", "final.md", "brief.md", "source.md", "outline.md"):
        if (piece / name).is_file():
            return True
    notes = piece / "notes.md"
    if not notes.is_file():
        return False
    for line in notes.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "<!--", "-->")):
            return True
    return False


def count_pieces():
    """Count piece folders and surface what's in flight."""
    total = 0
    with_notes = 0
    with_draft = 0
    scaffolds = 0
    for d in pieces_dirs():
        if not d.is_dir():
            continue
        for piece in d.iterdir():
            if not piece.is_dir() or piece.name.startswith(".") or piece.name.startswith("_"):
                continue
            if (piece / "notes.md").is_file():
                if not started(piece):
                    scaffolds += 1
                    continue
                total += 1
                with_notes += 1
                if (piece / "draft.md").is_file() or (piece / "final.md").is_file():
                    with_draft += 1
    return total, with_notes, with_draft, scaffolds


def themes_report(cfg, shipped):
    """One block on declared themes, only when the writer keeps the file.

    Absent or still the template: say nothing. A file nobody has filled is not
    a gap to nag about, per AGENTS.md on setting-gated loops.
    """
    path = cfg / "themes.md"
    st, _ = state(path, shipped)
    if st != OK:
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    body = text.split("\n## Search\n")[0]
    blocks = re.split(r"(?m)^### T\d", body)[1:]
    if not blocks:
        return
    shipped_n = sum(1 for b in blocks if re.search(r"\*\*Pieces shipped:\*\*(?!\s*none)", b))
    unknown_for = sum(1 for b in blocks if re.search(r"\*\*Written for:\*\*[^\n]*unknown", b))
    print(f"  Themes: {len(blocks)} declared")
    if shipped_n:
        print(f"    {shipped_n} with a shipped piece")
    if unknown_for:
        print(f"    {unknown_for} not yet saying who they are written for")
    print()


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
    total, with_notes, with_draft, scaffolds = count_pieces()

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
    if scaffolds:
        word = "folder" if scaffolds == 1 else "folders"
        print(f"    {scaffolds} scaffolded and not started ({word} only)")

    print()

    themes_report(cfg, HOME / "knowledge" / "themes.md")

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
    text = refl.read_text() if refl.is_file() else ""
    setting = re.search(r"^- Reflection:\s*(on|off)\s*$", text, re.M | re.IGNORECASE)
    if setting and setting.group(1).lower() == "on":
        print("  Reflection: on")
    elif setting:
        print("  Reflection: off (edit knowledge/reflection.md to turn on)")
    else:
        # The template reads "[on / off]" and used to be counted as on. It is
        # neither: nobody has chosen. Say what it would do and where it is set,
        # the same way the social schedule line does.
        print("  Reflection: template (turn on in knowledge/reflection.md: two "
              "questions at the end of a stage, your words recorded)")

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
        print("      Ask your agent:  learn ingest <your past writing>")
        print("      It drafts both voice files from evidence, and you accept")
        print("      or reject each section.")
        print("      A folder of files works. So does a Substack, beehiiv or")
        print("      Ghost export: download it, unzip it, and point at that.")
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
