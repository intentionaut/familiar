#!/usr/bin/env python3
"""Render CHANGELOG.md into site/releases.html.

The release notes are written once, in CHANGELOG.md. This renders them for the
web rather than keeping a second copy by hand, because a second copy is a copy
that goes stale: the site is meant to be canonical for the product, and a page
somebody has to remember to update is not.

Only the release entries are rendered. The "How these are written" rules at the
top of the changelog are for whoever writes an entry, not for whoever reads one.

    python3 scripts/build-site.py

Run by the Pages workflow before the site is uploaded, so what deploys always
matches the changelog in the same commit.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
OUT = ROOT / "site" / "releases.html"

# "## 0.17.0 (2026-09-02)"
VERSION = re.compile(r"^##\s+(\d+\.\d+\.\d+)\s*\((\d{4}-\d{2}-\d{2})\)\s*$")


def inline(text: str) -> str:
    """Bold, code and links. The changelog uses nothing else."""
    out = html.escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', out)
    return out


def render_body(lines: list[str]) -> str:
    """Paragraphs and bullet lists, which is all an entry contains."""
    parts: list[str] = []
    para: list[str] = []
    bullets: list[list[str]] = []

    def flush_para() -> None:
        if para:
            parts.append(f"<p>{inline(' '.join(para).strip())}</p>")
            para.clear()

    def flush_bullets() -> None:
        if bullets:
            items = "".join(f"<li>{inline(' '.join(b).strip())}</li>" for b in bullets)
            parts.append(f"<ul>{items}</ul>")
            bullets.clear()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            flush_bullets()
            continue
        if line.lstrip().startswith("- "):
            flush_para()
            bullets.append([line.lstrip()[2:]])
        elif bullets and line.startswith((" ", "\t")):
            bullets[-1].append(line.strip())   # continuation of the last bullet
        else:
            flush_bullets()
            para.append(line.strip())
    flush_para()
    flush_bullets()
    return "\n      ".join(parts)


def releases(text: str):
    """Every version entry, newest first, in the order the changelog has them."""
    found, current, body = [], None, []
    for line in text.splitlines():
        m = VERSION.match(line)
        if m:
            if current:
                found.append((*current, body))
            current, body = (m.group(1), m.group(2)), []
        elif current is not None:
            if line.strip() == "---":
                continue
            body.append(line)
    if current:
        found.append((*current, body))
    return found


PAGE = """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Release notes | Familiar</title>
<meta name="description" content="What changed in Familiar, written for the writer using it.">
<link rel="canonical" href="https://familiar.intentionaut.com/releases.html">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#f7e9e0">
<meta property="og:site_name" content="Familiar">
<meta property="og:title" content="Release notes | Familiar">
<meta property="og:description" content="What changed in Familiar, written for the writer using it.">
<meta property="og:url" content="https://familiar.intentionaut.com/releases.html">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..700&family=Jost:wght@300..600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="./style.css">
</head>
<body>

<section class="wrap">
  <p class="eyebrow"><a class="link-arrow" href="./">Familiar</a></p>
  <h1>Release notes</h1>
  <p class="lede">
    What changed, written for the writer using it rather than the developer who
    made it.
  </p>
</section>

<section class="wrap">
{releases}
</section>

<footer class="wrap">
  <p>
    Every entry is written from <a href="https://github.com/intentionaut/familiar/blob/main/CHANGELOG.md">CHANGELOG.md</a>
    in the repository, so this page and the source can never disagree.
  </p>
</footer>

</body>
</html>
"""

ENTRY = """  <article class="release">
    <h2 id="v{anchor}">{version}</h2>
    <p class="release-date"><time datetime="{date}">{date}</time></p>
    <div class="release-body">
      {body}
    </div>
  </article>"""


def main() -> int:
    if not CHANGELOG.is_file():
        print(f"no changelog at {CHANGELOG}", file=sys.stderr)
        return 1
    found = releases(CHANGELOG.read_text())
    if not found:
        print("no release entries found in the changelog", file=sys.stderr)
        return 1

    entries = "\n".join(
        ENTRY.format(version=v, anchor=v.replace(".", "-"), date=d, body=render_body(b))
        for v, d, b in found
    )
    OUT.write_text(PAGE.format(releases=entries))
    print(f"wrote {OUT.relative_to(ROOT)} ({len(found)} releases, newest {found[0][0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
