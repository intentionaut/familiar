#!/usr/bin/env python3
"""What Familiar can see, and what it still needs.

Honest about three states and never nags: ready, still a template, or absent.
Absent optional things are fine and are reported calmly. Run it any time:

    python3 scripts/doctor.py
"""
import argparse
import os
import re
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent

# The two Familiar cannot do good work without.
ESSENTIAL = ["positioning.md", "voice-guide.md"]
# Useful, and fine to leave until you need them.
OPTIONAL = ["social-schedule.md", "links.md", "reflection.md",
            "longform-channels.md", "examples/canonical.md"]
# Ships usable. Its bracketed text is report format, not blanks to fill, so
# checking it for placeholders reports a false alarm on a complete file.
SHIPS_COMPLETE = ["style-rules.md"]

PLACEHOLDER = re.compile(r"\[[^\]\n]{3,}\](?!\()")

OK, TEMPLATE, MISSING = "ready", "still a template", "not there yet"


def config_dir(explicit=None):
    """Familiar's config resolution order. A host is one location, not the one."""
    shipped = (HOME / "knowledge").resolve()
    for c in (explicit, os.environ.get("FAMILIAR_CONFIG"),
              "./knowledge", os.path.expanduser("~/.familiar/knowledge")):
        if c and (Path(c) / "positioning.md").is_file():
            found = Path(c).resolve()
            # Resolving to the repo's own folder means these are the shipped
            # templates, however we arrived at them. Say so rather than
            # calling them the writer's.
            return found, ("the shipped templates" if found == shipped else "yours")
    return shipped, "the shipped templates"


def state(path, shipped=None):
    """Filled, still a template, or absent.

    A bracket is only a blank if the shipped template has the same one. The
    writer's own prose contains brackets too: a voice guide that bans "as a
    [senior title]" framing is finished, not unfilled, and counting that as a
    blank tells a writer their voice guide is empty when it is not.
    """
    if not path.is_file():
        return MISSING, 0
    text = path.read_text()
    found = set(PLACEHOLDER.findall(text))
    if shipped is not None and shipped.is_file() and shipped.resolve() != path.resolve():
        found &= set(PLACEHOLDER.findall(shipped.read_text()))
    return (TEMPLATE if found else OK), len(found)


def commands_installed():
    found = {}
    for label, d in (("Claude Code", Path.home() / ".claude/commands"),
                     ("opencode", Path.home() / ".config/opencode/command")):
        found[label] = len(list(d.glob("familiar-*.md"))) if d.is_dir() else 0
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="a knowledge folder to check instead")
    args = ap.parse_args()

    cfg, whose = config_dir(args.config)
    print(f"Familiar   {HOME}")
    print(f"Config     {cfg}  ({whose})")

    adapters = len(list((HOME / ".claude" / "commands").glob("*.md")))
    inst = commands_installed()
    where = ", ".join(f"{k} {v}" for k, v in inst.items())
    print(f"Stages     {adapters} available   Installed: {where}")
    stale = [k for k, v in inst.items() if 0 < v < adapters]
    if stale:
        who = " and ".join(stale)
        verb = "is" if len(stale) == 1 else "are"
        print(f"           {who} {verb} behind. Run scripts/setup.sh to pick up "
              f"the newer stages.")
    print()

    unfilled = []
    for name in ESSENTIAL:
        st, n = state(cfg / name, HOME / "knowledge" / name)
        mark = "ok " if st == OK else "-> "
        extra = f" ({n} blank{'s' if n != 1 else ''} left)" if st == TEMPLATE else ""
        print(f"  {mark}{name:<24}{st}{extra}")
        if st != OK:
            unfilled.append(name)

    print()
    for name in SHIPS_COMPLETE:
        st = "ready" if (cfg / name).is_file() else MISSING
        print(f"     {name:<24}{st} (ships usable, edit when you disagree)")
    for name in OPTIONAL:
        st, n = state(cfg / name, HOME / "knowledge" / name)
        extra = f" ({n} blank{'s' if n != 1 else ''} left)" if st == TEMPLATE else ""
        print(f"     {name:<24}{st}{extra}")

    print()
    if not sum(inst.values()):
        print("The commands are not installed. Run scripts/setup.sh.")
        return 1

    if unfilled:
        print("Familiar does not know your voice yet, so a draft would be a guess.")
        print()
        print("  Fastest, if you have published before:")
        print("    /familiar-learn ingest <folder of your past writing>")
        print("    It reads them and drafts your voice files from evidence. You")
        print("    accept or reject each section; nothing is written without you.")
        print()
        print("  If you have not published, or would rather write it yourself:")
        print(f"    in {cfg}")
        print("      positioning.md   what the publication is")
        print("      voice-guide.md   how you write")
        print("    Short answers are fine. You can start with only positioning.")
        return 0

    print("Ready. Start with:  /familiar-interview <an idea you have been chewing on>")
    print("It asks one question at a time and stops when it has enough.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
