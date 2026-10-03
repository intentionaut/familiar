#!/usr/bin/env python3
"""Refuse public text that names a person, a private term or a session.

This repo is public. docs/public-writing.md says how its release notes and pull
requests are written. Commits made through GitHub's own interface skip every
local hook, so this runs on each pull request.

Five checks:

  pii      no email address, phone number or private key in an added line, the
           PR title or the PR description. `.piiallow` holds known-safe regexes.
  terms    no private term in the same places. Terms come from PRIVATE_TERMS
           (an Actions secret), one per line. Matched as whole words.
  traces   no link to a shared chat or agent session, the kind anyone can open.
  dashes   no em dash in the title, the description or an added changelog line.
  shape    no changelog entry touched by this change has more than five bullets.

The terms are private too, so the log names the place, never the term.

Usage:
  public-notes-check.py --base origin/main [--require-terms] [--changelog CHANGELOG.md]

Reads PR_TITLE, PR_BODY and PRIVATE_TERMS from the environment.
Exit 0 clean, 1 refused, 2 could not run.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PII = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"   # email address
    r"|\+\d[\d ]{9,}\d"                                  # international phone number
    r"|\b0[17]\d{8,9}\b"                                 # UK phone number
    r"|BEGIN [A-Z ]*PRIVATE KEY"
)
PII_SAFE = re.compile(r"noreply@|no-reply@|@example\.(com|org)|\bgit@|\b(you|your|name|user|someone)@")  # placeholders
# Links a stranger can open. A private session link, which only its owner can open, is left alone.
TRACES = re.compile(r"claude\.ai/share/|opencode\.ai/s/|chatgpt\.com/share/|chat\.openai\.com/share/")
DASHES = re.compile("[—―]")
# Lock files, the allowlist, and this check's own tests, which have to name what they refuse.
SKIP_FILES = re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|.*\.lock|\.piiallow|test_public_notes_check\.py)$")
MAX_BULLETS = 5


def added_lines(base):
    """Yield (path, line number in the new file, text) for every line the change adds."""
    r = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", base + "...HEAD"],
        capture_output=True, text=True, errors="replace",
    )
    if r.returncode:
        print("could not run: git diff against %s failed: %s" % (base, r.stderr.strip()[:200]))
        sys.exit(2)
    path, n = None, 0
    for line in r.stdout.splitlines():
        if line.startswith("+++ "):
            path = None if line[4:] == "/dev/null" else line[6:]
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            n = int(m.group(1)) if m else 0
        elif line.startswith("+") and not line.startswith("+++") and path:
            yield path, n, line[1:]
            n += 1


def allowlist(root):
    f = root / ".piiallow"
    if not f.exists():
        return None
    pats = [l.strip() for l in f.read_text().splitlines() if l.strip() and not l.strip().startswith("#")]
    return re.compile("|".join(pats)) if pats else None


def term_patterns(raw):
    terms = [t.strip() for t in raw.splitlines() if t.strip() and not t.strip().startswith("#")]
    return [re.compile(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", re.I) for t in terms]


def bullets_by_entry(text):
    """Map each changelog entry's heading line number to (last line number, bullet count)."""
    entries, start, count = {}, None, 0
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if line.startswith("## "):
            if start:
                entries[start] = (i - 1, count)
            start, count = i, 0
        elif start and line.startswith("- "):
            count += 1
    if start:
        entries[start] = (len(lines), count)
    return entries


def check(base, title, body, raw_terms, root, changelog="CHANGELOG.md"):
    """Return (refusals, notices). Each refusal is 'check: place'."""
    refused, notices = [], []
    allow = allowlist(root)
    terms = term_patterns(raw_terms) if raw_terms.strip() else None
    if terms is None:
        notices.append("terms: NOT CHECKED, PRIVATE_TERMS is not set")

    def scan(place, text, in_changelog=False, prose=False):
        if not SKIP_FILES.search(place.split(":")[0]):
            for m in PII.finditer(text):
                hit = text[max(0, m.start() - 20): m.end() + 20]
                if PII_SAFE.search(hit) or (allow and allow.search(text)):
                    continue
                refused.append("pii: " + place)
                break
            if terms and any(t.search(text) for t in terms):
                refused.append("terms: " + place)
            if TRACES.search(text):
                refused.append("traces: " + place)
        if (prose or in_changelog) and DASHES.search(text):
            refused.append("dashes: " + place)

    for n, line in enumerate(title.splitlines(), 1):
        scan("PR title", line, prose=True)
    for n, line in enumerate(body.splitlines(), 1):
        scan("PR description line %d" % n, line, prose=True)

    touched = set()
    for path, n, text in added_lines(base):
        is_log = path == changelog
        scan("%s:%d" % (path, n), text, in_changelog=is_log)
        if is_log:
            touched.add(n)

    log = root / changelog
    if touched and log.exists():
        for start, (end, count) in bullets_by_entry(log.read_text()).items():
            if count > MAX_BULLETS and any(start <= n <= end for n in touched):
                refused.append("shape: %s:%d has %d bullets, the most is %d" % (changelog, start, count, MAX_BULLETS))
    return refused, notices


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    p.add_argument("--require-terms", action="store_true")
    p.add_argument("--changelog", default="CHANGELOG.md")
    a = p.parse_args()
    raw_terms = os.environ.get("PRIVATE_TERMS", "")
    if a.require_terms and not raw_terms.strip():
        print("could not run: PRIVATE_TERMS is not set and this pull request requires the terms check")
        sys.exit(2)
    refused, notices = check(a.base, os.environ.get("PR_TITLE", ""), os.environ.get("PR_BODY", ""),
                             raw_terms, Path.cwd(), a.changelog)
    for n in notices:
        print(n)
    if refused:
        print("refused. See docs/public-writing.md.")
        for r in refused:
            print("  " + r)
        sys.exit(1)
    print("clean")


if __name__ == "__main__":
    main()
