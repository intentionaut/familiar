#!/usr/bin/env python3
"""Measure how much of a published piece is the writer's own sentences. It
reports; there is no gate and no threshold, and it changes nothing.

Familiar drafts from her outline and notes, so a piece can reach `final.md`
with most of its sentences written by the model and only nodded through. This
counts, so the trend is a fact she can see rather than a feeling. It does not
say what the number should be. The data decides later whether the writer-first
path should be the default.

For each sentence of `final.md`:

  kept     it is a sentence the model wrote, unchanged (case and punctuation aside)
  edited   it started as a sentence the model wrote and she changed some words:
           it still shares most of its word order with one
  hers     nothing the model wrote is close: she wrote it, or rewrote it past
           recognition

Her share is `hers` over all sentences. The share counting her edits too
(`hers` plus `edited`) is shown beside it. A sentence under three words is not
counted, and headings, code, block quotes and front matter are not read.

What counts as "the model wrote":

  model-first   the usual path: the sentences of `draft.md`
  writer-first  `draft.md` has `drafted_by: writer` in its front matter: she wrote
                the first draft, so the model's sentences are only the rewrites it
                suggested in `edits/*.md` (`Fix:` and `Rewrite:` lines)

Usage:
  her-share.py <piece folder> [--json]
  her-share.py --trend [<pieces folder> ...] [--json]     every piece with a final.md, oldest first

With no folder, `--trend` reads the pieces folders from paths.py. A piece with
no `final.md` has no published version to measure: it is listed as not
measured, never as zero.

Exit 0 on a report. Exit 2 when it could not run: the folder or `draft.md` is
missing, or a single piece has no `final.md`.
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paths  # noqa: E402

MIN_WORDS = 3            # a shorter sentence is not counted
KEPT = 0.95              # word-order match at or above this: the same sentence
EDITED = 0.6             # at or above this, and below KEPT: she changed some words
CANNOT_TELL = ("Cannot tell: whether a sentence she kept was one she would have written herself, or whether an edit "
               "was large or small in meaning. This counts sentences, not authorship.")


class CannotRun(Exception):
    pass


def words(s):
    s = s.replace("’", "'").replace("‘", "'")
    return re.sub(r"[^\w' ]+", " ", re.sub(r"[*_`]", "", s.lower())).split()


def blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(re.findall(r"^(\w+):\s*(.*?)\s*$", m.group(1), re.M)) if m else {}


def prose_sentences(text):
    text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", blank, text, flags=re.M | re.S)
    out = []
    for line in text.splitlines():
        if re.match(r"\s{0,3}(#{1,6}\s|>)", line):
            continue
        line = re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", line)
        for m in re.finditer(r"[^.!?]+[.!?]*", line):
            s = m.group(0).strip()
            if len(words(s)) >= MIN_WORDS:
                out.append(s)
    return out


def suggested_rewrites(folder):
    """The sentences of every `Fix:` and `Rewrite:` line in the piece's edit reports."""
    out = []
    for f in sorted((folder / "edits").glob("*.md")) if (folder / "edits").is_dir() else []:
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*(?:[-*]\s+)?(?:\*\*)?(?:Fix|Rewrite)(?:\*\*)?\s*:(?:\*\*)?\s*(.*)$", line, re.I)
            if m:
                out += prose_sentences(re.sub(r'^["“](.*)["”]$', r"\1", m.group(1).strip().strip("`")))
    return out


def model_sentences(folder):
    """(sentences the model wrote, her own draft sentences or [], path taken)."""
    draft = (folder / "draft.md").read_text(encoding="utf-8")
    if frontmatter(draft).get("drafted_by", "").strip("\"' ").lower() == "writer":
        return suggested_rewrites(folder), prose_sentences(draft), "writer-first"
    return prose_sentences(draft), [], "model-first"


def measure(folder):
    folder = Path(folder)
    if not (folder / "draft.md").is_file():
        raise CannotRun(f"no draft.md in {folder}")
    if not (folder / "final.md").is_file():
        raise CannotRun(f"no final.md in {folder}: there is no published version to measure")
    model, own, path = model_sentences(folder)
    mw, ow = [words(s) for s in model], [words(s) for s in own]
    final = prose_sentences((folder / "final.md").read_text(encoding="utf-8"))
    counts = {"kept": 0, "edited": 0, "hers": 0}

    def best(fw, pool):
        return max((SequenceMatcher(None, fw, m, autojunk=False).ratio() for m in pool), default=0.0)

    for s in final:
        fw = words(s)
        m = best(fw, mw)
        # Writer-first: a sentence that is closer to her own draft than to a rewrite the model suggested is hers.
        if ow and best(fw, ow) >= m:
            m = 0.0
        counts["kept" if m >= KEPT else "edited" if m >= EDITED else "hers"] += 1
    n = len(final)
    return {"piece": folder.name, "path": path, "sentences": n, **counts,
            "her_share": round(counts["hers"] / n, 3) if n else None,
            "her_share_with_edits": round((counts["hers"] + counts["edited"]) / n, 3) if n else None}


def pct(x):
    return "n/a" if x is None else f"{x:.0%}"


def trend(folders):
    rows, skipped = [], []
    for base in folders:
        for p in sorted(Path(base).glob("*/")):
            if not (p / "draft.md").is_file():
                continue
            if not (p / "final.md").is_file():
                skipped.append(p.name)
                continue
            rows.append(measure(p))
    rows.sort(key=lambda r: r["piece"])
    return rows, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folders", nargs="*")
    ap.add_argument("--trend", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.trend:
            folders = [Path(f) for f in a.folders] or paths.pieces_dirs()
            missing = [str(f) for f in folders if not f.is_dir()]
            if missing:
                raise CannotRun(f"not found: {', '.join(missing)}")
            rows, skipped = trend(folders)
            res = {"pieces": rows, "not_measured": skipped}
        elif len(a.folders) == 1:
            res = measure(a.folders[0])
        else:
            raise CannotRun("give one piece folder, or --trend")
    except CannotRun as e:
        print(f"her-share: could not run. {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    if not a.trend:
        print(f"{res['piece']} ({res['path']}): {res['sentences']} sentences in final.md\n"
              f"  her share {pct(res['her_share'])}  (hers {res['hers']}, edited from the draft {res['edited']}, "
              f"kept from the draft {res['kept']})\n  counting her edits {pct(res['her_share_with_edits'])}")
    else:
        print(f"{'piece':44} {'path':13} {'sentences':>9} {'her share':>10} {'with edits':>11}")
        for r in res["pieces"]:
            print(f"{r['piece'][:44]:44} {r['path']:13} {r['sentences']:>9} {pct(r['her_share']):>10} {pct(r['her_share_with_edits']):>11}")
        shares = [r["her_share"] for r in res["pieces"] if r["her_share"] is not None]
        if len(shares) >= 2:
            print(f"\n{len(shares)} pieces measured. Latest {pct(shares[-1])}; mean of the earlier ones {pct(sum(shares[:-1]) / len(shares[:-1]))}.")
        elif not shares:
            print("\nNo piece has both a draft.md and a final.md yet.")
        if res["not_measured"]:
            print(f"Not measured, no final.md: {', '.join(res['not_measured'])}")
    print(f"\nNo gate and no threshold. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
