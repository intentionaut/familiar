#!/usr/bin/env python3
"""Compare Familiar's AI-tell list against blader/humanizer and report gaps.

Humanizer (github.com/blader/humanizer) is the most actively curated list of
AI writing patterns. Familiar keeps its own list in knowledge/style-rules.md
because it runs as a report inside an editorial pipeline, not as a rewrite.
The two drift. This script fetches humanizer's SKILL.md, pulls out its
overused-word list and its numbered patterns, and writes
knowledge/humanizer-check.md listing anything Familiar does not mention yet.

It proposes; it never edits style-rules.md. A human decides what to adopt,
one pattern at a time, with a real example (see CONTRIBUTING.md).

Usage: scripts/humanizer-check.py [--quiet]
Exit code 0 always; the report says whether there is anything new.
"""
import re, sys, json, datetime, pathlib, urllib.request

RAW = "https://raw.githubusercontent.com/blader/humanizer/main/SKILL.md"
ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = ROOT / "knowledge" / "style-rules.md"
REPORT = ROOT / "knowledge" / "humanizer-check.md"

def fetch():
    with urllib.request.urlopen(RAW, timeout=30) as r:
        return r.read().decode("utf-8")

def words_from(skill):
    out = []
    for m in re.finditer(r"\*\*[^*]*AI words:\*\*\s*(.+)", skill):
        for w in m.group(1).split(","):
            w = re.sub(r"\(.*?\)", "", w).strip().strip(".").lower()
            if w:
                out.append(w)
    return sorted(set(out))

def patterns_from(skill):
    return re.findall(r"^### (\d+)\. (.+)$", skill, flags=re.M)

def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())

def main():
    quiet = "--quiet" in sys.argv
    skill = fetch()
    version = re.search(r"version:\s*([0-9.]+)", skill)
    version = version.group(1) if version else "unknown"
    ours = norm(RULES.read_text(encoding="utf-8"))

    missing_words = [w for w in words_from(skill) if w.split("/")[0].strip() not in ours]

    missing_patterns = []
    for num, title in patterns_from(skill):
        key = [t for t in norm(title).split() if len(t) > 3 and t not in
               ("with", "that", "from", "about", "when", "into", "left", "your")]
        hits = sum(1 for t in key if t in ours)
        if not key or hits / len(key) < 0.5:
            missing_patterns.append((num, title))

    today = datetime.date.today().isoformat()
    lines = [
        "# Humanizer check",
        "",
        f"Generated {today} against humanizer SKILL.md version {version}.",
        "Candidates only. Nothing here is applied; adopt one at a time with a real",
        "example, per CONTRIBUTING.md. Re-run: `scripts/humanizer-check.py`.",
        "",
        "## Overused words humanizer lists that style-rules.md does not mention",
        "",
    ]
    lines += [f"- {w}" for w in missing_words] or ["- none"]
    lines += ["", "## Humanizer patterns with no obvious counterpart in style-rules.md", "",
              "Matched loosely on heading words, so expect some false alarms.", ""]
    lines += [f"- §{n} {t}" for n, t in missing_patterns] or ["- none"]
    lines += ["", f"Source: {RAW}", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    summary = {"version": version, "missing_words": len(missing_words),
               "missing_patterns": len(missing_patterns), "report": str(REPORT.relative_to(ROOT))}
    if not quiet:
        print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
