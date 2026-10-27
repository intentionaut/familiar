#!/usr/bin/env python3
"""Flag runs of confident, unsourced assertions in a draft. It flags; it never
edits and never blocks, and it uses no model.

A weak paragraph reads as well as a strong one, so no human gate catches it:
three claims in a row, each stated flat, none with a source, a quote or a
hedge, sound as sure as the one she can back. This marks the runs so she knows
where to look. It cannot tell whether the claims are true, only that nothing in
the text holds them up.

A sentence counts toward a run when it is claim-shaped and nothing holds it up:

  claim-shaped  a claim pattern (a number or percentage, "studies
                show", "the first/largest/only", "most teams"), a sweeping word
                ("always", "never", "everyone", "nobody", "every x"), or a causal
                verb ("because", "drives", "leads to")
  held up by    a link, a citation "(Name, 2024)", "according to Name", a quotation
                or an `[NEEDS SOURCE` / `[ASK THE WRITER` bracket in the sentence
  hedged        "may", "might", "could", "perhaps", "probably", "seems", "often",
                "sometimes", "I think" and the like
  hers          a sentence that opens with I or we is her own experience, not a claim

A run is three or more such sentences in a row inside one paragraph (`--run`
changes the length). One claim-shaped sentence alone is not flagged: the
patterns catch plain prose too ("the first thing I did", "the most useful
meeting"), and a lone one is not uniform confidence.

Usage:
  unsourced-run.py <draft.md> [<draft.md> ...] [--run 3] [--json]

Exit 0 whether or not anything is flagged (a flag is advice, not a stop).
Exit 2 when it could not run: a file is missing.
"""
import argparse
import json
import re
import sys
from pathlib import Path

QUESTION = "which of these can she back?"
CANNOT_TELL = ("Cannot tell: whether any claim is true or common knowledge, or whether the draft holds a source "
               "this cannot see. Those are the writer's call.")
RUN = 3

# The first four are the regex pass a research tool runs to find claims that need a source, copied: core imports
# nothing from another module.
PATTERNS = (
    ("number", re.compile(r"\d+(\.\d+)?\s*(%|per ?cent|x\b|times\b)|[£$€]\s?\d|\b\d+(\.\d+)?\s*(million|billion|bn|m)\b"
                          r"|\b\d+(\.\d+)?\s+(days|weeks|months|hours|people|customers|users|teams|engineers|companies)\b", re.I)),
    ("research", re.compile(r"\b(studies|research|data|surveys?|reports?|experts?)\s+(show|shows|suggest|suggests|find|finds|found|agree|say|says)\b", re.I)),
    ("superlative", re.compile(r"\bthe (first|largest|biggest|only|fastest|most)\b", re.I)),
    ("market", re.compile(r"\b(most|every|all) (companies|teams|organisations|organizations|businesses|leaders|founders)\b", re.I)),
    # Added here: those four miss a flat claim made in plain words, and flag plain prose ("the first thing I did").
    ("sweeping", re.compile(r"\b(always|never|everyone|everybody|nobody|no one|every \w+|impossible|inevitabl[ey]|"
                            r"obviously|clearly|undeniabl[ey]|proven)\b", re.I)),
    ("causal", re.compile(r"\b(because|causes?|caused|drives?|drove|leads? to|led to|results? in|kills?|killed|is why|the reason)\b", re.I)),
)
HEDGE = re.compile(r"\b(may|might|could|perhaps|probably|possibly|seems?|appears?|often|sometimes|usually|tends? to|"
                   r"likely|arguably|in my experience|i think|i suspect|i believe|for me)\b", re.I)
HELD_UP = re.compile(r"https?://|\]\(|\(\s*[A-Z][^()]{1,60},\s*(19|20)\d{2}\s*\)|\baccording to [A-Z]|"
                     r"\[(?:NEEDS SOURCE|ASK THE WRITER)", re.I)
HERS = re.compile(r"^\s*(i|i'm|i've|i'd|i'll|we|we're|we've|we'd|we'll|my|our|me)\b", re.I)


class CannotRun(Exception):
    pass


def blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


def readable(text):
    """The draft with front matter, code, headings, block quotes blanked and quotations marked, same line numbers.
    A quotation is replaced by a QUOTE marker so the sentence around it still counts as held up."""
    text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", blank, text, flags=re.M | re.S)
    text = re.sub(r"`[^`\n]+`", blank, text)
    text = re.sub(r"^\s{0,3}(#{1,6}\s|>).*$", blank, text, flags=re.M)
    return re.sub(r'"[^"\n]*"|“[^”\n]*”', "[QUOTE]", text)


def paragraphs(text):
    """[(first line number, [(line, sentence)])] for each block of text between blank lines."""
    out, cur, start = [], [], None
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            if cur:
                out.append((start, cur))
            cur, start = [], None
            continue
        start = start or n
        for m in re.finditer(r"[^.!?]+[.!?]*", line):
            if m.group(0).strip():
                cur.append((n, m.group(0).strip()))
    if cur:
        out.append((start, cur))
    return out


def signals(sentence):
    """The claim patterns the sentence matches, or [] when it is not claim-shaped or something holds it up."""
    if HERS.match(sentence) or HELD_UP.search(sentence) or "[QUOTE]" in sentence or HEDGE.search(sentence):
        return []
    return [name for name, rx in PATTERNS if rx.search(sentence)]


def check(text, run=RUN):
    runs, lone = [], 0
    for _, sents in paragraphs(readable(text)):
        group = []
        for n, s in sents + [(0, "")]:
            sig = signals(s) if s else []
            if sig:
                group.append({"line": n, "sentence": s, "signals": sig})
                continue
            if len(group) >= run:
                runs.append({"from_line": group[0]["line"], "to_line": group[-1]["line"], "sentences": group,
                             "why": f"{len(group)} sentences in a row, none with a source, quote or hedge: {QUESTION}"})
            elif group:
                lone += len(group)
            group = []
    return {"runs": runs, "claim_shaped_not_flagged": lone}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--run", type=int, default=RUN, help=f"sentences in a row that make a run (default {RUN})")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if not a.files:
            raise CannotRun("no draft given")
        missing = [f for f in a.files if not Path(f).is_file()]
        if missing:
            raise CannotRun(f"not found: {', '.join(missing)}")
        report = {f: check(Path(f).read_text(encoding="utf-8"), a.run) for f in a.files}
    except CannotRun as e:
        print(f"unsourced-run: could not run. {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(report, indent=2))
        return 0
    for f, res in report.items():
        print(f"{f}: {len(res['runs'])} run{'s' if len(res['runs']) != 1 else ''} of {a.run} or more "
              f"(claim-shaped sentences outside a run, not flagged: {res['claim_shaped_not_flagged']})")
        for r in res["runs"]:
            print(f"  lines {r['from_line']}-{r['to_line']}  {r['why']}")
            for s in r["sentences"]:
                print(f"    line {s['line']}  {'+'.join(s['signals'])}  \"{s['sentence']}\"")
    print(f"\nNothing here is applied. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
