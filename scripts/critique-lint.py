#!/usr/bin/env python3
"""Lint an editor's report for flattery and for findings that point at nothing.
It flags; it never edits and never blocks.

The anti-flattery rules ("no compliment sandwiches", "quote the draft verbatim")
are prose a model is told to follow. This reads the report it wrote and checks
two things a program can check:

  praise      a finding, a section or the whole report opens with praise or
              agreement ("Great opening", "You're right that", "I love this")
              and does not quote the line it praises. "This works" said once,
              specifically, is allowed: a praise sentence that quotes the line it
              is about passes.
  unquoted    a finding (a numbered heading with an Issue, Fix or Rewrite under
              it, or a `3a.` / `4.1` / `R2-3a.` heading) that quotes none of the
              draft's words: no `[line N] "..."`, no quotation of three words or
              more, no block quote.

It deliberately does not ask for "at least one problem". That rewards inventing
a fault where the draft is fine, which is flattery's twin. A report with no
findings is not flagged for having none.

Findings are read the way the editor stages write them: a `###` heading that
starts with a finding number, up to the next heading of its own level or
higher. The `####` option headings stay inside it. A plain `### 3. Critical
fixes` section heading is a section, not a finding.

Usage:
  critique-lint.py <report.md> [<report.md> ...] [--json]

Exit 0 whether or not anything is flagged (a flag is advice, not a stop).
Exit 2 when it could not run: a file is missing, or a report has Issue, Fix or
Rewrite lines and no finding it could read. That is unknown, never clean.
"""
import argparse
import json
import re
import sys
from pathlib import Path

CANNOT_TELL = ("Cannot tell: whether praise is earned, whether a quotation is the right line, or whether a "
               "finding is a real fault. Those are the writer's call.")
PRAISE_Q = "is it specific? Quote the line it is about, or cut it."
QUOTE_Q = "which line of the draft is this about? Quote it."

PRAISE = re.compile(
    r"^(?:(?:great|good|nice|lovely|excellent|brilliant|fantastic|wonderful|superb|terrific|awesome|amazing|"
    r"impressive|compelling|powerful|clever|strong|solid|beautiful(?:ly)?)\b"
    r"|love (?:this|that|it|the)\b|i (?:really |absolutely )?(?:like|love|enjoy|admire)\b|what an? \w+"
    r"|well done\b|well written\b|this is (?:a |an )?(?:really |very |truly |such a |such an )?(?:great|good|strong|"
    r"excellent|beautiful|compelling|powerful|brilliant|lovely|wonderful|solid|fantastic|promising)\b"
    r"|you(?:'re| are) (?:absolutely |completely |quite |entirely )?right\b|good (?:point|catch|call|question|instinct)\b"
    r"|(?:absolutely|agreed|exactly|certainly|of course|spot on)\s*[,.!]|i agree\b|fair point\b|thanks?\b|thank you\b|happy to\b)",
    re.I)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FINDING = re.compile(r"^(?:R\d+-\d+(?:[a-z]|\.\d+)?|\d+(?:[a-z]|\.\d+))[.)]?\s+(?=\S)")   # 3a. 4.1 R2-3a. R2-3.
NUMBERED = re.compile(r"^(?:R\d+-)?\d+[.)]\s+(?=\S)")                        # 3.  (a finding only with an Issue under it)
MARKER = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?(Issue|Fix|Rewrite|Why it matters)(?:\*\*)?\s*:", re.I)
LABEL = re.compile(r"^\s*(?:[-*>]\s+)*(?:\*\*)?(?:Issue|Why it matters|Tradeoff|Question to the writer|Fix|Rewrite)"
                   r"(?:\*\*)?\s*:(?:\*\*)?\s*", re.I)
SKIP = re.compile(r"^\s*(?:(?:\*\*)?Disposition(?:\*\*)?\s*:|\[line\s+\d+\]|```|\|)", re.I)
SPAN = re.compile(r'"([^"\n]*)"|“([^”\n]*)”|`([^`\n]*)`')
LINE_REF = re.compile(r"\[line\s+\d+\]\s*[\"“]", re.I)


class CannotRun(Exception):
    pass


def blocks(text):
    """[(start line, level, heading text or '', [(line, text)])]: the text before the first heading, then each
    heading with the lines under it up to the next heading of its own level or higher."""
    out, cur = [], [0, 0, "", []]
    for n, line in enumerate(text.splitlines(), 1):
        m = HEADING.match(line)
        if m:
            level = len(m.group(1))
            if level <= 3:
                out.append(tuple(cur))
                cur = [n, level, m.group(2), []]
                continue
        cur[3].append((n, line))
    out.append(tuple(cur))
    return [b for b in out if b[2] or any(t.strip() for _, t in b[3])]


def first_prose(lines):
    """(line number, sentence) for the first line that is the editor's own words, labels stripped."""
    for n, t in lines:
        if not t.strip() or SKIP.match(t):
            continue
        body = LABEL.sub("", t).strip().lstrip("*_ ")
        if body:
            return n, re.split(r"(?<=[.!?])\s", body, maxsplit=1)[0]
    return None


def quotes(text):
    """True when the text quotes three words or more of the draft, in quotation marks or backticks."""
    return any(len(next(g for g in m.groups() if g is not None).split()) >= 3 for m in SPAN.finditer(text))


def has_quote(lines):
    return any(LINE_REF.search(t) or quotes(t) or t.lstrip().startswith(">") for _, t in lines)


def check(text):
    found, flags, praise_seen = 0, [], set()

    def praise(n, sentence, where):
        if n not in praise_seen and PRAISE.match(sentence) and not quotes(sentence):
            praise_seen.add(n)
            flags.append({"line": n, "rule": "praise", "where": where, "text": sentence, "why": PRAISE_Q})

    for start, level, head, lines in blocks(text):
        is_finding = level == 3 and bool(head) and (
            bool(FINDING.match(head)) or (bool(NUMBERED.match(head)) and any(MARKER.match(t) for _, t in lines)))
        found += is_finding
        title = FINDING.sub("", head) if FINDING.match(head) else NUMBERED.sub("", head)
        if head:
            praise(start, title.strip(), "heading")
        lead = first_prose(lines)
        if lead:
            praise(lead[0], lead[1], "finding" if is_finding else "section" if head else "report opening")
        if is_finding and not has_quote(lines):
            flags.append({"line": start, "rule": "unquoted", "where": "finding", "text": head, "why": QUOTE_Q})
    flags.sort(key=lambda f: (f["line"], f["rule"]))
    return found, flags


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if not a.files:
            raise CannotRun("no report given")
        missing = [f for f in a.files if not Path(f).is_file()]
        if missing:
            raise CannotRun(f"not found: {', '.join(missing)}")
        report = {}
        for f in a.files:
            text = Path(f).read_text(encoding="utf-8")
            found, flags = check(text)
            if not found and any(MARKER.match(t) for t in text.splitlines()):
                raise CannotRun(f"{f} has Issue, Fix or Rewrite lines and no finding heading it could read. "
                                "This is unknown, not clean.")
            report[f] = {"findings_read": found, "flags": flags}
    except CannotRun as e:
        print(f"critique-lint: could not run. {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(report, indent=2))
        return 0
    for f, res in report.items():
        n = len(res["flags"])
        print(f"{f}: {n} flag{'s' if n != 1 else ''} ({res['findings_read']} findings read)")
        for g in res["flags"]:
            print(f"  line {g['line']}  {g['rule']} ({g['where']})  \"{g['text']}\"  {g['why']}")
    print(f"\nNothing here is applied. {CANNOT_TELL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
