#!/usr/bin/env python3
"""Flag questions that break AGENTS.md, "Asking the writer".

Reads a prepared question file (interview-questions.md, or any markdown list of
questions) or a piece's SESSION-CONTEXT.md, where it checks the latest decision
gate. It catches the mechanical failures only. Whether the files already answer
a question is the asking stage's job; this cannot know.

  compound   more than one ask in one question
  memory     asks the writer to recall what they did rather than judge it now
  vague      an opener with no edges ("tell me more", "what are you noticing")
  internal   a theme id, a file name or a backticked label in the question
  shape      nothing says what a complete answer looks like
  not-asked  a decision gate that holds no question at all

Usage:
  question-check.py <file> [<file> ...]
  question-check.py --all SESSION-CONTEXT.md   every gate, not just the latest

Exit 0 clean, 1 flagged, 2 could not run.
"""
import argparse
import re
import sys
from pathlib import Path

MEMORY = re.compile(
    r"\b(remember|recall|back then|at the time|take the \w+ minutes"
    r"|what were you (looking at|doing|thinking)"
    r"|what did you (check|do|see|say|try|notice)( next| first)?"
    r"|when did you (first )?(realise|realize|notice|decide|know)"
    r"|the moment (you|of|when))\b", re.I)
VAGUE = re.compile(
    r"^\W*(\*\*)?(tell me (more|about (it|that|this|the week|your week))|what are you noticing|how (do|did) you feel"
    r"|any thoughts|thoughts\?|what('s| is) on your mind|anything else)", re.I)
INTERNAL = re.compile(r"`[^`]+`|\bT\d{1,2}\b|\b[\w-]+\.(md|py|json|html)\b")
PICK = re.compile(r"(^|\s|\*\*)A[.:)]", re.M)
SHAPE = re.compile(
    r"\b(yes or no|a number|how many|one (sentence|word|line|name|thing|moment"
    r"|decision|person|habit)|name one|which (one|of these|\w+ (survives|matters|goes|stays|first))|pick one"
    r"|or something else)\b", re.I)
LIST_ITEM = re.compile(r"^(\s{0,3})([-*+]|\d+[.)])\s+(.*)")
GATE_KEY = re.compile(r"^[A-Z][A-Za-z ]+:")


def asks(text):
    """Count the separate asks in one question."""
    body = re.sub(r"(^|\n)\s*(\*\*)?[A-D][.:)].*", "", text)  # option lines are not asks
    joined = len(re.findall(r",\s+and (why|what|how|when|who|where)\b", body, re.I))
    return body.count("?") + joined


def flags_for(text):
    out = []
    first = text.strip().splitlines()[0] if text.strip() else ""
    if "?" not in text:
        return ["not-asked"]
    if asks(text) > 1:
        out.append("compound")
    if MEMORY.search(text):
        out.append("memory")
    if VAGUE.search(first):
        out.append("vague")
    if INTERNAL.search(re.sub(r"\[(ASK THE WRITER|NEEDS SOURCE)[^\]]*\]", "", text)):
        out.append("internal")
    if not (PICK.search(text) and re.search(r"(^|\s|\*\*)B[.:)]", text)) and not SHAPE.search(text):
        out.append("shape")
    return out


def question_items(text):
    """(line number, text) for each question in a markdown list or paragraph."""
    items, cur, start = [], [], 0
    for n, line in enumerate(text.splitlines(), 1):
        m = LIST_ITEM.match(line)
        top = m and len(m.group(1)) == 0 and not re.match(r"\s*(\*\*)?[A-D][.:)]", m.group(3))
        if line.startswith("#") or not line.strip():
            if cur:
                items.append((start, "\n".join(cur)))
            cur = []
            continue
        if top:
            if cur:
                items.append((start, "\n".join(cur)))
            cur, start = [m.group(3)], n
        elif cur:
            cur.append(line.strip())
        elif "?" in line:
            cur, start = [line.strip()], n
    if cur:
        items.append((start, "\n".join(cur)))
    return [(n, t) for n, t in items if "?" in t]


def gates(text, every=False):
    found, cur, start = [], None, 0
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("Decision gate:"):
            cur, start = [line[len("Decision gate:"):].strip()], n
        elif cur is not None and line.strip() and not GATE_KEY.match(line) and not line.startswith("#"):
            cur.append(line.strip())
        elif cur is not None:
            found.append((start, " ".join(cur)))
            cur = None
    if cur is not None:
        found.append((start, " ".join(cur)))
    found = [(n, g) for n, g in found if not re.match(r"(none|n/a)\b", g, re.I)]
    return found if every else found[-1:]


def check(path, every=False):
    text = Path(path).read_text()
    if Path(path).name == "SESSION-CONTEXT.md":
        items = gates(text, every)
    else:
        items = question_items(text)
    return [(n, f, q) for n, q in items for f in flags_for(q)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--all", action="store_true", help="every decision gate, not only the latest")
    a = ap.parse_args()
    total = 0
    for f in a.files:
        try:
            found = check(f, a.all)
        except OSError as e:
            print(f"question-check could not read {f}: {e}", file=sys.stderr)
            return 2
        for n, flag, q in found:
            print(f"{f}:{n}: {flag}: {q.splitlines()[0][:100]}")
        total += len(found)
    if total:
        print(f"\n{total} flag(s). Rewrite per AGENTS.md, \"Asking the writer\", before the writer sees them.")
        return 1
    print("question-check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
