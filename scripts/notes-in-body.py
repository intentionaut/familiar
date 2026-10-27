#!/usr/bin/env python3
"""List the writer's own sentences from notes.md that the draft paraphrased. It
lists; it never edits and never blocks.

The draft is written from her notes, and a model that paraphrases her sentence
has sanded off the wording that was hers. Every line listed is a question, "put
her wording back, or let it go?", not a verdict: the paraphrase may be better
for where it sits, and that is her call.

Which sentences are hers. notes.md mixes her answers with the interviewer's
summary, so only the places that hold her words are read:

  - the sections `## Working thesis` and `## Spark candidates` (the interview's
    exit block keeps both in her words; `--sections` names others)
  - any block quote (`> ...`) anywhere in the file

A sentence under five words is not checked: a short line is too easy to
reproduce by accident for a match to mean anything.

Each of her sentences lands in one of three places:

  verbatim      it is in the draft as she wrote it (case, curly quotes and
                punctuation aside), alone or inside a longer sentence. Fine.
  paraphrased   a draft sentence says nearly the same thing in other words:
                most of her content words, or a long matching run of her words,
                are there. Listed.
  left out      nothing in the draft is close. Counted, not listed: leaving a
                line out is a choice, and the cutting room is where it goes.

Usage:
  notes-in-body.py <piece folder> [--sections "working thesis,spark candidates"] [--json]
  notes-in-body.py --notes notes.md --draft draft.md

Exit 0 whether or not anything is listed (a list is advice, not a stop).
Exit 2 when it could not run: a file is missing, or notes.md holds none of her
sentences to compare. That is unknown, never clean.
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

QUESTION = "put her wording back, or let it go?"
CANNOT_TELL = ("Cannot tell: whether the paraphrase reads better where it sits, or whether notes.md marks every "
               "sentence of hers. Those are the writer's call.")
SECTIONS = ("working thesis", "spark candidates")
MIN_WORDS = 5            # a shorter sentence is not checked
COVER = 0.5              # share of her content words the draft sentence has
MIN_SHARED = 3           # and at least this many of them
RATIO = 0.6              # or the word-order match between the two sentences
STOP = set("a an the and or but of to in on at for with by from as is are was were be been it its this that i we "
           "you he she they so do did does have has had".split())


class CannotRun(Exception):
    pass


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[*_`]", "", s.lower())
    return re.sub(r"\s+", " ", re.sub(r"[^\w' ]+", " ", s)).strip()


def words(s):
    return norm(s).split()


def content(s):
    return {w for w in words(s) if w not in STOP}


def sentences(text):
    """[(line number, sentence)]. A line break ends one too, so a list item never joins the next line."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"[^.!?]+[.!?]*", line):
            s = m.group(0).strip()
            if s:
                out.append((n, s))
    return out


def body(text):
    return re.sub(r"\A---\n.*?\n---\n", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def hers(notes, sections):
    """[(line, sentence)] from her sections and block quotes, markers and brackets stripped."""
    keep, section, picked = {s.lower() for s in sections}, "", []
    for n, raw in enumerate(body(notes).splitlines(), 1):
        if raw.startswith("#"):
            section = raw.lstrip("#").strip().lower()
            continue
        quoted = raw.lstrip().startswith(">")
        if not (quoted or section in keep):
            continue
        line = re.sub(r"^\s*(>\s*)*([-*+]|\d+[.)])?\s*", "", raw).strip().strip('"“”')
        if not line or line.startswith("[") or line.startswith("<"):
            continue
        picked += [(n, s.strip('"“” ')) for _, s in sentences(line)]
    return picked


def compare(her, draft_sents, draft_norm):
    """('verbatim' | 'paraphrased' | 'left out', best draft (line, sentence) or None, similarity)."""
    if f" {norm(her)} " in f" {draft_norm} ":
        return "verbatim", None, 1.0
    mine, hw = content(her), words(her)
    best, score = None, 0.0
    for n, s in draft_sents:
        shared = len(mine & content(s))
        cover = shared / len(mine) if mine else 0.0
        ratio = SequenceMatcher(None, hw, words(s), autojunk=False).ratio()
        if (cover >= COVER and shared >= MIN_SHARED) or ratio >= RATIO:
            if max(cover, ratio) > score:
                best, score = (n, s), max(cover, ratio)
    return ("paraphrased", best, round(score, 2)) if best else ("left out", None, 0.0)


def check(notes, draft, sections=SECTIONS):
    found = hers(notes, sections)
    mine = [(n, s) for n, s in found if len(words(s)) >= MIN_WORDS]
    if not found:
        raise CannotRun("notes.md holds none of her sentences to compare: no " + " or ".join(f"'## {s.title()}'" for s in sections)
                        + " section and no block quote. This is unknown, not clean.")
    text = body(draft)
    sents, dn = sentences(text), norm(text)
    out = {"checked": len(mine), "too_short": len(found) - len(mine), "verbatim": 0, "left_out": 0, "paraphrased": []}
    for n, s in mine:
        kind, near, score = compare(s, sents, dn)
        if kind == "verbatim":
            out["verbatim"] += 1
        elif kind == "left out":
            out["left_out"] += 1
        else:
            out["paraphrased"].append({"notes_line": n, "hers": s, "draft_line": near[0], "draft": near[1],
                                       "similarity": score, "why": QUESTION})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("piece", nargs="?", help="a piece folder with notes.md and draft.md")
    ap.add_argument("--notes")
    ap.add_argument("--draft")
    ap.add_argument("--sections", help="comma-separated headings in notes.md that hold her words")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.piece:
            notes_p, draft_p = Path(a.piece) / "notes.md", Path(a.piece) / "draft.md"
        elif a.notes and a.draft:
            notes_p, draft_p = Path(a.notes), Path(a.draft)
        else:
            raise CannotRun("give a piece folder, or --notes and --draft")
        missing = [str(p) for p in (notes_p, draft_p) if not p.is_file()]
        if missing:
            raise CannotRun(f"not found: {', '.join(missing)}")
        sections = [s.strip() for s in a.sections.split(",") if s.strip()] if a.sections else SECTIONS
        res = check(notes_p.read_text(encoding="utf-8"), draft_p.read_text(encoding="utf-8"), sections)
    except CannotRun as e:
        print(f"notes-in-body: could not run. {e}", file=sys.stderr)
        return 2
    res.update(notes=str(notes_p), draft=str(draft_p))
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    print(f"notes: {notes_p}   draft: {draft_p}")
    print(f"her sentences checked: {res['checked']}  verbatim: {res['verbatim']}  "
          f"paraphrased: {len(res['paraphrased'])}  left out: {res['left_out']}  too short to check: {res['too_short']}")
    for p in res["paraphrased"]:
        print(f"\n  notes line {p['notes_line']}: \"{p['hers']}\"\n  draft line {p['draft_line']}: \"{p['draft']}\"\n"
              f"  {p['similarity']:.0%} alike. {p['why']}")
    print(f"\nNothing here is applied. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
