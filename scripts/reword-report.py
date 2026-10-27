#!/usr/bin/env python3
"""Change report for a reworded draft: what changed, what was added, green, amber or red.
Report only (stage 1 of the tiered rewording plan). It never edits, restores, blocks or sends.

It compares a draft with the writer's source, sentence by sentence, and checks what a program can check:

  kept        share of the source's words that survive in the draft, and per sentence how many changed
  limits      the tier's limit: tier 1 verbatim, tier 2 about 10 percent of a sentence's words, tier 3 length within
              plus or minus 25 percent, tier 4 added material allowed (listed, never silently accepted)
  protected   numbers, quoted spans and modal or hedge words (could, will, might) in the source that are missing or
              changed in the draft. These stay verbatim at every tier.
  added       draft sentences with no source sentence behind them, scanned for a new number, a new name,
              first person, an anecdote or sensory line, and a joke-shaped line

  edit cap    more than three edits (changed or added sentences) in one paragraph is amber, at every tier
              (the first-run number, #639; adjust from the reports)

Red is a hard fail: a protected span gone or changed, or an added sentence that carries a new number, a first-person
anecdote or a joke. Amber is a tier limit passed, or any added sentence to read. Green is none of those.

Not run here, and said so in every report (unknown, never clean): the per-sentence meaning-drift check, which needs
a reader, and the voice-file check, which is the existing gate.

Usage:
  reword-report.py <source> <draft> [--tier 1-4] [--json]

Exit 0 whether the report is green, amber or red. Exit 2 when it could not run: a file is missing or empty.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

NOT_RUN = ["meaning drift per sentence (needs a reader; same, narrower or different)",
           "voice-file check (the existing gate, not called here)"]
CANNOT_TELL = ("Cannot tell: whether a changed sentence still means the same, whether an added sentence is true, "
               "or whether a joke-shaped line is a joke. Those are the writer's call.")
DEFAULT_TIER = 2
LIMIT = {2: 0.10}              # tier 2: share of a sentence's words changed
EDIT_CAP = 3                   # edits (changed or added sentences) per draft paragraph; first-run number, adjust from reports
LENGTH_BAND = 0.25             # tier 3 and 4: draft length against source length
SAME = 0.6                     # a draft sentence this close to a source sentence is that sentence, reworded
MODALS = ("could", "would", "should", "might", "may", "can", "will", "must", "maybe", "perhaps", "probably",
          "possibly", "sometimes", "often", "usually", "rarely", "never", "always", "mostly", "roughly", "about")

NUMBER = re.compile(r"[£$€]?\d[\d,.]*\s?(?:%|k|m|bn|x)?", re.I)
QUOTED = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')
NAME = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*")
FIRST = re.compile(r"\b(?:I|I'm|I've|I'd|I'll|my|me|mine|we|we're|we've|our|us)\b", re.I)
ANECDOTE = re.compile(r"\b(?:yesterday|last (?:week|month|year|night)|this morning|years? ago|once|the other day|"
                      r"i (?:remember|recall|saw|heard|met|watched|felt|smelt|smelled|tasted)|when i was)\b|"
                      r"\b(?:smell|smelt|taste|tasted|sound of|felt like|the warmth|the cold)\b", re.I)
JOKE = re.compile(r"\b(?:walks? into a bar|ha ?ha+|lol|joking|just kidding|punchline|no pun intended)\b|\?!|!{2,}|"
                  r"[\U0001F300-\U0001FAFF]", re.I)


class CannotRun(Exception):
    pass


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def words(s):
    return [w for w in (re.sub(r"[^\w£$€%'’-]", "", t).lower() for t in s.split()) if w]


def matched(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(m.size for m in sm.get_matching_blocks()), sm.ratio()


def pair(src, drafts):
    """For each draft sentence the best source sentence index and its closeness, or None when nothing is close."""
    sw = [words(s) for s in src]
    out = []
    for d in drafts:
        dw = words(d)
        best = max(((matched(w, dw)[1], i) for i, w in enumerate(sw)), default=(0, None))
        out.append((best[1], best[0]) if best[0] >= SAME else (None, best[0]))
    return out


def spans(text, rx):
    return [re.sub(r"\s+", "", m.group(0)).lower().strip(".,") for m in rx.finditer(text)]


def quoted(text):
    return [next(g for g in m.groups() if g).strip().lower() for m in QUOTED.finditer(text)]


def check(source, draft, tier=DEFAULT_TIER):
    src, dr = sentences(source), sentences(draft)
    sw, dw = words(source), words(draft)
    kept_n, _ = matched(sw, dw)
    kept = round(100 * kept_n / len(sw)) if sw else 100
    links = pair(src, dr)
    changed, added, flags = [], [], []
    used = set()

    for d, (i, close) in zip(dr, links):
        if i is None:
            added.append(d)
            continue
        used.add(i)
        s = src[i]
        if s == d:
            continue
        m, _ = matched(words(s), words(d))
        share = 1 - m / max(len(words(s)), len(words(d)), 1)
        changed.append({"before": s, "after": d, "share_changed": round(share, 2)})
        if tier in LIMIT and share > LIMIT[tier]:
            flags.append({"rule": "over-limit", "level": "amber", "text": d,
                          "why": f"{round(100 * share)} percent of the words changed; tier {tier} allows about "
                                 f"{round(100 * LIMIT[tier])}."})
    removed = [s for i, s in enumerate(src) if i not in used]

    if tier == 1 and re.sub(r"\s+", " ", source).strip() != re.sub(r"\s+", " ", draft).strip():
        flags.append({"rule": "tier-1", "level": "red", "text": "", "why": "Tier 1 is verbatim and the text differs."})
    for kind, rx, get in (("number", NUMBER, lambda t: spans(t, NUMBER)), ("quote", QUOTED, quoted)):
        missing = [x for x in get(source) if x not in get(draft)]
        for x in missing:
            flags.append({"rule": f"{kind}-changed", "level": "red", "text": x,
                          "why": f"A {kind} in the source is missing or changed in the draft. It stays verbatim."})
    for m in MODALS:
        rx = re.compile(rf"\b{m}\b", re.I)
        if len(rx.findall(source)) > len(rx.findall(draft)):
            flags.append({"rule": "modal-changed", "level": "amber", "text": m,
                          "why": "A modal or hedge word in the source is fewer in the draft. It stays verbatim."})
    for s in removed:
        flags.append({"rule": "removed", "level": "amber", "text": s,
                      "why": "A source sentence has no match in the draft. Cut on purpose?"})
    known_names = set(spans(source, NAME))
    for s in added:
        why = []
        if NUMBER.search(s) and not set(spans(s, NUMBER)) <= set(spans(source, NUMBER)):
            why.append("a number the source does not have")
        if set(spans(s, NAME)) - known_names:
            why.append("a name the source does not have")
        if FIRST.search(s) and ANECDOTE.search(s):
            why.append("a first-person anecdote or sensory line")
        if JOKE.search(s):
            why.append("a joke-shaped line")
        hard = [w for w in why if not w.startswith("a name")]
        flags.append({"rule": "added", "level": "red" if hard else "amber", "text": s,
                      "why": ("Added sentence with " + ", ".join(why) + ".") if why else
                             "Added sentence. Not in the source."})
    edited = {c["after"] for c in changed} | set(added)
    for para in re.split(r"\n\s*\n", draft):
        n = sum(1 for s in sentences(para) if s in edited)
        if n > EDIT_CAP:
            flags.append({"rule": "edit-cap", "level": "amber", "text": sentences(para)[0],
                          "why": f"{n} edits in one paragraph; the cap is {EDIT_CAP} for the first run."})
    if tier >= 3 and sw and abs(len(dw) - len(sw)) / len(sw) > LENGTH_BAND:
        flags.append({"rule": "length", "level": "amber", "text": f"{len(sw)} words to {len(dw)}",
                      "why": f"Length is outside plus or minus {round(100 * LENGTH_BAND)} percent of the source."})
    if tier >= 3 and changed and not any(f["level"] in ("red", "amber") for f in flags):
        flags.append({"rule": "reworked", "level": "amber", "text": "",
                      "why": f"{len(changed)} sentences reworded. Read the list."})

    level = ("red" if any(f["level"] == "red" for f in flags) else
             "amber" if flags or added else "green")
    return {"tier": tier, "status": level, "kept_percent": kept, "sentences_changed": len(changed),
            "sentences_added": len(added), "flags": flags, "changed": changed, "added": added,
            "not_run": NOT_RUN}


def read(path):
    p = Path(path)
    if not p.is_file():
        raise CannotRun(f"not found: {path}")
    text = p.read_text(encoding="utf-8")
    if not text.strip():
        raise CannotRun(f"{path} is empty. This is unknown, not clean.")
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source")
    ap.add_argument("draft")
    ap.add_argument("--tier", type=int, choices=(1, 2, 3, 4), default=DEFAULT_TIER)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        rep = check(read(a.source), read(a.draft), a.tier)
    except CannotRun as e:
        print(f"reword-report: could not run. {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rep, indent=2))
        return 0
    print(f"{rep['status'].upper()}  tier {rep['tier']}  {rep['kept_percent']}% of the source kept  "
          f"{rep['sentences_added']} added  {len(rep['flags'])} flags")
    for c in rep["changed"]:
        print(f"  changed\n    before: {c['before']}\n    after:  {c['after']}")
    for s in rep["added"]:
        print(f"  added   {s}")
    for f in rep["flags"]:
        print(f"  {f['level']}  {f['rule']}  {f['text']}  {f['why']}".replace("  ", " ", 1))
    print("\nNot run: " + "; ".join(rep["not_run"]) + ".")
    print(f"Nothing here is applied. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
