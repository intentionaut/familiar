#!/usr/bin/env python3
"""Install your engagement rule into an agent's own memory file.

`knowledge/engagement.md` says how you want an agent to talk to you. Every other
knowledge file is read by a Familiar stage, so it only applies while you are
inside one. This one has to apply everywhere, including in projects Familiar
knows nothing about, and the only place an agent reads before anything else is
its own memory file:

    Claude Code   ~/.claude/CLAUDE.md
    opencode      ~/.config/opencode/AGENTS.md
    Codex         ~/.codex/AGENTS.md
    Gemini CLI    ~/.gemini/GEMINI.md

Those files are yours and usually hold a great deal else, so the rule goes in
between two markers and nothing outside them is touched. Re-running replaces the
block rather than adding a second one.

    python3 scripts/engagement.py --check
    python3 scripts/engagement.py --install ~/.claude/CLAUDE.md
    python3 scripts/engagement.py --remove  ~/.claude/CLAUDE.md

Exit codes: 0 done, 2 nothing to install (off, or still a template), 1 a real
failure. `setup.sh` treats 2 as ordinary and says so once.
"""
import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import knowledge_dir  # noqa: E402

FILE = "engagement.md"
START = "<!-- familiar:engagement start -->"
END = "<!-- familiar:engagement end -->"
# Same shape doctor.py uses, so a file it calls a template is one this refuses.
PLACEHOLDER = re.compile(r"\[[^\]\n]{3,}\](?!\()")
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)

OFF, TEMPLATE, MISSING, READY = "off", "template", "missing", "ready"

# Where each agent keeps the file it reads before anything else. Kept here
# rather than in setup.sh so `--check` and the installer cannot disagree.
MEMORY_FILES = {
    "claude": "~/.claude/CLAUDE.md",
    "opencode": "~/.config/opencode/AGENTS.md",
    "codex": "~/.codex/AGENTS.md",
    "gemini": "~/.gemini/GEMINI.md",
}


def short_path(path):
    """A path a person can read."""
    path = Path(path)
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def setting_on(text):
    """Is `Engagement rule: on`? Anything else, including a bracket, is off."""
    m = re.search(r"^\s*[-*]?\s*Engagement rule\s*:\s*(.+?)\s*$",
                  text, re.I | re.M)
    return bool(m) and m.group(1).strip().lower() == "on"


def rule_body(text):
    """Everything under `## The rule`, which is the part that gets installed.

    Deliberately not the whole file. The rest of it explains what the file is
    for, and an explanation installed into a memory file is read every session
    as though it were an instruction.
    """
    m = re.search(r"^##\s+The rule\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return ""
    return m.group(1).strip()


def read_rule(explicit=None):
    """Return (state, body, source_path, whose)."""
    cfg, whose = knowledge_dir(explicit)
    path = cfg / FILE
    if not path.is_file():
        return MISSING, "", path, whose
    text = path.read_text(encoding="utf-8")
    body = rule_body(text)
    if not body or PLACEHOLDER.search(body):
        return TEMPLATE, body, path, whose
    if not setting_on(text):
        return OFF, body, path, whose
    return READY, body, path, whose


def block_for(body, source):
    """The managed block, with a line saying where to edit it.

    The pointer is not decoration. Without it the next person to read this file
    edits the copy, the next setup.sh run overwrites the edit, and the rule they
    thought they changed is the rule they had before.
    """
    return (
        f"{START}\n"
        f"<!-- Written by Familiar from {short_path(source)}. "
        f"Edit that file and re-run scripts/setup.sh; edits here are lost. -->\n"
        f"\n{body}\n\n"
        f"{END}"
    )


def write_atomic(path, text):
    """Write via a temp file in the same folder, then rename over.

    A memory file can hold months of accumulated rules. A half-written one is
    the kind of loss nobody notices until an agent starts behaving oddly.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".familiar-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def loose_copy(text, body):
    """Is the rule already in this file by hand, outside our block?

    Pasting it in yourself is the sensible first move and this installer is the
    second, so the two meeting is the normal case rather than a strange one. Two
    copies of one rule is not twice the rule; it is a file that contradicts
    itself the first time you edit one of them.
    """
    outside = BLOCK.sub("", text)
    for line in body.splitlines():
        line = line.strip()
        if len(line) > 24 and line in outside:
            return True
    return False


def install(target, body, source):
    target = Path(os.path.expanduser(target))
    block = block_for(body, source)
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""

    if BLOCK.search(existing):
        updated = BLOCK.sub(lambda _: block, existing, count=1)
        if updated == existing:
            return "current"
        write_atomic(target, updated)
        return "updated"

    warn = "duplicate" if loose_copy(existing, body) else ""
    if existing.strip():
        updated = existing.rstrip("\n") + "\n\n" + block + "\n"
    else:
        updated = block + "\n"
    write_atomic(target, updated)
    return warn or "installed"


def remove(target):
    target = Path(os.path.expanduser(target))
    if not target.is_file():
        return "absent"
    text = target.read_text(encoding="utf-8")
    if not BLOCK.search(text):
        return "absent"
    cleaned = re.sub(r"\n{3,}", "\n\n", BLOCK.sub("", text)).strip() + "\n"
    write_atomic(target, cleaned)
    return "removed"


def installed_in(target):
    """Is our block in this file, and does it match the rule as it stands now?"""
    target = Path(os.path.expanduser(target))
    if not target.is_file():
        return MISSING
    m = BLOCK.search(target.read_text(encoding="utf-8"))
    return "installed" if m else MISSING


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--install", metavar="FILE", help="a memory file to install into")
    ap.add_argument("--remove", metavar="FILE", help="take the block out again")
    ap.add_argument("--check", action="store_true", help="say what would happen")
    ap.add_argument("--config", help="a knowledge folder to read instead")
    ap.add_argument("--quiet", action="store_true", help="one line at most")
    args = ap.parse_args()

    if args.remove:
        print(f"  engagement rule: {remove(args.remove)}")
        return 0

    state, body, source, whose = read_rule(args.config)

    if args.check:
        print(f"engagement.md : {short_path(source)}  ({whose})")
        if state == MISSING:
            print("rule          : not there yet")
        elif state == TEMPLATE:
            print("rule          : still a template")
        elif state == OFF:
            print("rule          : written, switched off")
        else:
            print(f"rule          : ready, {len(body.splitlines())} lines")
        for agent, target in MEMORY_FILES.items():
            path = Path(os.path.expanduser(target))
            if not path.parent.exists():
                continue
            where = installed_in(target)
            mark = "installed" if where == "installed" else "not installed"
            print(f"  {agent:9} {short_path(path)}  {mark}")
        return 0

    if not args.install:
        ap.error("nothing to do: pass --install, --remove or --check")

    if state != READY:
        if not args.quiet:
            reason = {
                MISSING: f"no {FILE} in {short_path(source.parent)}",
                TEMPLATE: f"{short_path(source)} is still a template",
                OFF: f"{short_path(source)} has it switched off",
            }[state]
            print(f"  engagement rule: not installed, {reason}")
        return 2

    result = install(args.install, body, source)
    target = short_path(Path(os.path.expanduser(args.install)))
    if result == "duplicate":
        print(f"  engagement rule: added to {target}")
        print(f"    it looks like a copy is already in there by hand. Two copies of one")
        print(f"    rule disagree the first time you edit either. Take the loose one out.")
    elif result == "current":
        print(f"  engagement rule: already current in {target}")
    else:
        print(f"  engagement rule: {result} in {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
