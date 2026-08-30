#!/usr/bin/env python3
"""Build a static board of every piece, and a page for each one.

Familiar keeps each piece as a folder of markdown. That is right for writing
and wrong for seeing what you have. This writes a plain HTML board, columns by
stage, one card per piece with its title, date and the first thing it says.
Click a card and you get the whole piece on one page: what it argues, what is
waiting on you, what is still unresolved, then the draft itself.

Nothing is sent anywhere. Nothing is changed. It reads the piece folders and
writes HTML beside them.

Usage:
  scripts/board.py                      build the board and print the path
  scripts/board.py --open               build it and open it in a browser
  scripts/board.py --pieces DIR         somewhere other than ./pieces
  scripts/board.py --out DIR            somewhere other than <pieces>/.board
  scripts/board.py --command PREFIX     how to invoke a stage in the hint
  scripts/board.py --stale-days N       when a piece counts as resting (7)

Pieces can live in more than one place. Pass --pieces once per folder, or set
FAMILIAR_PIECES to a colon-separated list. When there is more than one, each
card says which folder it came from:

  scripts/board.py --open \
    --pieces ~/Documents/Dex/04-Projects/Writing \
    --pieces ~/Projects/intentionaut-newsroom/issues
"""
import argparse, datetime, html, os, pathlib, re, sys, webbrowser

# --------------------------------------------------------------------------
# Markdown to HTML, for display only
#
# This renders a draft so it can be read. It is deliberately not the converter
# a CMS push would need: nothing here leaves the machine, so being forgiving
# costs nothing. A push needs a converter that refuses what it cannot carry.
# Do not reuse this one for that.
# --------------------------------------------------------------------------

def _inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)", r'<img alt="\1" src="\2">', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", t)
    # Familiar's own markers, so unresolved work is visible at a glance.
    t = re.sub(r"\[(NEEDS SOURCE|ASK THE WRITER)([^\]]*)\]",
               r'<mark class="bracket">[\1\2]</mark>', t)
    return t

def md_to_html(md):
    out, lines, i = [], md.split("\n"), 0
    list_stack = []

    def close_lists(to=0):
        while len(list_stack) > to:
            out.append(f"</{list_stack.pop()}>")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            close_lists()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i])); i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue

        if not stripped:
            close_lists(); i += 1; continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            close_lists(); out.append("<hr>"); i += 1; continue

        m = re.match(r"(#{1,6})\s+(.*)", stripped)
        if m:
            close_lists()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            i += 1; continue

        if stripped.startswith(">"):
            close_lists()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append("<blockquote>" + _inline(" ".join(buf)) + "</blockquote>")
            continue

        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)", line)
        if m:
            indent = len(m.group(1)) // 2 + 1
            kind = "ul" if m.group(2) in "-*+" else "ol"
            if indent > len(list_stack):
                out.append(f"<{kind}>"); list_stack.append(kind)
            elif indent < len(list_stack):
                close_lists(indent)
            out.append(f"<li>{_inline(m.group(3))}</li>")
            i += 1; continue

        close_lists()
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^\s*([-*+]|\d+[.)])\s|^#{1,6}\s|^>|^```", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        if buf:
            out.append("<p>" + _inline(" ".join(buf)) + "</p>")

    close_lists()
    return "\n".join(out)

# --------------------------------------------------------------------------
# Reading a piece
# --------------------------------------------------------------------------

def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def frontmatter(md):
    """Pull a YAML-ish block out, even when a note sits above it.

    A draft does not always start with its frontmatter. A smoke-test warning or
    an editor's note above it is common, and the title still has to be found.
    Anything above the block is kept, because a note there is worth reading.
    """
    lines = md.split("\n")
    for start in range(min(len(lines), 20)):
        if lines[start].strip() != "---":
            continue
        for end in range(start + 1, min(len(lines), start + 60)):
            if lines[end].strip() != "---":
                continue
            fm = {}
            for line in lines[start + 1:end]:
                m = re.match(r'\s*([A-Za-z_]+):\s*"?(.*?)"?\s*$', line)
                if m:
                    fm[m.group(1)] = m.group(2)
            if not fm:
                break                       # a horizontal rule, not frontmatter
            before = "\n".join(lines[:start]).strip()
            after = "\n".join(lines[end + 1:]).lstrip("\n")
            return fm, (before + "\n\n" + after).lstrip("\n") if before else after
        break
    return {}, md

def last_context_entry(folder):
    """The last entry in the piece's own log, or a root log naming this piece."""
    text = read(folder / "SESSION-CONTEXT.md")
    if not text:
        root = folder.parent.parent / "SESSION-CONTEXT.md"
        rt = read(root)
        if rt:
            keep = [p for p in re.split(r"(?m)^(?=## \d{4}-\d{2}-\d{2} )", rt)
                    if folder.name in p.splitlines()[0:1][0] if p.strip()] if rt.strip() else []
            text = keep[-1] if keep else ""
    if not text:
        return {}
    entries = [p for p in re.split(r"(?m)^(?=## \d{4}-\d{2}-\d{2} )", text) if p.strip()]
    if not entries:
        return {}
    last = entries[-1]
    got = {}
    for field in ("Status", "Files", "What changed", "Decision gate", "Next stage"):
        m = re.search(rf"^{field}:\s*(.+?)(?=\n[A-Z][a-z]+ ?[a-z]*:|\Z)", last, re.S | re.M)
        if m:
            got[field] = " ".join(m.group(1).split())
    m = re.match(r"## (\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(\S+)", last)
    if m:
        got["when"], got["stage"] = m.group(1), m.group(2)
    return got

# The state of the writing, in the writer's terms. Familiar's stage names
# describe which prompt ran last, which is the tool's business rather than the
# writer's. What a writer scans for is what a piece needs next.
STAGES = [
    ("thinking", "Thinking"),
    ("writing",  "Writing"),
    ("editing",  "Editing"),
    ("ready",    "Ready"),
    ("sent",     "Sent"),
]

def derive_stage(folder, brackets=0):
    has = lambda *p: (folder.joinpath(*p)).exists()
    mtime = lambda *p: (folder.joinpath(*p)).stat().st_mtime
    if has("final.md"):
        return "sent"
    if has("draft.md"):
        if brackets:
            return "editing"
        d = mtime("draft.md")
        reports = [r for r in ("edits/line-edit-report.md", "edits/dev-edit-report.md")
                   if has(*r.split("/"))]
        if not reports:
            return "editing"          # a draft nobody has edited yet
        if any(mtime(*r.split("/")) > d for r in reports):
            return "editing"          # flags written after the draft, not worked through
        return "ready"
    if has("edits", "line-edit-report.md") or has("edits", "dev-edit-report.md"):
        return "editing"
    if has("outline.md"):
        return "writing"
    return "thinking"


def next_action(folder, state, brackets, has_social):
    """What this piece needs, when the context log has not said.

    Every card gets one. A board where most cards say nothing is a list.
    """
    has = lambda *p: (folder.joinpath(*p)).exists()
    mtime = lambda *p: (folder.joinpath(*p)).stat().st_mtime
    if state == "sent":
        return "Diff the draft against what you sent, to teach it your voice"
    if state == "ready":
        if has_social:
            return "Confirm the week, or leave a slot empty"
        return "Turn it into a week of posts, or send it"
    if state == "editing":
        if brackets:
            n = len(brackets) if isinstance(brackets, list) else brackets
            return f"Resolve {n} bracket{'s' if n != 1 else ''} the draft is still missing"
        if has("draft.md"):
            d = mtime("draft.md")
            for r, name in (("edits/line-edit-report.md", "line edit"),
                            ("edits/dev-edit-report.md", "developmental edit")):
                if has(*r.split("/")) and mtime(*r.split("/")) > d:
                    return f"Work through the {name}, flag by flag"
            return "Ask for a developmental edit"
        return "Work through the edit report"
    if state == "writing":
        return "Write the draft from the structure you chose"
    if has("notes.md"):
        return "Ask for three structures and pick one"
    if has("interview-questions.md") or has("brief.md"):
        return "Run the interview from the questions"
    return "Start the interview"

def newest_mtime(folder):
    best = folder.stat().st_mtime
    for p in folder.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            best = max(best, p.stat().st_mtime)
    return best

def ago(ts, now):
    d = now - ts
    if d < 3600: return f"{int(d // 60)}m"
    if d < 86400: return f"{int(d // 3600)}h"
    if d < 86400 * 14: return f"{int(d // 86400)}d"
    if d < 86400 * 70: return f"{int(d // 604800)}w"
    return f"{int(d // 2592000)}mo"

def reading_ease(text):
    words = re.findall(r"[A-Za-z']+", text)
    sents = [x for x in re.split(r"[.!?]+", text) if x.strip()]
    if not words or not sents:
        return None, None
    def syl(w):
        w = w.lower(); c = len(re.findall(r"[aeiouy]+", w))
        return max(1, c - (1 if w.endswith("e") and c > 1 else 0))
    sy = sum(syl(w) for w in words)
    fre = 206.835 - 1.015 * (len(words) / len(sents)) - 84.6 * (sy / len(words))
    return len(words), round(fre)

def gather(folder, now, stale_days, source=""):
    draft_raw = read(folder / "draft.md")
    fm, draft_body = frontmatter(draft_raw)
    notes = read(folder / "notes.md")
    outline = read(folder / "outline.md")

    title = fm.get("title") or ""
    if not title:
        m = re.search(r"^#\s+(.+)", notes or outline, re.M)
        title = m.group(1) if m else ""
    if not title:
        title = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", folder.name).replace("-", " ").title()

    date = fm.get("date") or ""
    if not date:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", folder.name)
        date = m.group(1) if m else ""

    # The first thing the piece actually says, in this order of preference.
    snippet = ""
    if draft_body:
        taken = []
        for para in draft_body.split("\n\n"):
            para = para.strip()
            if not para or para.startswith(("#", ">", "-", "*", "```")):
                continue
            taken.append(para)
            if len(" ".join(taken)) > 150:
                break
        snippet = " ".join(taken)
    if not snippet and notes:
        m = re.search(r"^##\s*Working thesis\s*\n+(.+?)(?=\n#|\Z)", notes, re.S | re.M)
        if m:
            snippet = m.group(1).strip()
    if not snippet:
        for para in (notes or outline).split("\n\n"):
            para = para.strip()
            if para and not para.startswith(("#", ">", "-", "*", "```", "|")):
                snippet = para; break
    snippet = " ".join(snippet.split())
    if len(snippet) > 240:
        snippet = snippet[:237].rsplit(" ", 1)[0] + "..."

    ctx = last_context_entry(folder)
    ts = newest_mtime(folder)
    words, fre = reading_ease(re.sub(r"\[(NEEDS SOURCE|ASK THE WRITER)[^\]]*\]", "", draft_body))
    brackets = re.findall(r"\[(?:NEEDS SOURCE|ASK THE WRITER)[^\]]*\]", draft_raw)
    state = derive_stage(folder, len(brackets))
    # The writer's own words win. The derived action is the fallback, and for
    # most pieces it is all there is.
    derived = next_action(folder, state, brackets, (folder / "social.md").exists())
    gate = ctx.get("Decision gate", "")
    action = gate or derived
    from_log = bool(gate)

    return {
        "slug": folder.name, "folder": folder, "title": title, "date": date,
        "source": source, "page": (f"{source}--{folder.name}" if source else folder.name),
        "snippet": snippet, "stage": state, "ts": ts,
        "action": action, "from_log": from_log,
        "ago": ago(ts, now), "stale": (now - ts) > stale_days * 86400,
        "ctx": ctx, "words": words, "fre": fre, "brackets": brackets,
        "subtitle": fm.get("subtitle", ""),
        "files": sorted(p.relative_to(folder).as_posix()
                        for p in folder.rglob("*")
                        if p.is_file() and not p.name.startswith(".")),
    }

# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------

CSS = """
:root{--paper:#faf7f4;--card:#fff;--ink:#2b2233;--muted:#6f6478;--line:#e6ded9;
--accent:#c4506a;--warn:#a8651f;--ok:#4a7c59;--shadow:0 1px 2px rgba(43,34,51,.06),0 8px 24px -16px rgba(43,34,51,.4)}
@media(prefers-color-scheme:dark){:root{--paper:#16131a;--card:#1e1a24;--ink:#ece7f0;
--muted:#9d93a8;--line:#2e2836;--accent:#e8899f;--warn:#d9a05b;--ok:#7fb98d;
--shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px -16px #000}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.6 ui-sans-serif,-apple-system,"Segoe UI",system-ui,sans-serif;
-webkit-font-smoothing:antialiased}
a{color:inherit}
header.top{padding:28px 32px 8px;display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
header.top h1{margin:0;font-size:1.3rem;font-weight:650;letter-spacing:-.01em}
header.top .meta{color:var(--muted);font-size:.85rem}
header.top .meta b{color:var(--ink);font-weight:600}
.board{display:flex;gap:12px;padding:16px 32px 48px;overflow-x:auto;align-items:stretch}
.col{flex:0 0 288px;min-width:288px;background:color-mix(in srgb,var(--ink) 3%,transparent);
border:1px solid var(--line);border-radius:14px;padding:12px 12px 6px}
.col h2{margin:0 0 12px;padding:0 4px;font-size:.72rem;text-transform:uppercase;
letter-spacing:.09em;color:var(--muted);font-weight:700;display:flex;gap:8px;align-items:center}
.col h2 span{background:var(--line);color:var(--muted);border-radius:999px;
padding:1px 8px;font-size:.7rem;letter-spacing:0;font-weight:600}
.col.empty{flex:0 0 168px;min-width:168px;background:transparent;border-style:dashed;opacity:.6}
.col.empty h2{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);
border-radius:12px;padding:14px 16px;margin-bottom:10px;box-shadow:var(--shadow);
transition:transform .12s ease,border-color .12s ease}
.card:hover{transform:translateY(-2px);border-color:var(--accent)}
.card h3{margin:0 0 4px;font-size:.98rem;line-height:1.35;font-weight:640}
.card .sub{color:var(--muted);font-size:.78rem;margin-bottom:8px;
display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.card p{margin:0;color:var(--muted);font-size:.85rem;line-height:1.5}
.card .waiting{margin-top:10px;padding-top:10px;border-top:1px dashed var(--line);
font-size:.8rem;color:var(--ink)}
.card .waiting b{color:var(--accent);font-weight:600;font-size:.72rem;
text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:2px}
.card .waiting.derived b{color:var(--muted)}
.card .waiting.derived{color:var(--muted)}
.pill{font-size:.7rem;padding:1px 7px;border-radius:999px;border:1px solid var(--line);
color:var(--muted);white-space:nowrap}
.pill.stale{color:var(--warn);border-color:var(--warn)}
.pill.brk{color:var(--accent);border-color:var(--accent)}
.pill.src{color:var(--muted);background:var(--line);border-color:transparent}
.empty-state{padding:48px 32px;color:var(--muted);max-width:52ch}
.empty-state code{background:var(--card);border:1px solid var(--line);
border-radius:6px;padding:2px 6px;font-size:.85em}
/* piece page */
.wrap{max-width:74ch;margin:0 auto;padding:32px 24px 96px}
.back{display:inline-block;color:var(--muted);text-decoration:none;font-size:.85rem;margin-bottom:24px}
.back:hover{color:var(--accent)}
.piece-head h1{margin:0 0 6px;font-size:1.9rem;line-height:1.2;letter-spacing:-.02em}
.piece-head .sub{color:var(--muted);font-size:1rem;margin:0 0 14px}
.facts{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:28px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:16px 18px;margin-bottom:24px;box-shadow:var(--shadow)}
.panel h2{margin:0 0 8px;font-size:.72rem;text-transform:uppercase;
letter-spacing:.09em;color:var(--accent);font-weight:700}
.panel p{margin:0 0 8px}
.panel p:last-child{margin:0}
.panel.next code{display:block;background:var(--paper);border:1px solid var(--line);
border-radius:6px;padding:8px 10px;margin-top:8px;font-size:.85rem;overflow-x:auto}
details.more{margin-bottom:14px;border:1px solid var(--line);border-radius:12px;
background:var(--card);overflow:hidden}
details.more>summary{cursor:pointer;padding:12px 18px;font-size:.85rem;color:var(--muted);
list-style:none;display:flex;justify-content:space-between}
details.more>summary::-webkit-details-marker{display:none}
details.more>summary:hover{color:var(--accent)}
details.more .inner{padding:0 18px 18px;border-top:1px solid var(--line)}
article.draft{font-size:1.02rem;line-height:1.72}
article.draft h1,article.draft h2,article.draft h3{line-height:1.25;margin:2em 0 .5em;
letter-spacing:-.01em}
article.draft h1{font-size:1.5rem}article.draft h2{font-size:1.2rem}
article.draft h3{font-size:1.03rem}
article.draft p{margin:0 0 1.15em}
article.draft blockquote{margin:1.4em 0;padding:2px 0 2px 18px;border-left:3px solid var(--accent);
color:var(--muted);font-style:normal}
article.draft pre{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:12px 14px;overflow-x:auto;font-size:.85rem}
article.draft code{font-size:.9em}
article.draft img{max-width:100%;border-radius:8px}
article.draft hr{border:0;border-top:1px solid var(--line);margin:2em 0}
mark.bracket{background:color-mix(in srgb,var(--accent) 16%,transparent);
color:var(--accent);border-radius:4px;padding:1px 4px;font-size:.88em;font-weight:600}
.none{color:var(--muted);font-style:italic}
"""

def page(title, body, css_depth=0):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style></head><body>
{body}
</body></html>"""

def card_html(p):
    pills = [f'<span class="pill">{html.escape(p["date"] or "no date")}</span>',
             f'<span class="pill{" stale" if p["stale"] else ""}">{p["ago"]}</span>']
    if p["brackets"]:
        n = len(p["brackets"])
        pills.append(f'<span class="pill brk">{n} bracket{"s" if n != 1 else ""}</span>')
    if p["source"]:
        pills.append(f'<span class="pill src">{html.escape(p["source"])}</span>')
    label = "Waiting on you" if p["from_log"] else "Next"
    w = (f'<div class="waiting{"" if p["from_log"] else " derived"}">'
         f'<b>{label}</b>{html.escape(p["action"])}</div>')
    return f"""<a class="card" href="{html.escape(p['page'])}.html">
  <h3>{html.escape(p['title'])}</h3>
  <div class="sub">{''.join(pills)}</div>
  <p>{html.escape(p['snippet']) or '<span class="none">nothing written yet</span>'}</p>
  {w}
</a>"""

def command_prefix(pieces_dir):
    """How Familiar is actually invoked for these pieces.

    In a Dex vault the skill is installed as familiar-custom and is called with
    a leading slash. Everywhere else the installed commands are familiar-*.
    Printing a command the writer cannot run is worse than printing none.
    """
    for parent in [pieces_dir] + list(pieces_dir.parents):
        if (parent / ".claude" / "skills" / "familiar-custom").is_dir():
            return "/familiar-custom"
    return "familiar"

NEXT_COMMAND = {
    "thinking": "familiar interview {slug}",
    "writing":  "familiar draft {slug}",
    "editing":  "familiar dev-edit {slug}",
    "ready":    "familiar social {slug}",
    "sent":     "familiar learn diff {slug}",
}

def piece_page(p, prefix="familiar"):
    facts = [f'<span class="pill">{html.escape(dict(STAGES)[p["stage"]])}</span>',
             f'<span class="pill">{html.escape(p["date"] or "no date")}</span>',
             f'<span class="pill{" stale" if p["stale"] else ""}">touched {p["ago"]} ago</span>']
    if p["source"]:
        facts.append(f'<span class="pill src">{html.escape(p["source"])}</span>')
    if p["words"]:
        facts.append(f'<span class="pill">{p["words"]} words</span>')
    if p["fre"] is not None:
        facts.append(f'<span class="pill">reading ease {p["fre"]}</span>')
    if p["brackets"]:
        facts.append(f'<span class="pill brk">{len(p["brackets"])} unresolved</span>')

    parts = [f'<a class="back" href="index.html">&larr; all pieces</a>',
             '<div class="piece-head">',
             f'<h1>{html.escape(p["title"])}</h1>']
    if p["subtitle"]:
        parts.append(f'<p class="sub">{html.escape(p["subtitle"])}</p>')
    parts.append(f'<div class="facts">{"".join(facts)}</div></div>')

    ctx = p["ctx"]
    parts.append(
        f'<div class="panel"><h2>{"Waiting on you" if p["from_log"] else "Next"}</h2>'
        f'<p>{html.escape(p["action"])}</p>'
        + (f'<p class="none">Last touched by {html.escape(ctx.get("stage",""))} '
           f'on {html.escape(ctx.get("when",""))}.</p>' if ctx.get("when")
           else '<p class="none">Worked out from the files. This piece has no '
                'context log yet, so no stage has left a note.</p>')
        + '</div>')

    if p["brackets"]:
        items = "".join(f"<li>{_inline(b)}</li>" for b in p["brackets"])
        parts.append(f'<div class="panel"><h2>Still unresolved</h2><ul>{items}</ul></div>')

    cmd = NEXT_COMMAND.get(p["stage"], "").format(slug=p["slug"])
    cmd = cmd.replace("familiar ", prefix + " ", 1) if cmd else ""
    parts.append(
        '<div class="panel next"><h2>Pick it back up</h2>'
        f'<p>The piece is at <b>{html.escape(dict(STAGES)[p["stage"]])}</b>. '
        'Open the folder, or run the next stage.</p>'
        f'<code>{html.escape(str(p["folder"]))}</code>'
        + (f'<code>{html.escape(cmd)}</code>' if cmd else "")
        + '</div>')

    # Supporting files, folded away.
    for name, label in (("notes.md", "Notes from the interview"),
                        ("outline.md", "The outline"),
                        ("edits/dev-edit-report.md", "Developmental edit"),
                        ("edits/line-edit-report.md", "Line edit"),
                        ("social.md", "Social")):
        body = read(p["folder"] / name)
        if body.strip():
            words = len(re.findall(r"[A-Za-z']+", body))
            parts.append(
                f'<details class="more"><summary><span>{html.escape(label)}</span>'
                f'<span>{words} words</span></summary>'
                f'<div class="inner"><article class="draft">{md_to_html(body)}</article></div>'
                '</details>')

    draft_raw = read(p["folder"] / "draft.md")
    if draft_raw.strip():
        _, body = frontmatter(draft_raw)
        parts.append('<h2 style="margin:36px 0 4px;font-size:.72rem;text-transform:uppercase;'
                     'letter-spacing:.09em;color:var(--muted)">The draft</h2>')
        parts.append(f'<article class="draft">{md_to_html(body)}</article>')
    else:
        parts.append('<p class="none">No draft yet.</p>')

    return page(p["title"], f'<div class="wrap">{"".join(parts)}</div>')

def board_page(pieces, pieces_dirs, prefix="familiar"):
    if not pieces:
        where = ", ".join(str(d) for d in pieces_dirs)
        body = (f'<header class="top"><h1>Familiar</h1></header>'
                '<div class="empty-state"><p>No pieces in '
                f'<code>{html.escape(where)}</code> yet.</p>'
                f'<p>Start one: <code>{html.escape(prefix)} interview "the thing that '
                'has been rattling around"</code></p></div>')
        return page("Familiar board", body)

    waiting = sum(1 for p in pieces if p["from_log"])
    stale = sum(1 for p in pieces if p["stale"])
    now = datetime.datetime.now().strftime("%-d %B, %H:%M")
    meta = f'<b>{len(pieces)}</b> piece{"s" if len(pieces) != 1 else ""}'
    if waiting:
        meta += f', <b>{waiting}</b> with a note from you'
    if stale:
        meta += f', <b>{stale}</b> resting'
    cols = []
    for key, label in STAGES:
        inc = [p for p in pieces if p["stage"] == key]
        cols.append(
            f'<div class="col{"" if inc else " empty"}"><h2>{label}'
            f'<span>{len(inc)}</span></h2>'
            + "".join(card_html(p) for p in inc) + "</div>")
    body = (f'<header class="top"><h1>Familiar</h1>'
            f'<div class="meta">{meta} &middot; built {now}</div></header>'
            f'<div class="board">{"".join(cols)}</div>')
    return page("Familiar board", body)

# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Build a static board of every piece.")
    ap.add_argument("--pieces", action="append", default=[],
                    help="folder holding the piece folders; repeatable "
                         "(default: ./pieces, or FAMILIAR_PIECES)")
    ap.add_argument("--out", default="", help="where to write the HTML (default: <first pieces>/.board)")
    ap.add_argument("--command", default="", help="how to invoke a stage in the hint")
    ap.add_argument("--stale-days", type=int, default=7)
    ap.add_argument("--open", action="store_true", help="open the board in a browser")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent
    raw = args.pieces or [q for q in os.environ.get("FAMILIAR_PIECES", "").split(":") if q]
    dirs = [pathlib.Path(q).expanduser().resolve() for q in raw] or [root / "pieces"]
    missing = [d for d in dirs if not d.is_dir()]
    if missing:
        sys.exit("No such folder: " + ", ".join(str(m) for m in missing))

    out = pathlib.Path(args.out).expanduser() if args.out else dirs[0] / ".board"
    out.mkdir(parents=True, exist_ok=True)

    # A source label only helps when there is more than one place to confuse.
    GENERIC = {"pieces", "issues", "writing", "drafts", "posts", "content",
               "src", "docs", "documents", "projects"}
    def label(d):
        for part in [d.name] + [q.name for q in d.parents]:
            if part.lower() in GENERIC or re.match(r"^\d\d[-_]", part):
                continue
            return part
        return d.name

    now = datetime.datetime.now().timestamp()
    pieces = []
    for d in dirs:
        src = label(d) if len(dirs) > 1 else ""
        for folder in sorted((f for f in d.iterdir()
                              if f.is_dir() and not f.name.startswith(".")),
                             key=lambda f: f.name, reverse=True):
            pieces.append(gather(folder, now, args.stale_days, src))
    pieces.sort(key=lambda p: p["slug"], reverse=True)

    prefix = args.command or command_prefix(dirs[0])
    for p in pieces:
        (out / f"{p['page']}.html").write_text(piece_page(p, prefix), encoding="utf-8")
    index = out / "index.html"
    index.write_text(board_page(pieces, dirs, prefix), encoding="utf-8")

    waiting = sum(1 for p in pieces if p["ctx"].get("Decision gate"))
    print(f"{len(pieces)} piece{'s' if len(pieces) != 1 else ''}, {waiting} waiting on you")
    print(index)
    if args.open:
        webbrowser.open(index.as_uri())

if __name__ == "__main__":
    main()
