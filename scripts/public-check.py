#!/usr/bin/env python3
"""Refuse a change that would put a writer's own material in this public repo.

This repo is public. Its `knowledge/` holds blank templates, and a writer's
filled-in house lives somewhere private (see AGENTS.md, "This repository is
public"). Commits made through GitHub's own interface skip every local hook,
so this runs on each pull request as well as in the tests.

Four checks:

  templates  every file under knowledge/ is listed in knowledge/TEMPLATES.
             A new file is a conscious addition, never a side effect.
  filled     no template carries a writer's answers: no dated or attributed
             `source: declared`, no rows in the tables that start empty.
  replaced   a change does not swap a template's placeholders for content. A
             template line reads `[what goes here]`; a change that removes
             three or more of those from a file and adds none has filled the
             file in, even with nothing the other checks can name.
  terms      no added line, commit message, PR title or PR description names
             a private term. Terms come from FAMILIAR_PRIVATE_TERMS (an
             Actions secret) and from `private/public-terms.txt` in the
             writer's house. A PR labelled `public-ok` skips this check only.

The terms are private too, so a public CI log names the place, never the term.

Usage:
  public-check.py                     templates and filled only
  public-check.py --base origin/main  all four, against that base

Exit 0 clean, 1 refused, 2 could not run.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import paths  # noqa: E402

MANIFEST = "knowledge/TEMPLATES"
EMPTY_TABLES = ("knowledge/metrics.md", "knowledge/rejected-rules.md")
FILLED = re.compile(r"source: declared`?\s*[,(]")
# A template's own blank: `[the thing to say]`. A markdown link, `[text](url)`, is not one.
PLACEHOLDER = re.compile(r"\[[^\]\n]{2,}\](?!\()")
REPLACED_AT = 3  # placeholder lines removed, with none added, before a file counts as filled in
IN_CI = bool(os.environ.get("GITHUB_ACTIONS"))


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout


def check_templates(tracked, manifest):
    listed = {l.strip() for l in manifest.splitlines()
              if l.strip() and not l.startswith("#")}
    return [f"{f}: not in {MANIFEST}. The repo ships blank templates only; "
            "a writer's own files belong in their house."
            for f in sorted(tracked)
            if f.startswith("knowledge/") and f != MANIFEST and f not in listed]


def check_filled(files):
    """files: {path: text}. Returns problems."""
    out = []
    for path, text in sorted(files.items()):
        for n, line in enumerate(text.splitlines(), 1):
            if FILLED.search(line):
                out.append(f"{path}:{n}: a dated or attributed `source: declared` "
                           "is a writer's answer, not a template")
        if path in EMPTY_TABLES:
            rows = [n for n, line in enumerate(text.splitlines(), 1)
                    if line.startswith("|")]
            # A header and its separator are the template; anything after is data.
            if len(rows) > 2:
                out.append(f"{path}:{rows[2]}: this table ships empty")
    return out


def check_replaced(changes, manifest):
    """changes: {path: (removed_lines, added_lines)} for files changed against the base.

    A template ships with placeholders. Taking several out and putting none back
    is how a writer's own answers get into a blank file, so it is refused for a
    listed template. One reworded placeholder, or a rewrite that keeps some, passes.
    """
    listed = {l.strip() for l in manifest.splitlines()
              if l.strip() and not l.startswith("#")}
    out = []
    for path, (removed, added) in sorted(changes.items()):
        if path not in listed or not path.endswith(".md"):
            continue
        gone = sum(1 for l in removed if PLACEHOLDER.search(l))
        kept = sum(1 for l in added if PLACEHOLDER.search(l))
        if gone >= REPLACED_AT and kept == 0 and any(l.strip() for l in added):
            out.append(f"{path}: {gone} placeholder lines replaced with content and none "
                       "put back. The repo ships blank templates only; the writer's "
                       "answers belong in their house.")
    return out


def load_terms(env=None, house_file=None):
    env = os.environ if env is None else env
    raw = env.get("FAMILIAR_PRIVATE_TERMS", "")
    if house_file is None:
        home, whose = paths.knowledge_dir()
        house_file = home / "private" / "public-terms.txt" if whose == "yours" else None
    if house_file and Path(house_file).is_file():
        raw += "\n" + Path(house_file).read_text()
    terms = {t.strip() for t in raw.splitlines()
             if t.strip() and not t.strip().startswith("#")}
    return sorted(terms)


def find_terms(sources, terms, show_term):
    """sources: [(where, text)]. Returns problems."""
    if not terms:
        return []
    pats = [(t, re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)", re.I)) for t in terms]
    out = []
    for where, text in sources:
        for n, line in enumerate(text.splitlines(), 1):
            for term, pat in pats:
                if pat.search(line):
                    what = f'"{term}"' if show_term else "a private term"
                    out.append(f"{where}, line {n}: names {what}")
    return out


def added_lines(base):
    """Added lines per file, and the commit messages, between base and HEAD."""
    sources, current, buf = [], None, []
    # Against the merge base, not HEAD, so uncommitted edits are read too.
    fork = git("merge-base", base, "HEAD").strip()
    for line in git("diff", "--unified=0", "--no-color", fork).splitlines():
        if line.startswith("+++ "):
            if current:
                sources.append((current + " (added lines)", "\n".join(buf)))
            current, buf = line[6:] if line.startswith("+++ b/") else None, []
        elif line.startswith("+") and current:
            buf.append(line[1:])
    if current:
        sources.append((current + " (added lines)", "\n".join(buf)))
    sources.append(("commit messages", git("log", "--format=%B", f"{base}..HEAD")))
    return sources


def removed_and_added(base):
    """{path: (removed lines, added lines)} between the merge base and the working tree."""
    fork = git("merge-base", base, "HEAD").strip()
    changes, current = {}, None
    for line in git("diff", "--unified=0", "--no-color", fork).splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
            if current:
                changes.setdefault(current, ([], []))
        elif line.startswith("--- "):
            continue
        elif current and line.startswith("-"):
            changes[current][0].append(line[1:])
        elif current and line.startswith("+"):
            changes[current][1].append(line[1:])
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    args = ap.parse_args()
    try:
        tracked = git("ls-files").splitlines()
        manifest = (ROOT / MANIFEST).read_text()
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"public-check could not run: {e}", file=sys.stderr)
        return 2

    knowledge = {f: (ROOT / f).read_text() for f in tracked
                 if f.startswith("knowledge/") and f.endswith(".md") and (ROOT / f).is_file()}
    problems = check_templates(tracked, manifest) + check_filled(knowledge)

    unchecked = False
    if args.base:
        problems += check_replaced(removed_and_added(args.base), manifest)
        if os.environ.get("PUBLIC_OK") == "true":
            print("terms: skipped, the PR is labelled public-ok")
        else:
            terms = load_terms()
            if not terms:
                print("terms: none loaded, so this cannot say the change is clean.")
                if IN_CI:
                    print("Set the FAMILIAR_PRIVATE_TERMS secret.")
                    return 2
                unchecked = True
            sources = added_lines(args.base)
            for key, label in (("PR_TITLE", "PR title"), ("PR_BODY", "PR description")):
                if os.environ.get(key):
                    sources.append((label, os.environ[key]))
            problems += find_terms(sources, terms, show_term=not IN_CI)

    if problems:
        print("Refused: this repo is public, and the change carries a writer's own material.\n")
        print("\n".join("  " + p for p in problems))
        print("\nMove it to the writer's house (python3 scripts/paths.py says where),"
              "\nthen take it out of the branch, the commit messages and the PR."
              "\nSee AGENTS.md, \"This repository is public\".")
        return 1
    if unchecked:
        print("public-check: templates clean; terms not checked")
        return 2
    print("public-check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
