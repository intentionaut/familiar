#!/usr/bin/env python3
"""Show what a suggested rewrite costs: compare each (her line, proposed line)
pair and flag the rough edges the proposal removes. It flags; it never edits
and never blocks.

Polish is not free. A rough edge often carries the voice, and a suggestion that
reads better can still read less like her. Every flag is a question, "does she
want this cost?", not a verdict. Four signals, per pair:

  contractions   a contraction in her line that the proposal expands or drops
  idiom          a spoken idiom in her line that the proposal does not keep
  fragments      her short sentences (five words or fewer) joined or cut, so
                 the proposal has fewer sentences than her line
  length         total words, or mean sentence length, moved more than the
                 band (default 30 percent; at least four words)

Where the pairs come from:

  a report     `edits/line-edit-report.md` or `edits/dev-edit-report.md`: a
               quoted line, `[line N] "her words"`, followed by `Fix:` or
               `Rewrite:` with the proposed line. A `Fix:` that is an
               instruction ("cut it") has no rewritten line to compare and is
               counted, not guessed at.
  --pair       --pair "her line" "proposed line", repeatable
  --pairs      a JSON file: [{"her": "...", "proposed": "...", "label": "..."}]

The idiom list is a short generic one. The writer's own list is read from
--idioms, FAMILIAR_IDIOMS or `idioms = ` in `.familiar`, one phrase per line;
it adds to the generic list. A named list that is missing is unknown, never
clean.

Usage:
  edge-diff.py <report.md> [<report.md> ...] [--pair HER PROPOSED]
               [--pairs pairs.json] [--idioms idioms.txt] [--band 0.3] [--json]

Exit 0 whether or not anything is flagged (a flag is advice, not a stop).
Exit 2 when it could not run: a file is missing, a named idiom list cannot be
read, or a report shows suggestions and no pair could be read from it.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paths  # noqa: E402

QUESTION = "does she want this cost?"
CANNOT_TELL = ("Cannot tell: whether the proposal reads better, or whether the edge was a fault. "
               "Those are the writer's call.")
BAND = 0.30
MIN_WORDS_MOVED = 4     # a short line moves by whole words; below this the ratio is noise
SHORT = 5               # words: a sentence this short is a fragment she may have meant

# Generic spoken idioms. Narrow on purpose: a longer list flags ordinary phrases.
IDIOMS = (
    "a bit of a", "a couple of", "pretty much", "sort of", "kind of", "i reckon", "fair enough",
    "the long and short of it", "come to think of it", "off the cuff", "back of an envelope",
    "rule of thumb", "get your head around", "get a handle on", "in the weeds", "on the back foot",
    "bite the bullet", "up in the air", "back to square one", "no-brainer", "rough and ready",
    "go through the motions", "tip of the iceberg", "fall flat", "hit the ground running",
    "keep an eye on", "end up", "figure out", "turn out", "boils down to", "at the end of the day",
    "by and large", "more or less", "for what it's worth", "if i'm honest", "to be fair",
)
# A Fix that starts with one of these is an instruction, not a rewritten line.
IMPERATIVE = {"cut", "drop", "delete", "remove", "name", "source", "add", "move", "replace", "split",
              "merge", "keep", "say", "ask", "check", "use", "make", "state", "show", "give", "put",
              "swap", "choose", "pick", "reword", "rewrite", "shorten", "lengthen", "quote", "cite"}

_CONTRACTION = re.compile(r"\b(?:\w+(?:n't|'re|'ve|'ll|'d|'m)|(?:it|he|she|that|there|here|what|who|let|how|where|when)'s)\b", re.I)
_QUOTE = re.compile(r'^\s*(?:\*\*)?\[line\s+(\d+)\](?:\*\*)?\s+["“](.*?)["”]\s*$')
_KEY = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?(Fix|Rewrite)(?:\*\*)?\s*:(?:\*\*)?\s*(.*)$", re.I)
_STOPS = re.compile(r"^\s*(?:(?:\*\*)?(?:Issue|Why it matters|Tradeoff|Question to the writer|Disposition|"
                    r"Fix|Rewrite)(?:\*\*)?\s*:|\[line\s+\d+\]|#{1,6}\s|```|\*\*\d)", re.I)


class CannotRun(Exception):
    pass


def _norm(s):
    return s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


def _sentences(s):
    return [p.strip() for p in re.split(r'(?<=[.!?])["\')]*\s+|\n+', _norm(s).strip()) if p.strip()]


def _words(s):
    return re.findall(r"[\w'-]+", _norm(s))


# -- reading pairs -------------------------------------------------------------------------------------------------
def read_report(path):
    """(pairs, instructions, markers) from a report. `markers` counts Fix/Rewrite lines seen, so a report whose
    suggestions could not be paired is unknown rather than clean."""
    pairs, instructions, markers = [], 0, 0
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    quote, n = None, 0
    i = 0
    while i < len(lines):
        m = _QUOTE.match(lines[i])
        if m:
            quote, n = m.group(2), int(m.group(1))
            i += 1
            continue
        k = _KEY.match(lines[i])
        if k:
            markers += 1
            body = [k.group(2).strip()]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not _STOPS.match(lines[j]):
                body.append(lines[j].strip())
                j += 1
            fix = " ".join(b for b in body if b).strip().strip("`").strip()
            fix = re.sub(r'^["“](.*)["”]$', r"\1", fix)
            first = (_words(fix) or [""])[0].lower()
            if quote is None or not fix:
                instructions += 1
            elif first in IMPERATIVE and not re.search(r'["“]', k.group(2)):
                instructions += 1
            else:
                pairs.append({"her": quote, "proposed": fix, "label": f"{Path(path).name} line {n}", "line": n})
            i = j
            continue
        i += 1
    return pairs, instructions, markers


def read_idioms(explicit=None):
    """(extra idioms, source, named). A named list that is missing raises; none named is just the generic list."""
    cand = explicit or os.environ.get("FAMILIAR_IDIOMS") or next(iter(paths.read_config().get("idioms", [])), None)
    if not cand:
        return [], None, False
    p = Path(cand).expanduser()
    if not p.is_file():
        raise CannotRun(f"idiom list named at {p} and not found. Her idioms were not checked; this is unknown, not clean.")
    out = [ln.strip().lstrip("-* ").strip("`").lower() for ln in p.read_text(encoding="utf-8").splitlines()]
    return [x for x in out if x and not x.startswith("#")], p, True


# -- the signals ---------------------------------------------------------------------------------------------------
def _has(text, phrase):
    return re.search(rf"(?<![\w'-]){re.escape(phrase)}(?![\w'-])", _norm(text), re.I) is not None


def compare(her, proposed, idioms, band=BAND):
    """[(rule, detail)] for one pair, in a fixed order."""
    out = []
    h, p = _norm(her), _norm(proposed)

    lost = Counter(c.lower() for c in _CONTRACTION.findall(h)) - Counter(c.lower() for c in _CONTRACTION.findall(p))
    if lost:
        out.append(("contractions", "her " + ", ".join(f'"{c}"' for c in lost.elements()) + " not kept"))

    for phrase in idioms:
        if _has(h, phrase) and not _has(p, phrase):
            out.append(("idiom", f'her "{phrase}" not kept'))

    hs, ps = _sentences(h), _sentences(p)
    if len(ps) < len(hs) and any(0 < len(_words(s)) <= SHORT for s in hs):
        out.append(("fragments", f"her {len(hs)} sentences became {len(ps)}, and she had a short one"))

    hw, pw = len(_words(h)), len(_words(p))
    moved = abs(pw - hw)
    if hw and moved >= MIN_WORDS_MOVED and moved / hw > band:
        out.append(("length", f"{hw} words became {pw} ({'+' if pw > hw else '-'}{round(100 * moved / hw)}%)"))
    elif hs and ps and not any(r == "fragments" for r, _ in out):
        hm, pm = hw / len(hs), pw / len(ps)
        if hm and abs(pm - hm) >= MIN_WORDS_MOVED and abs(pm - hm) / hm > band:
            out.append(("length", f"mean sentence length {hm:.0f} words became {pm:.0f}"))
    return out


def check(pairs, idioms, band=BAND):
    return [{"label": p.get("label", ""), "line": p.get("line"), "her": p["her"], "proposed": p["proposed"],
             "flags": [{"rule": r, "detail": d, "why": QUESTION} for r, d in compare(p["her"], p["proposed"], idioms, band)]}
            for p in pairs]


# -- main ----------------------------------------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reports", nargs="*", help="line-edit or dev-edit report files")
    ap.add_argument("--pair", nargs=2, action="append", metavar=("HER", "PROPOSED"), default=[])
    ap.add_argument("--pairs", help="JSON file of {her, proposed, label} objects")
    ap.add_argument("--idioms", help="the writer's idiom list, one phrase per line")
    ap.add_argument("--band", type=float, default=BAND, help="relative length change that flags (default 0.3)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if not (a.reports or a.pair or a.pairs):
            raise CannotRun("nothing to compare: give a report, --pair or --pairs")
        extra, idiom_src, _ = read_idioms(a.idioms)
        idioms = list(dict.fromkeys([*IDIOMS, *extra]))
        pairs, instructions = [], 0
        for r in a.reports:
            if not Path(r).is_file():
                raise CannotRun(f"not found: {r}")
            got, ins, markers = read_report(r)
            if markers and not got and not ins:
                raise CannotRun(f"{r}: suggestions found and no pair could be read from them. Unknown, not clean.")
            pairs += got
            instructions += ins
        if a.pairs:
            try:
                data = json.loads(Path(a.pairs).read_text(encoding="utf-8"))
                pairs += [{"her": d["her"], "proposed": d["proposed"], "label": d.get("label", "")} for d in data]
            except (OSError, ValueError, KeyError, TypeError) as e:
                raise CannotRun(f"{a.pairs} is not a list of {{her, proposed}} pairs: {e}")
        pairs += [{"her": h, "proposed": p, "label": "pair"} for h, p in a.pair]
    except CannotRun as e:
        print(f"edge-diff: could not run. {e}", file=sys.stderr)
        return 2

    results = check(pairs, idioms, a.band)
    report = {"pairs": len(pairs), "instructions": instructions,
              "idioms": {"generic": len(IDIOMS), "own": len(extra), "file": str(idiom_src) if idiom_src else None},
              "results": results}
    if a.json:
        print(json.dumps(report, indent=2))
        return 0
    own = f", {len(extra)} of her own ({idiom_src})" if idiom_src else ", none of her own set"
    print(f"idioms: {len(IDIOMS)} generic{own}")
    print(f"pairs read: {len(pairs)}" + (f" ({instructions} suggestions had no rewritten line to compare)" if instructions else ""))
    flagged = 0
    for n, r in enumerate(results, 1):
        if not r["flags"]:
            continue
        flagged += 1
        where = f"line {r['line']}" if r["line"] else r["label"]
        print(f"\npair {n} ({where}): \"{r['her']}\"")
        print(f"  proposed: \"{r['proposed']}\"")
        for f in r["flags"]:
            print(f"  {f['rule']}  {f['detail']}  {f['why']}")
    print(f"\n{flagged} of {len(pairs)} pairs flagged. Each flag asks a question; nothing here is applied. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
