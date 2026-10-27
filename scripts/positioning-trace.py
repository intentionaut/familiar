#!/usr/bin/env python3
"""Report which lines of a positioning one-pager trace to a cited source. It
reports; it never edits, rewrites, blocks or approves, and it never touches the
file it reads. Issue #563.

Experience-flags asks where a first-person line came from. This asks the same
of a positioning document: every factual or comparative line should cite a
source, and the source it cites should say it. Each line gets one status:

  traced     cites a source, and a sentence of that source holds the claim
  untraced   cites nothing
  mis-cited  cites an id that was not given, or cites a source that does not
             say it (a figure that differs counts as not saying it)

A citation is `[src: S1]` or `[src: S1, S2]` on the line. Sources are named on
the command line as `--source S1=notes/pricing.md`, or by `--sources-dir`,
where each file's stem is its id. For an untraced or mis-cited line the report
also says which given source does hold it, so she can decide whether to cite
that one. Whether the cited source is the right evidence stays her call.

Not read, and left exactly as written: front matter, headings, code, block
quotes, anything inside quotation marks, questions, a sentence that already
carries an `[ASK THE WRITER` or `[NEEDS SOURCE` bracket, and fragments of fewer
than three content words. The report counts what it did not read.

`--anchor FILE` is her buyer-belief line. Each line read is also marked as
sharing words with it or not. That is a hint to look, not a verdict.

Usage:
  positioning-trace.py <one-pager> --source ID=FILE [--source ...] [--sources-dir DIR] [--anchor FILE] [--json]

Exit 0 whether or not anything is untraced (a flag is advice, not a stop).
Exit 2 when it could not run: a file is missing, a source holds nothing to
trace against, or the one-pager holds no line to read. That is unknown, never
clean.
"""
import argparse
import importlib.util
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("experience_flags", HERE / "experience-flags.py")
ef = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ef)

CANNOT_TELL = ("Cannot tell: whether the source is the right evidence, whether a paraphrase keeps the meaning, "
               "or whether a line is true. Those are the writer's call.")
MIN_CONTENT = 3          # fewer content words than this is a fragment, not a claim
MIN_ANCHOR_SHARED = 2    # content words a line shares with the buyer-belief line to be marked as linked
CITE = re.compile(r"\[src:\s*([^\]]*)\]", re.I)
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
SHAPES = (
    ("figure", re.compile(r"\d")),
    ("comparative", re.compile(r"\b(?:more|less|fewer|than|faster|slower|better|worse|cheaper|higher|lower|"
                               r"bigger|smaller|most|least|best|only|unlike|versus|vs|instead of)\b|\w+er than", re.I)),
    ("absolute", re.compile(r"\b(?:every|all|none|never|always|no one|nobody|everyone|any)\b", re.I)),
)


class CannotRun(Exception):
    pass


def numbers(s):
    return {n.replace(",", "").rstrip(".") for n in NUMBER.findall(s.replace("’", "'"))}


def claim_sentences(text):
    """(line number, sentence, citations) for each sentence read; plus a count of what was not read."""
    body = ef.readable(text)
    out, skipped = [], {"fragment": 0, "question": 0, "bracket": 0}
    for n, line in enumerate(body.splitlines(), 1):
        pieces = []
        for s in re.split(r"(?<=[.!?])\s+", line.strip()):
            if pieces and re.match(r"\[(?:src:|ASK THE WRITER|NEEDS SOURCE)", s, re.I):
                # "... 5 days. [src: S1]": a trailing citation or bracket belongs to the sentence before
                pieces[-1] += " " + s
            elif s.strip():
                pieces.append(s)
        for s in pieces:
            if ef.BRACKET.search(s):
                skipped["bracket"] += 1
                continue
            cites = [c.strip() for m in CITE.finditer(s) for c in m.group(1).split(",") if c.strip()]
            plain = CITE.sub(" ", s).strip()
            if plain.endswith("?"):
                skipped["question"] += 1
                continue
            if len(ef.content(plain)) < MIN_CONTENT:
                skipped["fragment"] += 1
                continue
            out.append((n, plain, cites))
    return out, skipped


def supports(sentence, source_sentence):
    """Does one source sentence hold the claim? Same measure experience-flags uses, plus: every figure must match."""
    mine, sw = ef.content(sentence), ef.words(sentence)
    shared = len(mine & ef.content(source_sentence))
    close = (mine and shared / len(mine) >= ef.COVER and shared >= ef.MIN_SHARED) or \
        SequenceMatcher(None, sw, ef.words(source_sentence), autojunk=False).ratio() >= ef.RATIO
    return bool(close) and numbers(sentence) <= numbers(source_sentence)


def best(sentence, source_sents):
    for s in source_sents:
        if supports(sentence, s):
            return s
    return None


def check(onepager, sources, anchor=None):
    """sources: {id: [sentences]}. Returns (lines, skipped)."""
    claims, skipped = claim_sentences(onepager)
    anchor_words = ef.content(anchor) if anchor else None
    lines = []
    for n, s, cites in claims:
        quote = {c: best(s, sources[c]) for c in cites if c in sources}
        unknown = [c for c in cites if c not in sources]
        held = [c for c in cites if quote.get(c)]
        elsewhere = [i for i, ss in sources.items() if i not in cites and best(s, ss)]
        if held and not unknown:
            status, why = "traced", ""
        elif not cites:
            status, why = "untraced", "cites no source"
        elif unknown and not held:
            status, why = "mis-cited", f"cites {', '.join(unknown)}, which was not given"
        elif held:
            status, why = "mis-cited", f"cites {', '.join(unknown)}, which was not given (the others hold it)"
        else:
            status, why = "mis-cited", f"{', '.join(cites)} does not say this"
        row = {"line": n, "sentence": s, "status": status, "cites": cites,
               "shapes": [name for name, rx in SHAPES if rx.search(s)],
               "quote": {c: q for c, q in quote.items() if q}, "why": why}
        if status != "traced" and elsewhere:
            row["could_cite"] = {i: best(s, sources[i]) for i in elsewhere}
        if anchor_words is not None:
            row["anchor"] = len(ef.content(s) & anchor_words) >= MIN_ANCHOR_SHARED
        lines.append(row)
    return lines, skipped


def load_sources(pairs, folder):
    files = {}
    for p in pairs:
        sid, sep, path = p.partition("=")
        if not sep or not sid.strip() or not path.strip():
            raise CannotRun(f"--source wants ID=FILE, got {p!r}")
        files[sid.strip()] = Path(path)
    if folder:
        d = Path(folder)
        if not d.is_dir():
            raise CannotRun(f"not found: {folder}")
        for f in sorted(d.glob("*.md")) + sorted(d.glob("*.txt")):
            files.setdefault(f.stem, f)
    if not files:
        raise CannotRun("give at least one --source ID=FILE or --sources-dir")
    missing = [str(f) for f in files.values() if not f.is_file()]
    if missing:
        raise CannotRun(f"not found: {', '.join(missing)}")
    sources = {i: ef.source_sentences(f.read_text(encoding="utf-8")) for i, f in files.items()}
    empty = [i for i, ss in sources.items() if not ss]
    if empty:
        raise CannotRun(f"source {', '.join(empty)} holds no sentences to trace against. This is unknown, not clean.")
    return files, sources


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("onepager", nargs="?", help="the positioning one-pager (markdown)")
    ap.add_argument("--source", action="append", default=[], help="ID=FILE, a source a line may cite")
    ap.add_argument("--sources-dir", help="a folder of sources; each file's stem is its id")
    ap.add_argument("--anchor", help="the buyer-belief line, to mark which lines share words with it")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if not a.onepager:
            raise CannotRun("give the one-pager")
        op = Path(a.onepager)
        if not op.is_file():
            raise CannotRun(f"not found: {op}")
        files, sources = load_sources(a.source, a.sources_dir)
        anchor = None
        if a.anchor:
            if not Path(a.anchor).is_file():
                raise CannotRun(f"not found: {a.anchor}")
            anchor = Path(a.anchor).read_text(encoding="utf-8")
            if not ef.content(anchor):
                raise CannotRun("the anchor holds no words to compare against. This is unknown, not clean.")
        lines, skipped = check(op.read_text(encoding="utf-8"), sources, anchor)
        if not lines:
            raise CannotRun("the one-pager holds no line to read. This is unknown, not clean.")
    except CannotRun as e:
        print(f"positioning-trace: could not run. {e}", file=sys.stderr)
        return 2
    counts = {k: sum(1 for r in lines if r["status"] == k) for k in ("traced", "untraced", "mis-cited")}
    if a.json:
        print(json.dumps({"onepager": str(op), "sources": {i: str(f) for i, f in files.items()},
                          "counts": counts, "not_read": skipped, "lines": lines}, indent=2))
        return 0
    print(f"one-pager: {op}\nsources: {', '.join(f'{i}={f}' for i, f in files.items())}")
    print(f"\n{len(lines)} lines read: {counts['traced']} traced, {counts['untraced']} untraced, "
          f"{counts['mis-cited']} mis-cited. Not read: {sum(skipped.values())} "
          f"({skipped['fragment']} fragments, {skipped['question']} questions, {skipped['bracket']} already bracketed).")
    for r in lines:
        tag = f"  [{'+'.join(r['shapes'])}]" if r["shapes"] else ""
        print(f"\n  line {r['line']}  {r['status'].upper()}{tag}  \"{r['sentence']}\"")
        if r["why"]:
            print(f"    {r['why']}")
        for c, q in r["quote"].items():
            print(f"    {c}: \"{q}\"")
        for i, q in r.get("could_cite", {}).items():
            print(f"    {i} holds it: \"{q}\"")
        if "anchor" in r and not r["anchor"]:
            print("    anchor: shares no words with the buyer-belief line")
    print(f"\nNothing here is applied; the one-pager is untouched. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
