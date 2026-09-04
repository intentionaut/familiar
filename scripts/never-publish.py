#!/usr/bin/env python3
"""Check a draft against knowledge/never-publish.md.

Familiar reports and never rewrites. This is the exception, and it is narrow on
purpose: it does not refuse to write anything, it refuses to send. Drafting is
private and reversible. Publishing is not.

Two severities, because a check that cries wolf gets switched off:

  block  names and money. Exit 1. A match is almost certainly real.
  warn   numbers and phrases. Exit 0. A match needs a person to look.

Usage:
  never-publish.py <file>        check a file
  never-publish.py -             check stdin
  never-publish.py --list        show what is loaded, without the strings

Exit 0 clean or warnings only, 1 blocked, 2 could not run.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths

WORDS = re.compile(r"[A-Za-z][A-Za-z\s.'&-]*$")


def load():
    """Return (on, block, warn). Missing file or empty list means off.

    A house that resolved to the shipped templates is not a house. Reading
    those as if they were the writer's own is the failure `paths.py` exists to
    prevent, and a list read from them would be empty anyway.
    """
    house, whose = paths.knowledge_dir()
    if whose != "yours":
        return False, [], []
    f = house / "never-publish.md"
    if not f.is_file():
        return False, [], []
    text = f.read_text()

    setting = re.search(r"^-\s*Never publish:\s*(.+)$", text, re.M)
    if setting:
        v = setting.group(1).strip().lower()
        if v.startswith("off"):
            return False, [], []
        if v.startswith("["):          # still the template
            return False, [], []

    def block_after(heading):
        m = re.search(rf"^## {heading}\b(.*?)(?=^## |\Z)", text, re.S | re.M)
        if not m:
            return []
        out = []
        for fence in re.findall(r"```(.*?)```", m.group(1), re.S):
            for line in fence.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                line = re.split(r"\s\s+#", line, maxsplit=1)[0].strip()
                if not line:
                    continue
                if line.startswith("[") and line.endswith("]"):
                    continue           # untouched template placeholder
                out.append(line)
        return out

    b, w = block_after("Block"), block_after("Warn")
    return bool(b or w), b, w


def present(term, text):
    """Whole words for names, substring for money and numbers.

    Without this a three-letter client name fires inside ordinary words, the
    check becomes noise, and the writer turns it off.

    A boundary is only asked for at an end that is a word character. `\\b` after
    the full stop in "Acme Inc." wants a letter next and a sentence never
    provides one, so the entry would sit on the list matching nothing, which is
    the one failure this check cannot have.
    """
    if WORDS.match(term):
        left = r"\b" if re.match(r"\w", term) else ""
        right = r"\b" if re.search(r"\w$", term) else ""
        return re.search(left + re.escape(term) + right, text, re.I) is not None
    return term.lower() in text.lower()


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)

    on, block, warn = load()

    if args[0] == "--list":
        house, whose = paths.knowledge_dir()
        print(f"house         : {house}  ({whose})")
        print(f"never publish : {'on' if on else 'off'}")
        print(f"block         : {len(block)}")
        print(f"warn          : {len(warn)}")
        return 0

    if not on:
        return 0                        # off is a supported way to work

    src = args[0]
    try:
        text = sys.stdin.read() if src == "-" else Path(src).read_text()
    except OSError as e:
        print(f"never-publish: cannot read {src}: {e}", file=sys.stderr)
        return 2

    hits_b = [t for t in block if present(t, text)]
    hits_w = [t for t in warn if present(t, text)]

    if hits_b:
        print("BLOCKED. This text contains something on your never-publish list.")
        for t in hits_b:
            print(f"  {t}")
        print("\nRemove it, or publish with the check off if the list is wrong.")
    if hits_w:
        print("\nWorth a look before this goes out:")
        for t in hits_w:
            print(f"  {t}")
    if not hits_b and not hits_w:
        print(f"never-publish: clean ({len(block) + len(warn)} on the list)")
    return 1 if hits_b else 0


if __name__ == "__main__":
    sys.exit(main())
