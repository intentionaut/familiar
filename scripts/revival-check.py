#!/usr/bin/env python3
"""Flag a stage's output that brings back something the writer already killed.
It flags; it never edits and never blocks.

"Kills stay killed" is a rule a model is told to follow. This checks it. Three
kinds of kill are read, and each flag carries the original kill and its reason,
so she can say whether the evidence changed:

  cut      an entry in the piece's `cuts.md` flagged `dead`
  option   an option the writer did not choose, in any option set of the piece
           that records a `Chosen:` line (an edit report, `social.md`,
           `options.md`)
  rule     a row of the house's `rejected-rules.md`: a rule she turned down

A revival is an output sentence that holds most of a kill's content words (at
least three, or all of them in a short kill), however it is reworded. Text the
kill and the chosen option share is not a revival. The record itself is not
output: `cuts.md`, and an option set that already has a `Chosen:` line, are
masked when they sit in a file being checked, so a decided set is never read
back as a proposal. An option set still waiting on her is output, and is read.

Usage:
  revival-check.py <output file> [<output file> ...] [--piece <piece folder>] [--house <knowledge folder>] [--json]

`--piece` names the folder whose cuts and option sets are the kills; without
it only rejected rules are read. `--house` names the knowledge folder; without
it the house is resolved the way every stage resolves it, and the shipped
templates are never read as her rejections.

Exit 0 whether or not anything is flagged (a flag is advice, not a stop).
Exit 2 when it could not run: a file or folder is missing, or an option set
records a `Chosen:` line that names no option. That is unknown, never clean.
Where rejected rules were not read (no house), the report says so.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paths  # noqa: E402

QUESTION = "did the evidence change?"
CANNOT_TELL = ("Cannot tell: whether the evidence has changed since the kill, or whether this is a different thing "
               "that uses the same words. Those are the writer's call.")
COVER = 0.6              # share of a kill's content words one output sentence holds
MIN_SHARED = 3           # and at least this many (all of them, for a short kill)
MIN_OUT = 3              # an output sentence with fewer content words is not read
STOP = set("a an the and or but of to in on at for with by from as is are was were be been it its this that i we "
           "you he she they so do did does have has had not no if then than there their our my your".split())


class CannotRun(Exception):
    pass


def words(s):
    s = s.replace("’", "'").replace("‘", "'")
    return re.sub(r"[^\w' ]+", " ", re.sub(r"[*_`]", "", s.lower())).split()


def content(s):
    return {w for w in words(s) if w not in STOP}


def sentences(text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        line = re.sub(r"^\s*(#{1,6}|[-*+]|\d+[.)]|>)\s*", "", line)
        for m in re.finditer(r"[^.!?]+[.!?]*", line):
            if m.group(0).strip():
                out.append((n, m.group(0).strip()))
    return out


def blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


# -- the kills -----------------------------------------------------------------------------------------------------
def option_sets(text):
    """[(start, end, title, chosen letters or None, {letter: (label, text)}, because)] for each `## Option set:` block."""
    sets = []
    for m in re.finditer(r"^## Option set:(.*?)(?=^## |\Z)", text, re.M | re.S):
        block, title = m.group(0), m.group(1).splitlines()[0].strip() if m.group(1).strip() else ""
        opts = {}
        for o in re.finditer(r"^###\s+([A-Z])\.\s*(.*?)\n(.*?)(?=^###\s|\Z)", block, re.M | re.S):
            body = "\n".join(l for l in o.group(3).splitlines() if not re.match(r"\s*(Buys|Costs|Chosen|Because)\s*:", l, re.I))
            opts[o.group(1)] = (o.group(2).strip(), body.strip())
        c = re.search(r"^\s*Chosen\s*:\s*(.*)$", block, re.M | re.I)
        chosen = None
        if c:
            chosen = [x for x in re.findall(r"\b([A-Z])\b", c.group(1))]
        b = re.search(r"^\s*Because\s*:\s*(.+)$", block, re.M | re.I)
        sets.append((m.start(), m.end(), title, chosen, opts, b.group(1).strip() if b else None))
    return sets


def kills_from_piece(folder):
    """([kill], [problem]). A kill is {kind, kill, why, where, texts}; texts are what a revival would repeat."""
    kills, problems = [], []
    cuts = folder / "cuts.md"
    if cuts.is_file():
        raw = cuts.read_text(encoding="utf-8")
        for block in re.split(r"^###\s+", raw, flags=re.M)[1:]:
            head, _, rest = block.partition("\n")
            flag = re.search(r"^\s*(?:\*\*)?Flag(?:\*\*)?:\s*(\w+)", rest, re.M | re.I)
            if not flag or flag.group(1).lower() != "dead":
                continue
            why = re.search(r"^\s*(?:\*\*)?Why(?:\*\*)?:\s*(.+)", rest, re.M | re.I)
            material = "\n".join(l for l in rest.splitlines() if not re.match(r"\s*(?:\*\*)?(From|Why|Flag)(?:\*\*)?:", l, re.I))
            kills.append({"kind": "cut", "kill": head.strip(), "why": why.group(1).strip() if why else "(no reason recorded)",
                          "where": "cuts.md", "texts": [head.strip()] + [s for _, s in sentences(material)]})
    for f in sorted(folder.rglob("*.md")):
        for _, _, title, chosen, opts, because in option_sets(f.read_text(encoding="utf-8")):
            if chosen is None:
                continue
            if not chosen or not set(chosen) & set(opts):
                problems.append(f"{f.relative_to(folder)}: option set '{title}' has a Chosen line that names none of its options")
                continue
            keep = [s for L in chosen if L in opts for _, s in sentences(opts[L][1])]
            for L, (label, body) in opts.items():
                if L in chosen:
                    continue
                texts = [label] + [s for _, s in sentences(body) if not any(_similar(s, k) for k in keep)]
                kills.append({"kind": "option", "kill": f"{title}: option {L}, {label}",
                              "why": f"not chosen ({because})" if because else "not chosen",
                              "where": str(f.relative_to(folder)), "texts": texts})
    return kills, problems


def kills_from_rules(path):
    kills = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
            continue
        kills.append({"kind": "rule", "kill": cells[1], "why": cells[2], "where": "rejected-rules.md", "texts": [cells[1]]})
    return kills


# -- the check -----------------------------------------------------------------------------------------------------
def _similar(a, b):
    ca, cb = content(a), content(b)
    return bool(ca and cb) and len(ca & cb) / min(len(ca), len(cb)) >= 0.8


def masked(text):
    """The output with front matter, code and the record (decided option sets) blanked, line numbers kept."""
    text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", blank, text, flags=re.M | re.S)
    for start, end, _, chosen, _, _ in reversed(option_sets(text)):
        if chosen is not None:
            text = text[:start] + re.sub(r"[^\n]", " ", text[start:end]) + text[end:]
    return text


def check(text, kills):
    sents = [(n, s) for n, s in sentences(masked(text)) if len(content(s)) >= MIN_OUT]
    flags = []
    for k in kills:
        best = None
        for sig in k["texts"]:
            cs = content(sig)
            if len(cs) < 2:
                continue
            need = min(MIN_SHARED, len(cs))
            for n, s in sents:
                shared = len(cs & content(s))
                score = shared / len(cs)
                if shared >= need and score >= COVER and (best is None or score > best[0]):
                    best = (score, n, s)
        if best:
            flags.append({"line": best[1], "sentence": best[2], "kind": k["kind"], "kill": k["kill"], "why_killed": k["why"],
                          "recorded_in": k["where"], "similarity": round(best[0], 2), "question": QUESTION})
    return sorted(flags, key=lambda f: f["line"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("outputs", nargs="*")
    ap.add_argument("--piece")
    ap.add_argument("--house")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if not a.outputs:
            raise CannotRun("no output given")
        missing = [f for f in a.outputs if not Path(f).is_file()]
        if a.piece and not Path(a.piece).is_dir():
            missing.append(a.piece)
        if a.house and not Path(a.house).is_dir():
            missing.append(a.house)
        if missing:
            raise CannotRun(f"not found: {', '.join(missing)}")
        kills, problems, notes = [], [], []
        if a.piece:
            kills, problems = kills_from_piece(Path(a.piece))
            notes.append(f"piece: {a.piece} ({len(kills)} kills: "
                         f"{sum(k['kind'] == 'cut' for k in kills)} dead cuts, {sum(k['kind'] == 'option' for k in kills)} rejected options)")
        else:
            notes.append("piece: not given, cuts and rejected options not read")
        house, whose = (Path(a.house), "given") if a.house else paths.knowledge_dir()
        rules_file = house / "rejected-rules.md"
        if whose == "the shipped templates":
            notes.append("rejected rules: not checked (no house resolved; the shipped template is blank)")
        elif rules_file.is_file():
            rules = kills_from_rules(rules_file)
            kills += rules
            notes.append(f"rejected rules: {rules_file} ({len(rules)} read)")
        else:
            notes.append(f"rejected rules: no rejected-rules.md in {house} (none recorded)")
        if problems:
            raise CannotRun("; ".join(problems) + ". This is unknown, not clean.")
        report = {}
        for f in a.outputs:
            if Path(f).name == "cuts.md":
                notes.append(f"{f}: the record of the cuts, not a stage's output, so not checked")
                report[f] = []
            else:
                report[f] = check(Path(f).read_text(encoding="utf-8"), kills)
    except CannotRun as e:
        print(f"revival-check: could not run. {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"read": notes, "files": report}, indent=2))
        return 0
    print("\n".join(notes))
    for f, flags in report.items():
        print(f"\n{f}: {len(flags)} revival{'s' if len(flags) != 1 else ''}")
        for g in flags:
            print(f"  line {g['line']}  {g['kind']}  \"{g['sentence']}\"\n"
                  f"    killed: {g['kill']} ({g['recorded_in']}). Why: {g['why_killed']}. {g['question']}")
    print(f"\nNothing here is applied. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
