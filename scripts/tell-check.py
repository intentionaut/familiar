#!/usr/bin/env python3
"""Flag the phrases knowledge/style-rules.md names, the writer's own kills, and
forced groups of three. It flags; it never edits and never blocks.

The mechanical half of the AI-tell sweep in `draft` and `line-edit`. Every flag
is a question, "does it earn its place?", not a verdict: a word on the list may
be the writer's own, a term of art, or doing real work, and this cannot tell.

  rule <n>   a phrase quoted in style-rules.md pattern <n>, or in one of
             Familiar's own tells. Read from the house copy of style-rules.md,
             so a phrase added there is checked here with no release.
  kill       a phrase or pattern from the writer's kill list (`killed.md`)
  triplet    a forced group of three (pattern 6): "a, b and c" in one sentence,
             a list of exactly three, or three very short sentences in a row

Nothing is flagged inside code, quotation marks, a heading, a block quote or a
link address (style-rules.md: "Never flag a watched phrase inside a quotation,
a title or a proper name"). A pattern marked *Weak alone* is only flagged when
another tell shares the paragraph.

The kill list is found at, in order: --kills, FAMILIAR_KILLS, `kills = ` in
`.familiar`, then killed.md in the knowledge folder. One rule per line under
`## Killed`: `- phrase `the words` : <note>` matches whole words in any case,
`- pattern <name> `<regular expression>` : <note>` is matched in any case.
Lines under `## Retired` are the record and are not applied. With none of those set and no killed.md, kills are
reported as not checked. A kill list that was named and cannot be read is
unknown, never clean.

Usage:
  tell-check.py <file> [<file> ...] [--kills killed.md] [--json]

Exit 0 whether or not anything is flagged (a flag is advice, not a stop).
Exit 2 when it could not run: a file is missing, a named kill list cannot be
read, or style-rules.md no longer has the patterns this reads.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paths  # noqa: E402

QUESTION = "does it earn its place?"
TRIPLE = "does each one add a distinct idea?"
CANNOT_TELL = ("Cannot tell: whether a flagged word is a term of art, a quotation the masks missed, "
               "or the writer's own choice. Those are the writer's call.")

# The numbered patterns whose quoted phrases are literal enough to match. The
# rest (templates such as "not X but Y", formatting, examples of a shape) are
# for the editor's judgement and are not read here.
NUMBERED = (3, 4, 5, 9, 12, 13, 14, 15, 16, 17, 18, 22, 23)
# Familiar's own tells, by the start of their bold lead, read the same way.
OWN = ("Announcing evidence before presenting it", "A decisive verb pointed at a vague",
       '"Whether you\'re X, Y, or Z"')
MAX_WORDS = 5           # a longer quote is an example sentence, not a phrase to match
# Quoted in the rules as a fix or an example of a guess, not as a tell.
NOT_TELLS = {"founded and conducts", "she likely grew up", "it", "honestly"}
# Single words from these patterns are tells only in some uses ("bolted onto a fact", "figurative", "use is, are
# and has"), which this cannot see, so they count as weak alone.
USE_DEPENDENT = (15, 16, 18)
SMALL = {"a", "an", "the", "in", "on", "of", "for", "to", "with", "by", "at", "from", "as", "into", "about"}
SHORT = 6               # words: three sentences this short in a row read as a triplet

_PHRASE = re.compile(r"^-\s+phrase\s+`([^`]+)`(.*)$")
_PATTERN = re.compile(r"^-\s+pattern\s+(\w+)\s+`([^`]+)`(.*)$")


class CannotRun(Exception):
    pass


# -- style-rules.md ------------------------------------------------------------------------------------------------
def _items(text):
    """{key: item text} for the numbered patterns and Familiar's own tells, whitespace collapsed."""
    m = re.search(r"^## AI-tell patterns to flag\s*$", text, re.M)
    if not m:
        raise CannotRun("style-rules.md has no '## AI-tell patterns to flag' section")
    section = re.split(r"^## ", text[m.end():], maxsplit=1, flags=re.M)[0]
    out = {}
    for n, body in re.findall(r"^(\d+)\. (.*?)(?=^\d+\. |^### |\Z)", section, re.M | re.S):
        out[int(n)] = " ".join(body.split())
    own = re.search(r"^### Familiar's own tells\s*$(.*?)(?=^### |\Z)", section, re.M | re.S)
    if own:
        for body in re.findall(r"^- (.*?)(?=^- |\Z)", own.group(1), re.M | re.S):
            out[" ".join(body.split())[:80]] = " ".join(body.split())
    return out


def _quoted(item):
    """The literal phrases quoted in one item: short, no template letters, no trailing ellipsis kept."""
    item = re.split(r"\bBefore:", item)[0]
    found = []
    for q in re.findall(r'"([^"]+)"', item):
        # Keep a closing "," "?" or "!": "Look," and "Honestly?" are openers; "look" and "honestly" are fine.
        q = re.split(r"\.\.\.|…", q)[0].strip().rstrip(".").strip()
        if not q or q.lower() in NOT_TELLS or re.search(r"\b[XYZN]\b", q) or len(q.split()) > MAX_WORDS:
            continue
        found.append(q)
    return found


def _overused_words(item):
    """Pattern 12's word bullets as [(word, weak)]: every comma or slash separated entry. A bullet that qualifies its
    words ("as filler", "used figuratively", a note in parentheses) is a tell only in some uses, so it counts as weak."""
    words = []
    for bullet in re.findall(r"- (.*?)(?= - |\Z)", item):
        qualified = "(" in bullet or re.search(r",\s*(as|used)\b", bullet) is not None
        bullet = re.sub(r"\([^)]*\)", "", bullet)
        if '"' in bullet:
            words += [(q, False) for q in _quoted(bullet)]
            continue
        for part in re.split(r"[,/]", bullet):
            part = part.strip()
            if not part or part.startswith(("as ", "used ", "keep ", "especially")):
                continue
            if len(part.split()) <= 3:
                words.append((part, qualified))
    return words


def read_rules(path):
    """[(rule label, phrase, weak)] from style-rules.md. Raises CannotRun when a pattern it reads has gone."""
    items = _items(Path(path).read_text(encoding="utf-8"))
    rules = []
    for n in NUMBERED:
        if n not in items:
            raise CannotRun(f"style-rules.md has no pattern {n}: the check would silently skip it")
        body = items[n]
        weak = "*Weak alone.*" in body
        if n == 12:
            phrases = [(p, w) for p, w in _overused_words(body)]
        else:
            phrases = [(p, weak or (n in USE_DEPENDENT and " " not in p)) for p in _quoted(body)]
        if not phrases:
            raise CannotRun(f"style-rules.md pattern {n} yields no phrases: its wording changed")
        rules += [(f"rule {n}", p, w) for p, w in phrases]
    for lead in OWN:
        key = next((k for k in items if isinstance(k, str) and lead in k), None)
        if key is None:
            raise CannotRun(f"style-rules.md has no own tell starting {lead!r}")
        rules += [("rule own", p, False) for p in _quoted(items[key])]
    seen, out = set(), []
    for r in rules:
        if r[1].lower() not in seen:
            seen.add(r[1].lower())
            out.append(r)
    return out


# -- the kill list -------------------------------------------------------------------------------------------------
def kill_source(explicit=None):
    """(path, named). `named` is True when something asked for this file, so a missing one is unknown, not absent."""
    for c in (explicit, os.environ.get("FAMILIAR_KILLS"), *paths.read_config().get("kills", [])):
        if c:
            return Path(c).expanduser(), True
    return paths.knowledge_dir()[0] / "killed.md", False


def read_kills(path):
    """[(rule, name, compiled)] from the `## Killed` section. A line that will not load stops the run."""
    kills, section = [], None
    for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        if section != "killed" or not line.startswith("- "):
            continue
        m = _PATTERN.match(line)
        if m:
            try:
                kills.append((f"kill {m.group(1)}", m.group(1), re.compile(m.group(2), re.I | re.M)))
            except re.error as e:
                raise CannotRun(f"{path}:{n}: pattern {m.group(1)!r} does not compile: {e}")
            continue
        m = _PHRASE.match(line)
        if m:
            # Whole words as the kill list's format defines them: a hyphen or apostrophe ends a word here.
            kills.append(("kill", m.group(1), re.compile(rf"(?<!\w){re.escape(m.group(1))}(?!\w)", re.I)))
            continue
        raise CannotRun(f"{path}:{n}: not a phrase or pattern line: {line}")
    return kills


# -- masking -------------------------------------------------------------------------------------------------------
def _blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


def masked(text):
    """The text with everything that must not be flagged blanked out, same length, so offsets and lines still hold."""
    text = re.sub(r"\A---\n.*?\n---\n", _blank, text, flags=re.S)          # front matter
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", _blank, text, flags=re.M | re.S)
    text = re.sub(r"`[^`\n]+`", _blank, text)
    text = re.sub(r"^\s{0,3}(#{1,6}\s|>).*$", _blank, text, flags=re.M)
    text = re.sub(r"\]\([^)]*\)|https?://\S+", _blank, text)
    text = re.sub(r'"[^"\n]*"|“[^”\n]*”', _blank, text)
    return text


def _word_rx(phrase):
    return re.compile(rf"(?<![\w'-]){re.escape(phrase)}(?![\w'-])", re.I)


# -- triplets ------------------------------------------------------------------------------------------------------
def _sentences(par):
    """(offset, sentence) pairs. A line break ends one too, so a byline or a list item never joins the next line."""
    return [(m.start(), m.group(0)) for m in re.finditer(r"[^.!?\n]+[.!?]?", par) if m.group(0).strip()]


def triplets(par, orig=None):
    """[(offset in par, match, why)] for forced groups of three in one paragraph. `par` is masked; `orig` is the
    same span unmasked, used to count words, since a masked quotation would otherwise make a sentence look short."""
    orig = par if orig is None else orig
    out = []
    for start, s in _sentences(par):
        for m in re.finditer(r",? (?:and|or) ", s):
            before, after = s[:m.start()], s[m.end():]
            pieces = before.split(",")
            if len(pieces) != 2:
                continue
            # The last item is short and ends the clause: "a, b and c." A list that runs on into more clause ("the
            # feature and the outcome had folded into one") is usually commas doing grammar, not a list of three.
            last = re.match(r"[\w'-]+(?: [\w'-]+){0,2}(?=\s*(?:[.,;:!?)]|$))", after)
            second = pieces[1].strip()
            if not last or not second or len(second.split()) > 4:
                continue
            lead = pieces[0].split()
            if not lead:
                continue
            # The first item is as long as the second. When the second opens with a small word ("in code") the first
            # must open the same way, or the sentence is a clause and a pair ("you can show it, in code and in use").
            first = lead[-len(second.split()):]
            if second.split()[0].lower() in SMALL and first[0].lower() != second.split()[0].lower():
                continue
            items = [" ".join(first), second, last.group(0)]
            if any(re.search(r"\d", i) for i in items) or all(i[:1].isupper() for i in items[1:]):
                continue
            out.append((start + len(s) - len(s.lstrip()), s.strip(), "three items in one sentence: " + TRIPLE))
            break
    run = [(st, s, len(orig[st:st + len(s)].split())) for st, s in _sentences(par)]
    for i in range(len(run) - 2):
        three = run[i:i + 3]
        if all(0 < n <= SHORT for _, _, n in three):
            if i + 3 < len(run) and run[i + 3][2] <= SHORT:
                continue  # four or more short sentences is a different shape
            if i > 0 and run[i - 1][2] <= SHORT:
                continue
            out.append((three[0][0] + len(three[0][1]) - len(three[0][1].lstrip()),
                        " ".join(s.strip() for _, s, _ in three), "three short sentences in a row: " + TRIPLE))
    return out


def list_triplets(text):
    """[(offset, first item, why)] for a bulleted or numbered list of exactly three."""
    out, block = [], []
    for m in re.finditer(r"^.*$", text, re.M):
        if re.match(r"\s{0,3}([-*+]|\d+[.)])\s+\S", m.group(0)):
            block.append(m)
            continue
        if len(block) == 3:
            out.append((block[0].start(), block[0].group(0).strip(), "a list of exactly three: " + TRIPLE))
        block = []
    if len(block) == 3:
        out.append((block[0].start(), block[0].group(0).strip(), "a list of exactly three: " + TRIPLE))
    return out


# -- the check -----------------------------------------------------------------------------------------------------
def _line(text, offset):
    return text.count("\n", 0, offset) + 1


def check(text, rules, kills):
    """Every flag in reading order: {line, rule, match, why}. Weak-alone hits only where another tell shares the paragraph."""
    view = masked(text)
    flags = []
    for label, phrase, weak in rules:
        for m in _word_rx(phrase).finditer(view):
            flags.append({"offset": m.start(), "rule": label, "match": text[m.start():m.end()], "weak": weak})
    for label, name, rx in kills or []:
        for m in rx.finditer(view):
            flags.append({"offset": m.start(), "rule": label, "match": text[m.start():m.end()], "weak": False})
    for off, first, why in list_triplets(view):
        flags.append({"offset": off, "rule": "triplet", "match": text[off:off + len(first)], "weak": False, "why": why})
    for pm in re.finditer(r"(?:[^\n]|\n(?!\s*\n))+", view):
        for off, s, why in triplets(pm.group(0), text[pm.start():pm.end()]):
            o = pm.start() + off
            flags.append({"offset": o, "rule": "triplet", "match": text[o:o + len(s)], "weak": False, "why": why})
    # One span named by both the writer's kill list and the rules is one flag, under her kill.
    flags.sort(key=lambda f: not f["rule"].startswith("kill"))
    seen, unique = set(), []
    for f in flags:
        key = (f["offset"], len(f["match"]))
        if key not in seen:
            seen.add(key)
            unique.append(f)
    flags = unique
    paragraphs = [(m.start(), m.end()) for m in re.finditer(r"(?:[^\n]|\n(?!\s*\n))+", text)]

    def para(off):
        return next((i for i, (a, b) in enumerate(paragraphs) if a <= off < b), -1)

    kept = []
    for f in flags:
        # Company is another phrase or kill; a triplet is a shape guess and does not vouch for a weak word.
        if f["weak"] and not any(g is not f and g["rule"] != "triplet" and para(g["offset"]) == para(f["offset"]) and g["offset"] != f["offset"]
                                 for g in flags):
            continue
        kept.append(f)
    kept.sort(key=lambda f: (f["offset"], f["rule"]))
    return [{"line": _line(text, f["offset"]), "rule": f["rule"], "match": f["match"],
             "why": f.get("why", QUESTION)} for f in kept]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--kills", help="the kill list to read (killed.md)")
    ap.add_argument("--rules", help="style-rules.md to read (default: the house copy)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.rules:
            rules_path, whose = Path(a.rules), "given"
        else:
            k, whose = paths.knowledge_dir()
            rules_path = k / "style-rules.md"
        if not rules_path.is_file():
            raise CannotRun(f"style-rules.md not found at {rules_path}")
        rules = read_rules(rules_path)
        kpath, named = kill_source(a.kills)
        if kpath.is_file():
            kills = read_kills(kpath)
            kill_line = f"kills: {kpath} ({len(kills)} read)"
        elif named:
            raise CannotRun(f"kill list named at {kpath} and not found. Kills were not checked; this is unknown, not clean.")
        else:
            kills = None
            kill_line = "kills: not checked (no kill list set; see --kills or FAMILIAR_KILLS)"
        missing = [f for f in a.files if not Path(f).is_file()]
        if missing:
            raise CannotRun(f"not found: {', '.join(missing)}")
    except CannotRun as e:
        print(f"tell-check: could not run. {e}", file=sys.stderr)
        return 2

    report = {"rules": {"file": str(rules_path), "from": whose, "phrases": len(rules)},
              "kills": {"file": str(kpath), "read": kills is not None, "count": len(kills or [])},
              "files": {}}
    for f in a.files:
        report["files"][f] = check(Path(f).read_text(encoding="utf-8"), rules, kills)
    if a.json:
        print(json.dumps(report, indent=2))
        return 0
    print(f"rules: {rules_path} ({whose}), {len(rules)} phrases")
    print(kill_line)
    for f, flags in report["files"].items():
        print(f"\n{f}: {len(flags)} flag{'s' if len(flags) != 1 else ''}")
        for g in flags:
            print(f"  line {g['line']}  {g['rule']}  \"{g['match']}\"  {g['why']}")
    print(f"\nEach flag asks a question; nothing here is applied. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
