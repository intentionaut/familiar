#!/usr/bin/env python3
"""Flag the sentences in a draft that claim an experience nobody gave it. It
flags; it never edits and never blocks.

No check can tell whether a joke lands or a feeling is true. This asks where a
line came from. A model has no lived experience, so a first-person, sensory,
anecdote or joke-shaped sentence in a draft is either the writer's (it traces
to her notes) or invented. Each one that does not trace is a question for her,
the same `[ASK THE WRITER: ...]` the draft stage already uses for a scene or a
feeling it was not given. Whether a line lands stays her call; this only makes
sure she is asked.

Four shapes, matched by pattern:

  first-person  I or we followed by a past-tense verb: "I stood in the car park"
  sensory       smell, taste, sound, sight and touch words used as scene: "smelled of"
  anecdote      a stock opening for a story: "last winter", "one morning", "years ago"
  joke          a joke or a wink at the reader: "plot twist", "spoiler", "who knew"

A flagged sentence is traced when a sentence of her notes holds most of its
content words, or a long run of its words in order. The sources are notes.md
and, where they exist, source.md and session.md in the piece folder, plus any
`--also` file. A sentence that already carries an `[ASK THE WRITER` or
`[NEEDS SOURCE` bracket, a quotation, a heading, a block quote or code is not
read.

Usage:
  experience-flags.py <piece folder> [--also FILE ...] [--json]
  experience-flags.py --draft draft.md --notes notes.md [--also FILE ...]

Exit 0 whether or not anything is flagged (a flag is advice, not a stop).
Exit 2 when it could not run: a file is missing, or a source holds nothing to
trace against. A draft with no sources is unknown, never clean.
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

CANNOT_TELL = ("Cannot tell: whether the line is true, whether it lands, or whether she told it to the "
               "interviewer without it reaching the notes. Those are the writer's call.")
COVER = 0.5              # share of the sentence's content words one source sentence holds
MIN_SHARED = 3           # and at least this many
RATIO = 0.6              # or the word-order match between the two sentences
STOP = set("a an the and or but of to in on at for with by from as is are was were be been it its this that i we "
           "you he she they so do did does have has had my our me us".split())

PAST = (r"was|were|had|did|went|saw|felt|found|said|told|made|took|got|came|knew|thought|ran|sat|stood|heard|"
        r"watched|spent|wrote|built|lost|left|asked|began|started|met|paid|sent|woke|slept|drove|read|forgot|"
        r"\w{3,}(?<!e)ed")
SHAPES = (
    ("first-person", re.compile(rf"\b(?:i|we)\b[^.!?]{{0,20}}?\b(?:{PAST})\b", re.I)),
    ("sensory", re.compile(r"\b(?:smell(?:s|ed)?|smelt|scent|aroma|stench|stank|stink(?:s|ing)?|taste[ds]?|"
                           r"the (?:sound|sight|feel|hum|hiss|creak|echo|glare|chill|damp) of|hummed|buzzed|"
                           r"creaked|hissed|felt (?:cold|warm|hot|heavy|tight|sick|damp))\b", re.I)),
    ("anecdote", re.compile(r"\b(?:one (?:day|morning|evening|night|afternoon|time)|last (?:week|month|year|summer|"
                            r"winter|spring|autumn|night)|yesterday|(?:years?|months?|weeks?|days?|summers?|winters?) ago|"
                            r"the other day|that (?:morning|evening|night|afternoon|day|week)|back then|"
                            r"when i was|i (?:still )?remember)\b", re.I)),
    ("joke", re.compile(r"\b(?:plot twist|spoiler(?: alert)?|who knew|what could (?:possibly )?go wrong|"
                        r"cue the|walks? into a bar|as one does|narrator:|reader, )", re.I)),
)
BRACKET = re.compile(r"\[(?:ASK THE WRITER|NEEDS SOURCE)", re.I)


class CannotRun(Exception):
    pass


def norm(s):
    s = s.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^\w' ]+", " ", re.sub(r"[*_`]", "", s.lower()))).strip()


def words(s):
    return norm(s).split()


def content(s):
    return {w for w in words(s) if w not in STOP}


def sentences(text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"[^.!?]+[.!?]*", line):
            if m.group(0).strip():
                out.append((n, m.group(0).strip()))
    return out


def blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


def readable(text):
    """The draft with front matter, code, headings, block quotes and quotations blanked, same line numbers."""
    text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", blank, text, flags=re.M | re.S)
    text = re.sub(r"`[^`\n]+`", blank, text)
    text = re.sub(r"^\s{0,3}(#{1,6}\s|>).*$", blank, text, flags=re.M)
    return re.sub(r'"[^"\n]*"|“[^”\n]*”', blank, text)


def source_sentences(text):
    text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)
    return [s for _, s in sentences(re.sub(r"^\s{0,3}#{1,6}\s.*$", blank, text, flags=re.M)) if not s.startswith("[")]


def traced(sentence, sources):
    mine, sw = content(sentence), words(sentence)
    for s in sources:
        shared = len(mine & content(s))
        if (mine and shared / len(mine) >= COVER and shared >= MIN_SHARED) or \
                SequenceMatcher(None, sw, words(s), autojunk=False).ratio() >= RATIO:
            return True
    return False


def check(draft, sources):
    flags = []
    for n, s in sentences(readable(draft)):
        if BRACKET.search(s):
            continue
        shapes = [name for name, rx in SHAPES if rx.search(s)]
        if shapes and not traced(s, sources):
            flags.append({"line": n, "shapes": shapes, "sentence": s,
                          "ask": f"[ASK THE WRITER: where did this come from? ({shapes[0]})]"})
    return flags


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("piece", nargs="?", help="a piece folder with draft.md and notes.md")
    ap.add_argument("--draft")
    ap.add_argument("--notes")
    ap.add_argument("--also", action="append", default=[], help="another file she wrote or said, to trace against")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.piece:
            d = Path(a.piece)
            draft_p, notes_p = d / "draft.md", d / "notes.md"
            also = [str(d / n) for n in ("source.md", "session.md") if (d / n).is_file()] + a.also
        elif a.draft and a.notes:
            draft_p, notes_p, also = Path(a.draft), Path(a.notes), a.also
        else:
            raise CannotRun("give a piece folder, or --draft and --notes")
        files = [draft_p, notes_p] + [Path(f) for f in also]
        missing = [str(f) for f in files if not f.is_file()]
        if missing:
            raise CannotRun(f"not found: {', '.join(missing)}")
        sources = []
        for f in files[1:]:
            sources += source_sentences(f.read_text(encoding="utf-8"))
        if not sources:
            raise CannotRun("the notes hold no sentences to trace against. This is unknown, not clean.")
        flags = check(draft_p.read_text(encoding="utf-8"), sources)
    except CannotRun as e:
        print(f"experience-flags: could not run. {e}", file=sys.stderr)
        return 2
    traced_against = [str(f) for f in files[1:]]
    if a.json:
        print(json.dumps({"draft": str(draft_p), "traced_against": traced_against, "flags": flags}, indent=2))
        return 0
    print(f"draft: {draft_p}\ntraced against: {', '.join(traced_against)}")
    print(f"\n{len(flags)} sentence{'s' if len(flags) != 1 else ''} with no trace to her notes")
    for f in flags:
        print(f"  line {f['line']}  {'+'.join(f['shapes'])}  \"{f['sentence']}\"\n    {f['ask']}")
    print(f"\nNothing here is applied. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
