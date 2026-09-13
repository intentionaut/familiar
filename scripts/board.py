#!/usr/bin/env python3
"""Build a static board of every piece, and a page for each one.

Familiar keeps each piece as a folder of markdown. That is right for writing
and wrong for seeing what you have. This writes a plain HTML board, columns by
stage, one card per piece with its title, date and the first thing it says.
Click a card and you get the whole piece on one page: what it argues, what is
waiting on you, what is still unresolved, then the draft itself.

Nothing is sent anywhere, except a request to Google Fonts for a family the
writer names in board.md. Without --serve nothing is changed: it reads the
piece folders and writes HTML beside them.

Usage:
  scripts/board.py                      build the board and print the path
  scripts/board.py --open               build it and open it in a browser
  scripts/board.py --pieces DIR         somewhere other than ./pieces
  scripts/board.py --out DIR            somewhere other than <pieces>/.board
  scripts/board.py --command PREFIX     how to invoke a stage in the hint
  scripts/board.py --serve              serve it, so pieces can be tidied away
  scripts/board.py --stale-days N       when a piece counts as resting (7)

--serve adds an Archive control to each card. Archiving moves a piece folder
into `.archive/` beside the others. Nothing is deleted by archiving, and a
piece can be restored from the archive with one click. Deleting for good is
only possible from the archive, which means no single action can destroy work
you can still see.

--serve also makes each piece's page a document to write in. Every paragraph
is typed into where it sits, showing its markdown while the cursor is in it,
and the draft saves itself. Select any words to comment on them; comments wait
until they are sent to an agent session (scripts/rework.py), and the agent's
suggestions come back beside the paragraph to accept, edit, reply to or
reject. Picks and the open question are answered there too.
scripts/board_edit.py holds the rules each write follows.

Pieces can live in more than one place. Pass --pieces once per folder, or set
FAMILIAR_PIECES to a colon-separated list. When there is more than one, each
card says which folder it came from:

  scripts/board.py --open \
    --pieces ~/Documents/Dex/04-Projects/Writing \
    --pieces ~/Projects/intentionaut-newsroom/issues
"""
import argparse, datetime, html, json, os, pathlib, re, secrets, shutil, sys, threading, webbrowser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from paths import pieces_dirs as resolved_pieces, knowledge_dir  # noqa: E402
import board_edit  # noqa: E402

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

def md_to_html(md, track=False):
    """Render Markdown for reading.

    With track, every top-level block carries data-l="start-end": the lines of
    md it came from, end exclusive. That is how the served board hands the
    writer exactly the lines behind a paragraph, and puts them back in the same
    place, without trying to turn HTML back into Markdown.
    """
    out, lines, i = [], md.split("\n"), 0
    list_stack = []
    list_open = []          # where the outermost list's tag sits in out, and its first line

    def at(start, end):
        return f' data-l="{start}-{end}"' if track else ""

    def close_lists(to=0):
        while len(list_stack) > to:
            out.append(f"</{list_stack.pop()}>")
        if to == 0 and list_open:
            idx, start = list_open
            out[idx] = out[idx][:-1] + at(start, i) + ">"
            list_open.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            close_lists()
            start = i
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i])); i += 1
            i += 1
            out.append(f"<pre{at(start, min(i, len(lines)))}><code>"
                       + "\n".join(buf) + "</code></pre>")
            continue

        if not stripped:
            close_lists(); i += 1; continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            close_lists(); out.append(f"<hr{at(i, i + 1)}>"); i += 1; continue

        m = re.match(r"(#{1,6})\s+(.*)", stripped)
        if m:
            close_lists()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}{at(i, i + 1)}>{_inline(m.group(2))}</h{lvl}>")
            i += 1; continue

        if stripped.startswith(">"):
            close_lists()
            start, buf = i, []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append(f"<blockquote{at(start, i)}>" + _inline(" ".join(buf)) + "</blockquote>")
            continue

        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)", line)
        if m:
            indent = len(m.group(1)) // 2 + 1
            kind = "ul" if m.group(2) in "-*+" else "ol"
            if indent > len(list_stack):
                if not list_stack:
                    list_open[:] = [len(out), i]
                out.append(f"<{kind}>"); list_stack.append(kind)
            elif indent < len(list_stack):
                close_lists(indent)
            out.append(f"<li>{_inline(m.group(3))}</li>")
            i += 1; continue

        close_lists()
        start, buf = i, []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^\s*([-*+]|\d+[.)])\s|^#{1,6}\s|^>|^```", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        if not buf:
            # A line none of the rules above could place. Show it as text
            # rather than stall on it.
            buf.append(stripped); i += 1
        out.append(f"<p{at(start, i)}>" + _inline(" ".join(buf)) + "</p>")

    close_lists()
    return "\n".join(out)

# --------------------------------------------------------------------------
# Reading a piece
# --------------------------------------------------------------------------

def safe_name(*parts):
    """A filename that survives being linked to.

    Piece folders are named by the writer and can hold spaces, ampersands and
    anything else a filesystem allows. A page named after one has to be
    reduced to characters that need no escaping in a URL.
    """
    raw = "--".join(q for q in parts if q)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-.")
    return name or "piece"

def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def frontmatter_span(md):
    """((first, last) line of the frontmatter block, its fields), or (None, {}).

    A draft does not always start with its frontmatter. A smoke-test warning or
    an editor's note above it is common, and the title still has to be found.
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
            # No fields means a horizontal rule, not frontmatter.
            return ((start, end), fm) if fm else (None, {})
        break
    return None, {}


def frontmatter(md):
    """Pull a YAML-ish block out, even when a note sits above it.

    Anything above the block is kept, because a note there is worth reading.
    """
    span, fm = frontmatter_span(md)
    if not span:
        return {}, md
    lines = md.split("\n")
    before = "\n".join(lines[:span[0]]).strip()
    after = "\n".join(lines[span[1] + 1:]).lstrip("\n")
    return fm, (before + "\n\n" + after).lstrip("\n") if before else after

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

def derive_stage(folder, brackets=0, has_draft=True, reworking=False):
    """has_draft is False when draft.md exists but holds nothing to read.

    An empty file is a placeholder, and calling it a draft sends the writer to
    a developmental edit of nothing. A section in rework means the writer has
    asked for changes, so the piece is still being edited.
    """
    has = lambda *p: (folder.joinpath(*p)).exists() and (
        p != ("draft.md",) or has_draft)
    mtime = lambda *p: (folder.joinpath(*p)).stat().st_mtime
    if has("final.md"):
        return "sent"
    if has("draft.md"):
        if brackets or reworking:
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


def next_action(folder, state, brackets, has_social, has_draft=True, asked=0, proposed=0,
                noted=0):
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
        if proposed:
            return f"{proposed} suggestion{'s' if proposed != 1 else ''} came back for you"
        if noted:
            return f"{noted} comment{'s' if noted != 1 else ''} not sent to your agent yet"
        if asked:
            return f"{asked} comment{'s' if asked != 1 else ''} with your agent"
        if has("draft.md"):
            d = mtime("draft.md")
            for r, name in (("edits/line-edit-report.md", "line edit"),
                            ("edits/dev-edit-report.md", "developmental edit")):
                if has(*r.split("/")) and mtime(*r.split("/")) > d:
                    return f"Work through the {name}, flag by flag"
            return "Ask for a developmental edit"
        return "Work through the edit report"
    if state == "writing":
        if (folder / "draft.md").exists() and not has_draft:
            return "The draft file is empty. Write it, or delete the file"
        if (folder / "outline.md").exists():
            return "Write the draft from the structure you chose"
        return "Write the draft"
    stub = (folder / "draft.md").exists() and not has_draft
    if has("notes.md"):
        return ("Ask for three structures and pick one"
                + (", and clear out the empty draft file" if stub else ""))
    if stub:
        return "There is an empty draft file and nothing else. Start the interview"
    if has("interview-questions.md") or has("brief.md"):
        return "Run the interview from the questions"
    return "Start the interview"

def read_cuts(folder):
    """Cuts made during the writing, from cuts.md.

    One entry per H3, with a Flag: line of dead, reusable or blocked. Only
    reusable ones are surfaced: a dead cut is settled and a blocked one is
    waiting on something the board cannot see.
    """
    raw = read(folder / "cuts.md")
    if not raw:
        return []
    out = []
    for block in re.split(r"^###\s+", raw, flags=re.M)[1:]:
        head, _, rest = block.partition("\n")
        flag = ""
        m = re.search(r"^\s*(?:\*\*)?Flag(?:\*\*)?:\s*(\w+)", rest, re.M | re.I)
        if m:
            flag = m.group(1).lower()
        why = ""
        m = re.search(r"^\s*(?:\*\*)?Why(?:\*\*)?:\s*(.+)", rest, re.M | re.I)
        if m:
            why = m.group(1).strip()
        out.append({"what": head.strip(), "flag": flag, "why": why})
    return out


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
    # A piece that came in through /bring has prose before it has notes. Its
    # spine is where the argument is written down, so it stands in for both.
    spine = read(folder / "spine.md")

    title = fm.get("title") or ""
    if not title:
        m = re.search(r"^#\s+(.+)", notes or outline or spine, re.M)
        title = re.sub(r"^Spine:\s*", "", m.group(1)) if m else ""
    if not title:
        words = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", folder.name).replace("-", " ").strip()
        title = (words[:1].upper() + words[1:]) if words else folder.name

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
    if not snippet and spine:
        m = re.search(r"^##\s*The argument as found\s*\n+(.+?)(?=\n#|\Z)", spine, re.S | re.M)
        if m:
            snippet = m.group(1).strip()
    if not snippet:
        for para in (notes or outline or spine).split("\n\n"):
            para = para.strip()
            if para and not para.startswith(("#", ">", "-", "*", "```", "|")):
                snippet = para; break
    # Snippets are plain text, so emphasis markers would show as asterisks.
    snippet = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", snippet)
    snippet = " ".join(snippet.split())
    if len(snippet) > 240:
        snippet = snippet[:237].rsplit(" ", 1)[0] + "..."

    cuts = read_cuts(folder)
    ctx = last_context_entry(folder)
    ts = newest_mtime(folder)
    words, fre = reading_ease(re.sub(r"\[(NEEDS SOURCE|ASK THE WRITER)[^\]]*\]", "", draft_body))
    brackets = re.findall(r"\[(?:NEEDS SOURCE|ASK THE WRITER)[^\]]*\]", draft_raw)
    has_draft = bool(draft_body.strip())
    rework = board_edit.read_rework(folder)
    waiting = {k: r for k, r in rework.items() if board_edit.state(r) != "closed"}
    kinds = [board_edit.state(r) for r in waiting.values()]
    asked, proposed, noted = kinds.count("asked"), kinds.count("proposed"), kinds.count("noted")
    state = derive_stage(folder, len(brackets), has_draft, bool(waiting))
    # The writer's own words win. The derived action is the fallback, and for
    # most pieces it is all there is.
    derived = next_action(folder, state, brackets,
                          (folder / "social.md").exists(), has_draft,
                          asked, proposed, noted)
    cmd = NEXT_COMMAND.get(state, "")
    if state == "editing" and waiting and not brackets:
        # A proposal waiting is the writer's move, on the board. A request
        # waiting is an agent's, answered from the command line.
        cmd = "familiar rework watch" if asked else ""
    gate = ctx.get("Decision gate", "")
    action = gate or derived
    from_log = bool(gate)

    return {
        "slug": folder.name, "folder": folder, "title": title, "date": date,
        "source": source, "page": safe_name(source, folder.name),
        "snippet": snippet, "stage": state, "ts": ts,
        "action": action, "from_log": from_log,
        "ago": ago(ts, now), "stale": (now - ts) > stale_days * 86400,
        "ctx": ctx, "words": words, "fre": fre, "brackets": brackets,
        "cuts": cuts,
        "reusable": [c for c in cuts if c["flag"] == "reusable"],
        "rework": waiting, "reworking": len(waiting),
        "cmd": cmd,
        "subtitle": fm.get("subtitle", ""),
        # Kept versions live in .versions/ and are not the piece's files.
        "files": sorted(p.relative_to(folder).as_posix()
                        for p in folder.rglob("*")
                        if p.is_file() and not any(
                            x.startswith(".") for x in p.relative_to(folder).parts)),
    }

# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------

# The board's own light colours. A writer's board.md can replace any of them.
LIGHT = {"paper": "#faf7f4", "card": "#fff", "ink": "#2b2233", "muted": "#6f6478",
         "line": "#e6ded9", "accent": "#c4506a", "warn": "#a8651f", "ok": "#4a7c59"}

CSS = """
:root{__LIGHT__;--shadow:0 1px 2px rgba(43,34,51,.06),0 8px 24px -16px rgba(43,34,51,.4)}
@media(prefers-color-scheme:dark){:root{--paper:#16131a;--card:#1e1a24;--ink:#ece7f0;
--muted:#9d93a8;--line:#2e2836;--accent:#e8899f;--warn:#d9a05b;--ok:#7fb98d;
--shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px -16px #000}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.6 ui-sans-serif,-apple-system,"Segoe UI",system-ui,sans-serif;
-webkit-font-smoothing:antialiased}
a{color:inherit}
.tools{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.tools button{font:inherit;font-size:.78rem;color:var(--muted);background:transparent;
border:1px solid var(--line);border-radius:6px;padding:2px 8px;cursor:pointer}
.tools button:hover,.tools .filelink:hover{color:var(--ink);border-color:var(--muted)}
.tools .filelink{font-size:.78rem;color:var(--muted);border:1px solid var(--line);border-radius:6px;padding:2px 8px;text-decoration:none}
label.filter{font-size:.85rem;color:var(--muted);display:flex;align-items:center;gap:6px;cursor:pointer}
body.waiting-only .card:not([data-waiting]){display:none}
body.waiting-only .col:has(.card:not([data-waiting])):not(:has(.card[data-waiting])) h2 span{opacity:.4}
.pill.reuse{background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}
ul.cuts{margin:0;padding-left:18px}
ul.cuts li{margin:.3em 0}
ul.cuts .why{display:block;color:var(--muted);font-size:.9em}
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
padding:16px 18px;margin-bottom:24px}
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
/* interactive */
.card{position:relative}
.act{position:absolute;top:10px;right:10px;opacity:0;transition:opacity .12s ease}
.card:hover .act,.act:focus-within{opacity:1}
.act button{font:inherit;font-size:.72rem;color:var(--muted);background:var(--paper);
border:1px solid var(--line);border-radius:999px;padding:2px 9px;cursor:pointer}
.act button:hover{color:var(--accent);border-color:var(--accent)}
.arch{margin:8px 32px 56px;max-width:900px}
.arch>summary{cursor:pointer;color:var(--muted);font-size:.8rem;
text-transform:uppercase;letter-spacing:.09em;font-weight:700;list-style:none;padding:8px 0}
.arch>summary::-webkit-details-marker{display:none}
.arch>summary:hover{color:var(--accent)}
.arow{display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--card);
border:1px solid var(--line);border-radius:10px;margin-bottom:8px;flex-wrap:wrap}
.arow .t{font-weight:600;flex:1;min-width:180px}
.arow .when{color:var(--muted);font-size:.8rem}
.arow button{font:inherit;font-size:.78rem;padding:3px 10px;border-radius:999px;
border:1px solid var(--line);background:var(--paper);color:var(--muted);cursor:pointer}
.arow button:hover{border-color:var(--accent);color:var(--accent)}
.arow button.danger:hover{border-color:#c0392b;color:#c0392b}
#toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:var(--ink);
color:var(--paper);padding:10px 16px;border-radius:999px;font-size:.85rem;display:none;
align-items:center;gap:14px;box-shadow:0 12px 32px -12px rgba(0,0,0,.5);z-index:20}
#toast button{font:inherit;font-size:.82rem;background:none;border:0;color:var(--paper);
text-decoration:underline;cursor:pointer;padding:0}
.pill.noted{color:var(--accent);border-color:var(--accent)}
details.ask>summary,details.flags>summary,details.everything>summary{cursor:pointer;color:var(--muted);
font-size:.85rem;list-style:none;padding:4px 0}
details.ask>summary::-webkit-details-marker,details.flags>summary::-webkit-details-marker,
details.everything>summary::-webkit-details-marker{display:none}
details.ask>summary::before{content:"+ "}
details.ask[open]>summary::before{content:"\u2212 "}
details.ask>summary:hover,details.flags>summary:hover,details.everything>summary:hover{color:var(--accent)}
details.ask textarea,form.inline textarea{display:block;width:100%;font:inherit;font-size:.95rem;
color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:10px 12px;margin:6px 0 8px;resize:vertical}
.flag{padding:8px 0;border-top:1px dashed var(--line);font-size:.9rem}
.flag details summary{cursor:pointer;color:var(--muted);font-size:.8rem}
.panel.waitnote code{white-space:normal}
details.everything{margin-top:32px}
.gate{border-left:3px solid var(--accent);padding:2px 0 2px 14px;margin:0 0 24px}
.gate.quiet{border-left-color:var(--line)}
.gate .label{display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;
color:var(--muted);font-weight:700}
.gate p{margin:2px 0 0}
.docbar{position:sticky;top:0;z-index:6;display:flex;align-items:center;gap:12px;flex-wrap:wrap;
padding:10px 0;margin:28px 0 12px;background:var(--paper);border-bottom:1px solid var(--line)}
.docbar .tools{margin-left:auto}
.banner{border:1px solid var(--warn);background:color-mix(in srgb,var(--warn) 10%,var(--card));
border-radius:10px;padding:12px 14px;margin:0 0 16px;font-size:.92rem}
.banner p{margin:0 0 8px}
article.doc{font-size:1.04rem;line-height:1.72}
.blk{border-radius:6px;padding:2px 10px;margin:0 -10px 1.1em;cursor:text;min-height:1.7em;
transition:background-color .1s}
.blk:hover{background:color-mix(in srgb,var(--ink) 4%,transparent)}
.blk>:first-child{margin-top:0}
.blk>:last-child{margin-bottom:0}
.blk.editing,.blk.pending{white-space:pre-wrap;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
font-size:.9rem;line-height:1.7}
.blk.editing{background:var(--card);outline:1px solid var(--accent);box-shadow:var(--shadow)}
.blk.pending{color:var(--muted)}
.blk.composer{min-height:3em}
.blk.composer:empty::before{content:"Write here";color:var(--muted)}
.threads{margin:-6px 0 18px}
.cmt{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;
background:var(--card);padding:10px 12px;margin:0 0 8px;font-size:.9rem;line-height:1.5}
.cmt.k-noted{border-left-color:var(--muted)}
.cmt .q{margin:0 0 6px;color:var(--muted);font-style:italic}
.cmt .said{margin:0 0 6px;white-space:pre-wrap}
.cmt .said.agent{color:var(--muted)}
.cmt .state{margin:0 0 6px;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;
color:var(--muted);font-weight:600}
.diff{white-space:pre-wrap;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85rem;
line-height:1.6;background:var(--paper);border-radius:6px;padding:8px 10px;margin:0 0 8px}
.diff del{color:#a33b36;background:color-mix(in srgb,#a33b36 10%,transparent)}
.diff ins{color:var(--ok);background:color-mix(in srgb,var(--ok) 12%,transparent)}
mark.c{background:color-mix(in srgb,var(--accent) 18%,transparent);color:inherit;border-radius:2px}
#notepop .filter{margin:0 0 8px}
/* editing, when served */
.hint{color:var(--muted);font-size:.78rem}
.tools button.primary{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.tools button.primary:hover{background:var(--accent);border-color:var(--accent);color:#fff}
.tools button:disabled{opacity:.5;cursor:default}
.tools{align-items:center}
.panel textarea,.panel input[type=text],#notepop textarea{display:block;width:100%;
font:inherit;font-size:.92rem;color:var(--ink);background:var(--paper);border:1px solid var(--line);
border-radius:8px;padding:8px 10px;margin:6px 0 8px;resize:vertical}
.panel textarea:focus,.panel input:focus,#notepop textarea:focus{
outline:2px solid color-mix(in srgb,var(--accent) 35%,transparent);border-color:var(--accent)}
.opt{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border:1px solid var(--line);
border-radius:10px;margin:8px 0;cursor:pointer;background:var(--paper)}
.opt:has(input:checked){border-color:var(--accent);background:color-mix(in srgb,var(--accent) 5%,var(--card))}
.opt input{margin-top:.35em;accent-color:var(--accent)}
.opt .label{display:block;font-weight:640;margin-bottom:2px}
.draft.small{font-size:.88rem;line-height:1.55}
.draft.small p,.draft.small blockquote,.draft.small ul{margin:0 0 .6em}
.draft.small pre{font-size:.78rem;white-space:pre-wrap;margin:.4em 0}
.drafthead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:36px 0 8px}
.drafthead .label{margin:0;font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted)}
.drafthead .tools{margin:0 0 0 auto}
#notebtn{position:absolute;z-index:30;font:inherit;font-size:.8rem;padding:4px 12px;border-radius:999px;
border:0;background:var(--ink);color:var(--paper);cursor:pointer;box-shadow:var(--shadow)}
#notepop{position:absolute;z-index:31;background:var(--card);border:1px solid var(--line);
border-radius:12px;box-shadow:0 12px 32px -12px rgba(0,0,0,.35);padding:10px 12px;
width:min(340px,calc(100vw - 32px))}
#notepop q{display:block;color:var(--muted);font-size:.82rem;font-style:italic}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""
CSS = CSS.replace("__LIGHT__", ";".join(f"--{k}:{v}" for k, v in LIGHT.items()))

BOARD_JS = """
// Copy to clipboard. navigator.clipboard needs a secure context and the board
// is usually opened as a file, so fall back to the old way rather than fail.
function copyText(text, btn) {
  const done = () => {
    const was = btn.textContent;
    btn.textContent = "copied";
    setTimeout(() => { btn.textContent = was; }, 1200);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done, () => fallback(text, done));
  } else { fallback(text, done); }
}
function fallback(text, done) {
  const ta = document.createElement("textarea");
  ta.value = text; ta.setAttribute("readonly", "");
  ta.style.position = "fixed"; ta.style.opacity = "0";
  document.body.appendChild(ta); ta.select();
  try { document.execCommand("copy"); done(); } catch (e) {}
  document.body.removeChild(ta);
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-copy]");
  if (!b) return;
  e.preventDefault(); e.stopPropagation();
  copyText(b.getAttribute("data-copy"), b);
});

// Show only the pieces carrying a note from the writer.
document.addEventListener("change", (e) => {
  if (e.target.id !== "waiting-only") return;
  document.body.classList.toggle("waiting-only", e.target.checked);
  try { localStorage.setItem("familiarWaitingOnly", e.target.checked ? "1" : ""); } catch (err) {}
});
try {
  if (localStorage.getItem("familiarWaitingOnly")) {
    const box = document.getElementById("waiting-only");
    if (box) { box.checked = true; document.body.classList.add("waiting-only"); }
  }
} catch (err) {}
"""


# --------------------------------------------------------------------------
# The writer's own look
#
# A writer can give the board their publication's colours and fonts in
# board.md, in the house. Nothing about any one writer's brand belongs here.
# --------------------------------------------------------------------------

SAFE_COLOUR = re.compile(r"^[#\w\s(),.%/-]+$")
SAFE_FONT = re.compile(r"""^[\w\s,'"-]+$""")
# A family name, optionally with Google's axis list after a colon (wght@400;700).
GOOGLE_FONT = re.compile(r"[A-Za-z0-9 ]{1,60}(:[A-Za-z0-9,@;.]{1,60})?")


def read_theme(path=None):
    """The look declared in the house's board.md, or {} when there is none.

    One setting per line, `Paper: #f6f4ef`, at the start of the line. A value
    that could break out of the stylesheet is ignored rather than used: the
    file is plain text edited by hand, and one stray brace would take the
    whole board's styling with it.
    """
    if path is None:
        path = knowledge_dir()[0] / "board.md"
    got = {}
    for m in re.finditer(r"(?m)^([A-Za-z][A-Za-z ]*?):[ \t]*(\S.*?)\s*$", read(path)):
        key, val = m.group(1).strip().lower(), m.group(2)
        if key in LIGHT and SAFE_COLOUR.match(val):
            got[key] = val
        elif key == "scheme" and val.lower() in ("light", "system"):
            got["scheme"] = val.lower()
        elif key in ("font", "display font") and SAFE_FONT.match(val):
            got[key] = val
        elif key == "google fonts":
            names = [n.strip() for n in val.split(",") if n.strip()]
            if names and all(GOOGLE_FONT.fullmatch(n) for n in names):
                got[key] = names
        elif key == "text size" and re.fullmatch(r"\d{1,2}(\.\d+)?(px|rem|pt)", val):
            got[key] = val
    return got


def theme_css(theme):
    """CSS that goes after the board's own, so the writer's settings win.

    `Scheme: light` keeps the page light in dark mode too. Otherwise the
    writer's colours are for the light page and dark mode keeps the board's
    own dark colours, since a palette drawn for a light page rarely survives
    being inverted.
    """
    colours = {k: v for k, v in theme.items() if k in LIGHT}
    out = []
    if theme.get("scheme") == "light":
        tokens = ";".join(f"--{k}:{v}" for k, v in {**LIGHT, **colours}.items())
        out.append(f":root{{{tokens};color-scheme:light}}")
    elif colours:
        tokens = ";".join(f"--{k}:{v}" for k, v in colours.items())
        out.append(f"@media(prefers-color-scheme:light){{:root{{{tokens}}}}}")
    if theme.get("font"):
        out.append(f"body{{font-family:{theme['font']}}}")
    if theme.get("text size"):
        out.append(f"article.draft,article.doc{{font-size:{theme['text size']}}}")
    if theme.get("display font"):
        out.append("header.top h1,.piece-head h1,.card h3,article.draft h1,"
                   f"article.draft h2,article.draft h3{{font-family:{theme['display font']}}}")
    return "\n".join(out)


def fonts_link(theme):
    """The Google Fonts stylesheet for the families named in board.md, or nothing.

    The one thing the board fetches from outside this machine, and only because
    the writer asked for a font by name.
    """
    names = theme.get("google fonts")
    if not names:
        return ""
    q = "&".join("family=" + n.replace(" ", "+") for n in names)
    return ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{q}&display=swap">')


def page(title, body, css_depth=0):
    theme = read_theme()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
{fonts_link(theme)}<style>{CSS}{theme_css(theme)}</style></head><body>
{body}
<script>{BOARD_JS}</script>
</body></html>"""

def shown_command(cmd, prefix):
    """A stage command as this writer invokes it. `familiar rework` is the
    command line itself rather than a stage, so it is shown as it is."""
    if not cmd or prefix == "familiar" or cmd.startswith("familiar rework"):
        return cmd
    return f"{prefix} {cmd.split(' ', 1)[1]}"


def card_html(p, token="", prefix="familiar"):
    pills = [f'<span class="pill">{html.escape(p["date"] or "no date")}</span>',
             f'<span class="pill{" stale" if p["stale"] else ""}">{p["ago"]}</span>']
    if p["brackets"]:
        n = len(p["brackets"])
        pills.append(f'<span class="pill brk">{n} bracket{"s" if n != 1 else ""}</span>')
    if p["reusable"]:
        n = len(p["reusable"])
        pills.append(f'<span class="pill reuse">{n} to revive</span>')
    if p["reworking"]:
        n = p["reworking"]
        pills.append(f'<span class="pill noted">{n} comment{"s" if n != 1 else ""}</span>')
    if p["source"]:
        pills.append(f'<span class="pill src">{html.escape(p["source"])}</span>')
    label = "Waiting on you" if p["from_log"] else "Next"
    w = (f'<div class="waiting{"" if p["from_log"] else " derived"}">'
         f'<b>{label}</b>{html.escape(p["action"])}</div>')
    act = ""
    if token:
        buttons = ('<button data-act="archive" title="Move it out of the way, '
                   'reversibly">Archive</button>')
        if p["stage"] != "sent":
            buttons += ('<button class="danger" data-act="delete" '
                        'title="Delete the folder">Delete</button>')
        act = f'<span class="act">{buttons}</span>' 
    # The card is one big link, so these are buttons rather than nested anchors.
    # Both copy: opening a local file from a page is blocked in most browsers,
    # and a path on the clipboard works everywhere the board does.
    cmd = p["cmd"].format(slug=p["slug"])
    tools = []
    if cmd:
        full = shown_command(cmd, prefix)
        tools.append(f'<button data-copy="{html.escape(full, quote=True)}" '
                     f'title="Copy the command for what this piece needs next">'
                     f'copy command</button>')
    draft = p["folder"] / "draft.md"
    if draft.is_file():
        tools.append(f'<button data-copy="{html.escape(str(draft), quote=True)}" '
                     f'title="Copy the path to the draft">copy path</button>')
    tool_row = f'<div class="tools">{"".join(tools)}</div>' if tools else ""
    waiting_attr = ' data-waiting="1"' if p["from_log"] else ""
    return f"""<a class="card" href="{html.escape(p['page'])}.html" data-id="{html.escape(p['page'])}"{waiting_attr}>{act}
  <h3>{html.escape(p['title'])}</h3>
  <div class="sub">{''.join(pills)}</div>
  <p>{html.escape(p['snippet']) or '<span class="none">nothing written yet</span>'}</p>
  {w}
  {tool_row}
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

def piece_head(p):
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

    parts = ['<div class="piece-head">', f'<h1>{html.escape(p["title"])}</h1>']
    if p["subtitle"]:
        parts.append(f'<p class="sub">{html.escape(p["subtitle"])}</p>')
    parts.append(f'<div class="facts">{"".join(facts)}</div></div>')
    return "".join(parts)


def last_touched(p):
    ctx = p["ctx"]
    if ctx.get("when"):
        return (f'<p class="none">Last touched by {html.escape(ctx.get("stage", ""))} '
                f'on {html.escape(ctx.get("when", ""))}.</p>')
    return ('<p class="none">Worked out from the files. This piece has no '
            'context log yet, so no stage has left a note.</p>')


def brackets_panel(p):
    if not p["brackets"]:
        return ""
    items = "".join(f"<li>{_inline(b)}</li>" for b in p["brackets"])
    return f'<div class="panel"><h2>Still unresolved</h2><ul>{items}</ul></div>'


def pick_up_panel(p, prefix):
    cmd = p["cmd"].format(slug=p["slug"])
    cmd = shown_command(cmd, prefix)
    return (
        '<div class="panel next"><h2>Pick it back up</h2>'
        f'<p>The piece is at <b>{html.escape(dict(STAGES)[p["stage"]])}</b>. '
        'Open the draft, or run the next stage.</p>'
        f'<code>{html.escape(str(p["folder"]))}</code>'
        + (f'<code>{html.escape(cmd)}</code>' if cmd else "")
        # Nothing wraps this page in a link, so a real file link is valid here.
        # It opens when the board is viewed as a file, which is the default.
        + '<div class="tools">'
        + (f'<a class="filelink" href="file://{html.escape(str(p["folder"] / "draft.md"))}">'
           'open draft.md</a>' if (p["folder"] / "draft.md").is_file() else "")
        + (f'<button data-copy="{html.escape(cmd, quote=True)}">copy command</button>'
           if cmd else "")
        + f'<button data-copy="{html.escape(str(p["folder"]), quote=True)}">copy folder</button>'
        + '</div>'
        + '</div>')


def supporting_html(p):
    """Supporting files, folded away."""
    parts = []
    for name, label in (("spine.md", "The spine it came in with"),
                        ("notes.md", "Notes from the interview"),
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
    return "".join(parts)


def piece_page(p, prefix="familiar", token=""):
    if token:
        return edit_page(p, prefix, token)
    parts = ['<a class="back" href="index.html">&larr; all pieces</a>', piece_head(p)]

    if p["reusable"]:
        rows = "".join(
            f'<li><b>{html.escape(c["what"])}</b>'
            + (f'<span class="why">{html.escape(c["why"])}</span>' if c["why"] else "")
            + '</li>'
            for c in p["reusable"])
        parts.append('<div class="panel"><h2>Cut, and worth reviving</h2>'
                     f'<ul class="cuts">{rows}</ul></div>')

    parts.append(
        f'<div class="panel"><h2>{"Waiting on you" if p["from_log"] else "Next"}</h2>'
        f'<p>{html.escape(p["action"])}</p>' + last_touched(p) + '</div>')
    parts.append(brackets_panel(p))
    parts.append(pick_up_panel(p, prefix))
    parts.append(supporting_html(p))

    draft_raw = read(p["folder"] / "draft.md")
    if draft_raw.strip():
        _, body = frontmatter(draft_raw)
        parts.append('<h2 style="margin:36px 0 4px;font-size:.72rem;text-transform:uppercase;'
                     'letter-spacing:.09em;color:var(--muted)">The draft</h2>')
        parts.append(f'<article class="draft">{md_to_html(body)}</article>')
    else:
        parts.append('<p class="none">No draft yet.</p>')

    return page(p["title"], f'<div class="wrap">{"".join(parts)}</div>')


REPORT_NAMES = {"dev-edit": "dev edit", "line-edit": "line edit"}
WATCH_ASK = ("Answer the comments on the Familiar board, and keep watching for more "
             "(familiar rework watch).")


def report_label(rel):
    m = re.match(r"edits/(.+?)-report(?:-(\d+))?\.md$", rel)
    if not m:
        return rel
    name = REPORT_NAMES.get(m.group(1), m.group(1).replace("-", " "))
    return name + (f" {m.group(2)}" if m.group(2) else "")


def rework_version(folder):
    """What an open page compares against to notice a change: the comments,
    which an agent writes, and the draft, which another editor might."""
    return {"rework": board_edit.digest(board_edit.read_soft(folder / board_edit.REWORK)),
            "draft": board_edit.digest(board_edit.read_soft(folder / "draft.md"))}


def edit_page(p, prefix, token):
    """A piece's page when the board is served: the draft as a document you write in.

    Every paragraph is typed into where it sits, and shows its markdown while
    the cursor is in it, so nothing is converted and nothing is lost on the way
    back to the file. The document saves itself a moment after typing stops.
    Select any words to comment on them; comments wait until they are sent to an
    agent, and what the agent suggests comes back beside the paragraph, to
    accept, edit, reply to or reject. What has been typed and not yet saved is
    held in the browser until it has been.
    """
    esc = lambda s: html.escape(s or "", quote=True)
    folder = p["folder"]
    sent = (folder / "final.md").exists()
    try:
        raw, readable = board_edit.read_exact(folder / "draft.md"), True
    except board_edit.Refused:
        raw, readable = read(folder / "draft.md"), False
    workable = readable and not sent and "\r" not in raw

    main = ['<a class="back" href="index.html">&larr; all pieces</a>', piece_head(p)]
    if p["from_log"]:
        main.append(
            '<div class="gate"><span class="label">Waiting on you</span>'
            f'<p>{esc(p["action"])}</p>'
            '<details class="ask"><summary>Answer it</summary>'
            '<form data-form="answer"><textarea name="answer" rows="3" '
            'aria-label="Your answer" placeholder="Your answer, in your words"></textarea>'
            '<div class="tools"><button class="primary" type="submit">Record answer</button>'
            '<span class="hint">Goes into the context log as you wrote it. No stage runs.</span>'
            '</div></form></details></div>')
    else:
        main.append(f'<div class="gate quiet"><span class="label">Next</span>'
                    f'<p>{esc(p["action"])}</p></div>')

    for rel, idx, s in board_edit.open_option_sets(folder):
        opts = "".join(
            f'<label class="opt"><input type="radio" name="letter" value="{esc(o["letter"])}">'
            f'<div><span class="label">{esc(o["letter"])}. {esc(o["label"])}</span>'
            f'<div class="draft small">{md_to_html(o["body"])}</div></div></label>'
            for o in s["options"])
        main.append(
            f'<form class="panel" data-form="choose" data-file="{esc(rel)}" '
            f'data-set="{esc(s["title"])}" data-index="{idx}">'
            f'<h2>Choose: {esc(s["title"])}</h2>{opts}'
            '<input type="text" name="because" aria-label="Because" '
            'placeholder="Because, in your words">'
            '<div class="tools"><button class="primary" type="submit">Record pick</button>'
            '<label class="filter"><input type="checkbox" name="nogiven"> no reason given</label>'
            '</div></form>')

    _, bl = board_edit.blocks(raw) if raw.strip() else (0, [])
    placed, proposals = {}, {}
    for tid, rounds in p["rework"].items():
        target = board_edit.target_of(raw, rounds)
        if rounds[0]["fields"].get("Whole") == "yes":
            where = "whole"
        else:
            where = next((k for k, b in enumerate(bl) if target and b["start"] == target["start"]),
                         None)
        placed.setdefault(where, []).append((tid, rounds))
        if rounds[-1]["kind"] == "proposed":
            proposals[tid] = {"from": target["text"] if target else "", "to": rounds[-1]["body"]}
    flags = {}
    if workable:
        for rel, fs in board_edit.report_flags(folder):
            for f in fs:
                flags.setdefault(board_edit.flag_block(f, bl), []).append((rel, f))
    kinds = [board_edit.state(r) for r in p["rework"].values()]
    noted, asked = kinds.count("noted"), kinds.count("asked")

    def card(tid, rounds):
        first, last = rounds[0], rounds[-1]
        quote = first["fields"].get("Quote")
        said = [first["body"]] + [r["body"] for r in rounds[1:] if r["kind"] == "asked"]
        out = [f'<div class="cmt k-{last["kind"]}" data-thread="{tid}">']
        if quote:
            out.append(f'<p class="q">“{esc(quote)}”</p>')
        out += [f'<p class="said">{esc(s)}</p>' for s in dict.fromkeys(said)]
        if last["kind"] == "noted":
            out.append('<p class="state">Not sent yet</p><div class="tools">'
                       f'<button class="primary" data-send="{tid}">Send to Agent</button>'
                       f'<button data-drop="{tid}">Delete</button></div>')
        elif last["kind"] == "asked":
            out.append('<p class="state">With your agent</p><div class="tools">'
                       f'<button data-drop="{tid}">Withdraw</button></div>')
        else:
            note = last["fields"].get("Note")
            out.append(f'<p class="state">Suggested, round {last["n"]}</p>'
                       + (f'<p class="said agent">{esc(note)}</p>' if note else "")
                       + f'<div class="diff" data-diff="{tid}"></div><div class="tools">'
                       f'<button class="primary" data-accept="{tid}">Accept</button>'
                       f'<button data-edit="{tid}">Edit, then Accept</button>'
                       f'<button data-reply="{tid}">Reply</button>'
                       f'<button data-drop="{tid}">Reject</button></div>')
        out.append('</div>')
        return "".join(out)

    def flags_html(items, src):
        names = {report_label(r) for r, _ in items}
        where = f"the {names.pop()}" if len(names) == 1 else "the edit reports"
        rows = []
        for rel, f in items:
            send_it = ("" if src is None else
                       f'<button data-flag data-src="{esc(src)}" data-report="{esc(rel)}" '
                       f'data-key="{esc(f["key"])}">Send to Agent</button>')
            rows.append(f'<div class="flag"><div><b>{esc(f["label"])}</b> {esc(f["title"])}</div>'
                        f'<details><summary>the finding</summary><div class="draft small">'
                        f'{md_to_html(f["body"])}</div></details>'
                        f'<div class="tools">{send_it}</div></div>')
        n = len(items)
        return (f'<details class="flags"><summary>{n} finding{"s" if n != 1 else ""} from '
                f'{where}</summary>{"".join(rows)}</details>')

    if raw.strip() and workable:
        main.append(
            '<div class="docbar"><span class="hint" id="savestate"></span><span class="tools">'
            '<button type="button" data-whole>Comment on the Whole Draft</button>'
            f'<button type="button" class="primary" id="sendall"{"" if noted else " hidden"}>'
            f'Send {noted} Comment{"s" if noted != 1 else ""}</button></span></div>'
            '<div id="banner" class="banner" hidden></div>')
        if asked:
            main.append(
                f'<div class="panel waitnote"><p><b>{asked} with your agent.</b> If no session '
                'is watching, paste this into one:</p>'
                f'<code>{esc(WATCH_ASK)}</code><div class="tools">'
                f'<button data-copy="{esc(WATCH_ASK)}">copy</button></div></div>')
        doc = ['<article class="doc draft" id="doc">']
        if placed.get("whole"):
            doc.append('<div class="threads">' + "".join(card(t, r) for t, r in placed["whole"])
                       + '</div>')
        for k, b in enumerate(bl):
            doc.append(f'<div class="blk" data-src="{esc(b["text"])}">{md_to_html(b["text"])}</div>')
            if placed.get(k):
                doc.append('<div class="threads">' + "".join(card(t, r) for t, r in placed[k])
                           + '</div>')
            if flags.get(k):
                doc.append(flags_html(flags[k], b["text"]))
        doc.append('<div class="blk composer" data-src=""></div></article>')
        main.append("".join(doc))
        if placed.get(None):
            main.append('<div class="panel"><h2>Comments whose words have left the draft</h2>'
                        + "".join(card(t, r) for t, r in placed[None]) + '</div>')
        if flags.get(None):
            main.append('<div class="panel"><h2>About the whole piece</h2>'
                        + flags_html(flags[None], None) + '</div>')
    elif raw.strip():
        why = ("Sent, so the draft stays as it is: it is what learn diff compares with what "
               "went out." if sent else
               "draft.md has Windows line endings or is not UTF-8 text, so it can be read "
               "here and not edited.")
        _, body = frontmatter(raw)
        main.append(f'<div class="drafthead"><h2 class="label">The draft</h2>'
                    f'<span class="hint">{why}</span></div>'
                    f'<article class="draft">{md_to_html(body)}</article>')
    else:
        main.append('<p class="none">No draft yet.</p>')

    more = [pick_up_panel(p, prefix), supporting_html(p)]
    if p["cuts"]:
        rows = "".join(f'<li><b>{esc(c["what"])}</b> <span class="pill">{esc(c["flag"] or "no flag")}</span>'
                       + (f'<span class="why">{esc(c["why"])}</span>' if c["why"] else "") + '</li>'
                       for c in p["cuts"])
        more.append(f'<div class="panel"><h2>Cuts</h2><ul class="cuts">{rows}</ul></div>')
    kept = len(board_edit.versions(folder))
    if kept:
        more.append(f'<p class="none">{kept} earlier version{"s" if kept != 1 else ""} of the '
                    'draft kept in <code>.versions/</code> in the piece folder.</p>')
    main.append('<details class="everything"><summary>Everything else in the piece</summary>'
                + "".join(more) + '</details>')

    version = rework_version(folder)
    data = {"id": p["page"], "token": token, "hash": board_edit.digest(raw),
            "rework": version["rework"], "proposals": proposals, "workable": workable}
    # Inside a script tag, "</" would end it early. JSON allows "\/" for "/".
    blob = json.dumps(data).replace("</", "<\\/").replace("<!--", "<\\u0021--")
    body = (f'<div class="wrap">{"".join(main)}</div><div id="toast" role="status"></div>'
            f'<script type="application/json" id="piece-data">{blob}</script>'
            f'<script>{EDIT_JS}</script>')
    return page(p["title"], body)


EDIT_JS = r"""
(() => {
const D = JSON.parse(document.getElementById("piece-data").textContent);
const doc = document.getElementById("doc");
const toast = document.getElementById("toast");
let hideToast = null;

function say(msg, ms) {
  toast.textContent = msg;
  toast.style.display = "flex";
  clearTimeout(hideToast);
  hideToast = setTimeout(() => { toast.style.display = "none"; }, ms || 8000);
}
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

async function api(action, body) {
  const r = await fetch("/api/" + action, {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-Familiar-Token": D.token},
    body: JSON.stringify(Object.assign({id: D.id}, body))
  });
  const text = await r.text();
  let data = null;
  try { data = JSON.parse(text); } catch (e) {}
  return {ok: r.ok, status: r.status, data, error: (data && data.error) || text};
}

const PLACE = "familiarPlace:" + location.pathname;
function reload() {
  try { sessionStorage.setItem(PLACE, String(window.scrollY)); } catch (e) {}
  location.reload();
}
try {
  const y = sessionStorage.getItem(PLACE);
  if (y !== null) {
    sessionStorage.removeItem(PLACE);
    requestAnimationFrame(() => window.scrollTo(0, Number(y)));
  }
} catch (e) {}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); say("Copied."); return; } catch (e) {}
  const ta = document.createElement("textarea");
  ta.value = text; document.body.appendChild(ta); ta.select();
  try { document.execCommand("copy"); say("Copied."); } catch (e) {}
  ta.remove();
}

// Taking a suggestion or throwing a comment away asks for a second click,
// because one stray click should never change the draft or lose words.
function armed(btn, label) {
  if (btn.dataset.armed) return true;
  const was = btn.textContent;
  btn.dataset.armed = "1";
  btn.textContent = label;
  setTimeout(() => { delete btn.dataset.armed; btn.textContent = was; }, 4000);
  return false;
}

// ---- the document ------------------------------------------------------
// Each paragraph keeps its markdown in data-src. The one being typed in shows
// that markdown and is read back from the page as it is typed; the page never
// rewrites a paragraph while the cursor is in it, which is what keeps the
// cursor where it is.

const stateEl = document.getElementById("savestate");
const PENDING = "familiarPending:" + D.id;
let base = D.hash, timer = null, saving = false, more = false, stopped = false;
const PLAIN = (() => {
  const d = document.createElement("div");
  try { d.contentEditable = "plaintext-only"; } catch (e) {}
  return d.contentEditable === "plaintext-only";
})();

function setState(t) { if (stateEl) stateEl.textContent = t; }
function textOf(b) { return b.innerText.replace(/ /g, " ").replace(/\n+$/, ""); }
function all() { return doc ? Array.from(doc.querySelectorAll(".blk")) : []; }
function sources() {
  return all().map((b) => b.classList.contains("editing") ? textOf(b) : b.dataset.src)
    .filter((t) => t.trim());
}
function remember() {
  try { localStorage.setItem(PENDING, JSON.stringify({base, blocks: sources()})); } catch (e) {}
}
function forget() { try { localStorage.removeItem(PENDING); } catch (e) {} }

function schedule() {
  if (stopped) return;
  remember();
  setState("Editing");
  clearTimeout(timer);
  timer = setTimeout(save, 900);
}

async function save() {
  clearTimeout(timer);
  timer = null;
  if (stopped || !doc) return true;
  if (saving) { more = true; return false; }
  saving = true;
  setState("Saving");
  const texts = sources();
  const res = await api("save", {base, blocks: texts});
  saving = false;
  if (res.ok) {
    base = res.data.hash;
    if (!timer) forget();
    setState("Saved");
    let j = 0;
    all().forEach((b) => {
      const src = b.classList.contains("editing") ? textOf(b) : b.dataset.src;
      if (!src.trim()) return;
      const html = res.data.html[j++];
      if (!b.classList.contains("editing") && b.dataset.src === texts[j - 1] && html !== undefined) {
        b.innerHTML = html;
        b.classList.remove("pending");
      }
    });
    if (more) { more = false; return save(); }
    return true;
  }
  if (res.status === 409 && res.data && res.data.conflict) { stop(); return false; }
  setState("Not saved: " + res.error + " What you typed is kept in this browser.");
  return false;
}

function banner(text, actions) {
  const el = document.getElementById("banner");
  if (!el) return;
  el.innerHTML = "";
  const p = document.createElement("p");
  p.textContent = text;
  el.append(p);
  const row = document.createElement("div");
  row.className = "tools";
  actions.forEach(([label, fn]) => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = label; b.addEventListener("click", fn);
    row.append(b);
  });
  el.append(row);
  el.hidden = false;
}

function stop() {
  stopped = true;
  setState("Not saving");
  remember();
  banner("draft.md was changed somewhere else while this page was open, so saving has " +
         "stopped here rather than write over it. What you typed is kept in this browser.",
         [["Copy What I Typed", () => copyText(sources().join("\n\n"))],
          ["Reload the Draft", () => { forget(); reload(); }]]);
}

function makeBlock(src) {
  const b = document.createElement("div");
  b.className = "blk pending";
  b.dataset.src = src;
  b.textContent = src;
  return b;
}
function afterBlock(b, n) {
  // A new paragraph goes after this one's comments, not between them and it.
  let ref = b;
  while (ref.nextElementSibling && !ref.nextElementSibling.classList.contains("blk")) {
    ref = ref.nextElementSibling;
  }
  ref.after(n);
}
function prevBlock(b) { const a = all(); return a[a.indexOf(b) - 1] || null; }
function nextBlock(b) { const a = all(); return a[a.indexOf(b) + 1] || null; }
function composer() {
  const c = document.createElement("div");
  c.className = "blk composer";
  c.dataset.src = "";
  doc.append(c);
  return c;
}

function caretOffset(el) {
  const sel = window.getSelection();
  if (!sel.rangeCount) return 0;
  const r = sel.getRangeAt(0).cloneRange();
  const pre = document.createRange();
  pre.selectNodeContents(el);
  pre.setEnd(r.endContainer, r.endOffset);
  return pre.toString().length;
}
function placeCaret(el, offset) {
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let node, left = offset;
  while ((node = walker.nextNode())) {
    if (left <= node.nodeValue.length) {
      const r = document.createRange();
      r.setStart(node, left); r.collapse(true);
      const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      return;
    }
    left -= node.nodeValue.length;
  }
  const r = document.createRange();
  r.selectNodeContents(el); r.collapse(false);
  const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
}
// Where in the markdown the click landed, found by matching the words just
// before it. Markdown the page does not show can defeat the match, and then
// the cursor goes to the end.
function caretFor(e, b, src) {
  let node = null, off = 0;
  if (document.caretPositionFromPoint) {
    const p = document.caretPositionFromPoint(e.clientX, e.clientY);
    if (p) { node = p.offsetNode; off = p.offset; }
  } else if (document.caretRangeFromPoint) {
    const r = document.caretRangeFromPoint(e.clientX, e.clientY);
    if (r) { node = r.startContainer; off = r.startOffset; }
  }
  if (!node || node.nodeType !== 3 || !b.contains(node)) return src.length;
  const before = node.textContent.slice(Math.max(0, off - 30), off);
  for (let n = before.length; n >= 4; n -= 4) {
    const bit = before.slice(before.length - n);
    const at = src.indexOf(bit);
    if (at >= 0 && src.indexOf(bit, at + 1) < 0) return at + bit.length;
  }
  return src.length;
}

function edit(b, caret) {
  if (b.classList.contains("editing")) return;
  all().forEach((x) => { if (x !== b) leave(x); });
  if (!b._html && !b.classList.contains("pending")) b._html = b.innerHTML;
  b.classList.add("editing");
  b.contentEditable = PLAIN ? "plaintext-only" : "true";
  b.textContent = b.dataset.src;
  b.focus();
  placeCaret(b, caret == null ? b.dataset.src.length : caret);
}
function leave(b) {
  if (!b.classList.contains("editing")) return;
  const t = textOf(b);
  const changed = t !== b.dataset.src;
  b.dataset.src = t;
  b.classList.remove("editing");
  b.removeAttribute("contenteditable");
  if (b.classList.contains("composer")) { b.textContent = ""; return; }
  if (!t.trim()) {
    b.remove();
    schedule();
    return;
  }
  if (changed) {
    b.textContent = t;
    b.classList.add("pending");
    b._html = "";
    save();
  } else if (b._html) {
    b.innerHTML = b._html;
  } else {
    b.textContent = t;
  }
}

if (doc && D.workable) {
  all().forEach((b) => { b._html = b.innerHTML; });

  doc.addEventListener("click", (e) => {
    if (e.target.closest(".cmt, .flags, .threads")) return;
    const b = e.target.closest(".blk");
    if (!b || b.classList.contains("editing")) return;
    const link = e.target.closest("a");
    if (link && (e.metaKey || e.ctrlKey)) return;
    const sel = window.getSelection();
    if (sel && !sel.isCollapsed && sel.toString().trim()) return;
    e.preventDefault();
    edit(b, caretFor(e, b, b.dataset.src));
  });

  doc.addEventListener("focusout", (e) => {
    const b = e.target.closest && e.target.closest(".blk.editing");
    if (!b) return;
    setTimeout(() => { if (!b.contains(document.activeElement)) leave(b); }, 0);
  });

  doc.addEventListener("paste", (e) => {
    if (!e.target.closest(".blk.editing")) return;
    e.preventDefault();
    const text = (e.clipboardData || window.clipboardData).getData("text/plain");
    document.execCommand("insertText", false, text);
  });

  doc.addEventListener("keydown", (e) => {
    const b = e.target.closest(".blk.editing");
    if (!b) return;
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") { e.preventDefault(); save(); return; }
    if (e.key === "Escape") { e.preventDefault(); b.blur(); return; }
    if (e.key === "Enter") {
      e.preventDefault();
      document.execCommand("insertText", false, "\n");
      return;
    }
    const sel = window.getSelection();
    if (!sel.isCollapsed) return;
    const t = textOf(b), at = caretOffset(b);
    if (e.key === "Backspace" && at === 0) {
      const prev = prevBlock(b);
      if (!prev || prev.classList.contains("composer")) return;
      e.preventDefault();
      const join = prev.dataset.src.length;
      prev.dataset.src = prev.dataset.src + (t ? "\n" + t : "");
      if (b.classList.contains("composer")) b.textContent = ""; else b.remove();
      edit(prev, join);
      schedule();
      return;
    }
    const up = (e.key === "ArrowUp" && !t.slice(0, at).includes("\n")) || (e.key === "ArrowLeft" && at === 0);
    const down = (e.key === "ArrowDown" && !t.slice(at).includes("\n")) || (e.key === "ArrowRight" && at >= t.length);
    if (up && prevBlock(b)) { e.preventDefault(); const p = prevBlock(b); leave(b); edit(p, p.dataset.src.length); }
    else if (down && nextBlock(b)) { e.preventDefault(); const n = nextBlock(b); leave(b); edit(n, 0); }
  });

  // A blank line starts a new paragraph, the way it does in markdown: press
  // Enter twice. Never inside a code block that has not been closed.
  doc.addEventListener("input", (e) => {
    const b = e.target.closest(".blk.editing");
    if (!b) return;
    const raw = b.innerText.replace(/ /g, " ");
    const fences = (raw.match(/^```/gm) || []).length;
    const splitter = /\n[ \t]*\n/;
    if (fences % 2 === 0 && splitter.test(raw)) {
      const at = caretOffset(b);
      const parts = raw.split(splitter);
      const beforeParts = raw.slice(0, at).split(splitter);
      const k = beforeParts.length - 1, off = beforeParts[k].length;
      const wasComposer = b.classList.contains("composer");
      b.classList.remove("composer");
      b.textContent = parts[0];
      let last = b;
      const made = [b];
      for (let j = 1; j < parts.length; j++) {
        const n = makeBlock(parts[j].replace(/\n+$/, ""));
        afterBlock(last, n);
        last = n;
        made.push(n);
      }
      if (wasComposer) composer();
      const target = made[Math.min(k, made.length - 1)];
      if (target !== b) { leave(b); edit(target, off); }
      else placeCaret(b, off);
    } else if (b.classList.contains("composer") && raw.trim()) {
      b.classList.remove("composer");
      composer();
    }
    schedule();
  });

  document.addEventListener("visibilitychange", () => { if (document.hidden && timer) save(); });
  window.addEventListener("beforeunload", (e) => {
    if (timer || saving) { save(); e.preventDefault(); e.returnValue = ""; }
  });

  // Typed last time and never saved: put it back if the draft has not moved
  // since, and offer it if it has.
  try {
    const p = JSON.parse(localStorage.getItem(PENDING) || "null");
    if (p && Array.isArray(p.blocks) && p.blocks.join("\n\n") !== sources().join("\n\n")) {
      if (p.base === D.hash) {
        all().forEach((b) => { if (!b.classList.contains("composer")) b.remove(); });
        const c = doc.querySelector(".blk.composer");
        p.blocks.forEach((src) => c.before(makeBlock(src)));
        say("Put back what you typed last time, which had not been saved.");
        schedule();
      } else {
        banner("You typed something last time that was never saved, and the draft has " +
               "changed since.",
               [["Copy It", () => copyText(p.blocks.join("\n\n"))],
                ["Discard It", () => { forget(); document.getElementById("banner").hidden = true; }]]);
      }
    }
  } catch (e) {}
}

// ---- comments ------------------------------------------------------------

function diffHTML(a, b) {
  const A = a.split(/(\s+)/), B = b.split(/(\s+)/);
  const n = A.length, m = B.length;
  if (n * m > 4000000) return "<del>" + esc(a) + "</del><ins>" + esc(b) + "</ins>";
  const L = Array.from({length: n + 1}, () => new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  let i = 0, j = 0, out = "";
  while (i < n && j < m) {
    if (A[i] === B[j]) { out += esc(A[i]); i++; j++; }
    else if (L[i + 1][j] >= L[i][j + 1]) { out += "<del>" + esc(A[i]) + "</del>"; i++; }
    else { out += "<ins>" + esc(B[j]) + "</ins>"; j++; }
  }
  while (i < n) out += "<del>" + esc(A[i++]) + "</del>";
  while (j < m) out += "<ins>" + esc(B[j++]) + "</ins>";
  return out.replace(/<\/del><del>/g, "").replace(/<\/ins><ins>/g, "");
}
document.querySelectorAll("[data-diff]").forEach((el) => {
  const pr = D.proposals[el.dataset.diff];
  if (pr) el.innerHTML = diffHTML(pr.from, pr.to);
});

// Mark the words each comment is about, where they sit in one piece of text.
document.querySelectorAll(".threads").forEach((t) => {
  let b = t.previousElementSibling;
  while (b && !b.classList.contains("blk")) b = b.previousElementSibling;
  if (!b) return;
  t.querySelectorAll(".cmt .q").forEach((q) => {
    const words = q.textContent.replace(/^“|”$/g, "").slice(0, 60);
    if (!words.trim()) return;
    const walker = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const at = node.nodeValue.indexOf(words);
      if (at < 0) continue;
      const r = document.createRange();
      r.setStart(node, at); r.setEnd(node, at + words.length);
      const mark = document.createElement("mark");
      mark.className = "c";
      r.surroundContents(mark);
      break;
    }
  });
});

const nb = document.createElement("button");
nb.id = "notebtn"; nb.type = "button"; nb.textContent = "Comment"; nb.hidden = true;
document.body.append(nb);
let picked = null;

function openPopover(at, whole) {
  const old = document.getElementById("notepop");
  if (old) old.remove();
  const pop = document.createElement("form");
  pop.id = "notepop";
  pop.innerHTML = '<q></q><textarea rows="4" aria-label="Your comment" ' +
    'placeholder="What should change, or your own version"></textarea>' +
    '<label class="filter"><input type="checkbox" name="own"> this is my own wording</label>' +
    '<div class="tools"><button class="primary" type="submit">Comment</button>' +
    '<button type="button" data-now>Comment and Send</button>' +
    '<button type="button" data-x>Cancel</button></div>';
  const q = whole ? "The whole draft" : picked.quote;
  pop.querySelector("q").textContent = q.length > 140 ? q.slice(0, 137) + "..." : q;
  pop.style.left = at.left + "px";
  pop.style.top = at.top + "px";
  document.body.append(pop);
  const ta = pop.querySelector("textarea");
  ta.focus();
  const go = async (sendNow, btn) => {
    const text = ta.value.trim();
    if (!text) { say("Say what should change, or write your version."); return; }
    btn.disabled = true;
    if (!(await save())) { btn.disabled = false; say("The draft could not be saved, so the comment waits. What you wrote is still here."); return; }
    const res = await api("comment", {
      text, own: pop.querySelector("[name=own]").checked, send: sendNow, whole: !!whole,
      quote: whole ? "" : picked.quote, block: whole ? "" : picked.block});
    btn.disabled = false;
    if (!res.ok) { say(res.error + " What you wrote is still here."); return; }
    pop.remove();
    reload();
  };
  pop.addEventListener("submit", (e) => { e.preventDefault(); go(false, pop.querySelector("button.primary")); });
  pop.querySelector("[data-now]").addEventListener("click", (e) => go(true, e.currentTarget));
  pop.querySelector("[data-x]").addEventListener("click", () => pop.remove());
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); pop.requestSubmit(); }
    if (e.key === "Escape" && !ta.value.trim()) pop.remove();
  });
}

if (doc && D.workable) {
  doc.addEventListener("mouseup", () => setTimeout(() => {
    const sel = window.getSelection();
    const text = sel && sel.rangeCount ? sel.toString().trim() : "";
    if (!text) { nb.hidden = true; return; }
    const r = sel.getRangeAt(0);
    const a = (r.startContainer.nodeType === 3 ? r.startContainer.parentElement : r.startContainer).closest(".blk");
    const z = (r.endContainer.nodeType === 3 ? r.endContainer.parentElement : r.endContainer).closest(".blk");
    if (!a || a !== z || a.classList.contains("composer")) { nb.hidden = true; return; }
    picked = {quote: text, block: a.classList.contains("editing") ? textOf(a) : a.dataset.src};
    const rect = r.getBoundingClientRect();
    const maxLeft = window.scrollX + document.documentElement.clientWidth - 360;
    nb.style.left = Math.max(window.scrollX + 16, Math.min(window.scrollX + rect.left, maxLeft)) + "px";
    nb.style.top = (window.scrollY + rect.bottom + 8) + "px";
    nb.hidden = false;
  }, 0));
}
nb.addEventListener("mousedown", (e) => e.preventDefault());
nb.addEventListener("click", () => {
  nb.hidden = true;
  openPopover({left: parseFloat(nb.style.left), top: parseFloat(nb.style.top)}, false);
});
document.addEventListener("mousedown", (e) => {
  if (!e.target.closest("#notebtn, #notepop")) nb.hidden = true;
});

function inlineForm(after, placeholder, button, value, onSend) {
  const old = after.parentElement.querySelector("form.inline");
  if (old) old.remove();
  const form = document.createElement("form");
  form.className = "inline";
  form.innerHTML = '<textarea rows="4"></textarea><div class="tools">' +
    '<button class="primary" type="submit"></button><button type="button" data-x>Cancel</button></div>';
  const ta = form.querySelector("textarea");
  ta.placeholder = placeholder;
  ta.setAttribute("aria-label", placeholder);
  if (value) { ta.value = value; ta.rows = Math.min(24, value.split("\n").length + 2); }
  form.querySelector("button.primary").textContent = button;
  form.querySelector("[data-x]").addEventListener("click", () => form.remove());
  form.addEventListener("submit", (e) => { e.preventDefault(); onSend(ta.value, form.querySelector("button.primary")); });
  after.after(form);
  ta.focus();
}

async function act(action, body, btn) {
  if (btn) btn.disabled = true;
  if (!(await save())) {
    if (btn) btn.disabled = false;
    say("The draft could not be saved first, so nothing else was done.");
    return;
  }
  const res = await api(action, body);
  if (btn) btn.disabled = false;
  if (!res.ok) { say(res.error || "That did not go through."); return; }
  reload();
}

document.addEventListener("click", (e) => {
  const t = (sel) => e.target.closest(sel);
  let b;
  if ((b = t("[data-whole]"))) {
    e.preventDefault();
    const r = b.getBoundingClientRect();
    openPopover({left: window.scrollX + Math.max(16, r.left - 200), top: window.scrollY + r.bottom + 8}, true);
  } else if ((b = t("#sendall"))) {
    e.preventDefault();
    act("send", {}, b);
  } else if ((b = t("[data-send]"))) {
    e.preventDefault();
    act("send", {threads: [b.dataset.send]}, b);
  } else if ((b = t("[data-accept]"))) {
    e.preventDefault();
    if (armed(b, "Click Again to Accept")) act("accept", {thread: b.dataset.accept}, b);
  } else if ((b = t("[data-drop]"))) {
    e.preventDefault();
    if (armed(b, "Click Again to Confirm")) act("drop", {thread: b.dataset.drop}, b);
  } else if ((b = t("[data-reply]"))) {
    e.preventDefault();
    const tid = b.dataset.reply;
    inlineForm(b.parentElement, "What should change this time?", "Send Reply", "", (text, btn) => {
      if (!text.trim()) { say("Say what should change this time."); return; }
      act("reply", {thread: tid, text}, btn);
    });
  } else if ((b = t("[data-edit]"))) {
    e.preventDefault();
    const tid = b.dataset.edit;
    inlineForm(b.parentElement, "Your version", "Accept My Version", (D.proposals[tid] || {}).to, (text, btn) => {
      if (!text.trim()) { say("There is nothing to put in its place."); return; }
      act("accept", {thread: tid, text}, btn);
    });
  } else if ((b = t("[data-flag]"))) {
    e.preventDefault();
    const d = b.dataset;
    inlineForm(b.parentElement, "Anything to add? Optional.", "Send to Agent", "", (text, btn) => {
      act("comment", {text, block: d.src, report: d.report, key: d.key, send: true}, btn);
    });
  }
});

document.addEventListener("submit", (e) => {
  const f = e.target;
  const kind = f.dataset.form;
  if (!kind) return;
  e.preventDefault();
  const fd = new FormData(f);
  const btn = f.querySelector("button.primary, button[type=submit]");
  if (kind === "choose") {
    const because = fd.get("nogiven") ? "not given" : String(fd.get("because") || "").trim();
    if (!fd.get("letter")) { say("Pick one first."); return; }
    if (!because) { say("Add a Because, or tick 'no reason given'."); return; }
    act("choose", {file: f.dataset.file, set: f.dataset.set, index: Number(f.dataset.index),
                   letter: fd.get("letter"), because}, btn);
  } else if (kind === "answer") {
    const answer = String(fd.get("answer") || "").trim();
    if (!answer) { say("Write the answer first."); return; }
    act("answer", {answer}, btn);
  }
});

// A suggestion that comes back shows up by itself, once nobody is typing. A
// change to the draft from somewhere else stops the saving rather than being
// written over.
let told = false;
setInterval(async () => {
  try {
    const r = await fetch("/api/version/" + D.id, {cache: "no-store"});
    if (!r.ok) return;
    const v = await r.json();
    if (D.workable && !stopped && !saving && !timer && v.draft !== base) { stop(); return; }
    if (v.rework === D.rework) return;
    const busy = document.querySelector(".blk.editing, #notepop, form.inline") || timer || saving;
    if (!busy) reload();
    else if (!told) { told = true; say("Something came back from your agent. It will show when you click out of what you are typing."); }
  } catch (e) {}
}, 4000);
})();
"""


def deletable(folder):
    """A piece that has been sent is not the board's to destroy.

    `final.md` is the record that something went out. It is what `learn diff`
    reads, and it is evidence of a thing that exists in the world. Everything
    else in a piece folder is working material, and clearing it out is the
    writer's business.
    """
    return not (folder / "final.md").exists()

def list_archive(dirs, source_of=None):
    """Everything sitting in .archive, newest first.

    An archived piece keeps the id it had on the board, so Restore can find
    what Archive moved.
    """
    source_of = source_of or {}
    out = []
    for d in dirs:
        arch = d / ".archive"
        if not arch.is_dir():
            continue
        for folder in arch.iterdir():
            if not folder.is_dir() or folder.name.startswith("."):
                continue
            fm, _ = frontmatter(read(folder / "draft.md"))
            out.append({"id": safe_name(source_of.get(d, ""), folder.name), "folder": folder,
                        "home": d, "slug": folder.name,
                        "title": fm.get("title") or folder.name,
                        "deletable": deletable(folder),
                        "ts": folder.stat().st_mtime})
    return sorted(out, key=lambda a: a["ts"], reverse=True)

def archive_html(archived, token):
    if not archived:
        return ""
    rows = "".join(
        f'<div class="arow" data-id="{html.escape(a["id"])}">'
        f'<span class="t">{html.escape(a["title"])}</span>'
        f'<span class="when">{html.escape(a["slug"])}</span>'
        + (('<button data-act="restore">Restore</button>'
            + ('<button class="danger" data-act="delete">Delete</button>'
               if a["deletable"] else '<span class="when">sent, kept</span>'))
           if token else "")
        + '</div>'
        for a in archived)
    n = len(archived)
    return (f'<details class="arch"><summary>Archive ({n})</summary>{rows}'
            + ("" if token else '<p class="none">Run with --serve to restore or '
                                'delete these.</p>')
            + '</details>')

def board_page(pieces, pieces_dirs, prefix="familiar", archived=(), token=""):
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
            + "".join(card_html(p, token, prefix) for p in inc) + "</div>")
    waiting_toggle = (
        '<label class="filter"><input type="checkbox" id="waiting-only">'
        'only what is waiting on me</label>') if waiting else ""
    body = (f'<header class="top"><h1>Familiar</h1>'
            f'<div class="meta">{meta} &middot; built {now}</div>'
            f'{waiting_toggle}</header>'
            f'<div class="board">{"".join(cols)}</div>'
            + archive_html(archived, token)
            + ('<div id="toast"></div>' + CLIENT_JS.replace("__TOKEN__", token)
               if token else ""))
    return page("Familiar board", body)

CLIENT_JS = """
<script>
const TOKEN = "__TOKEN__";
const toast = document.getElementById("toast");
let hide = null;
function say(msg, onUndo) {
  toast.innerHTML = "";
  toast.append(msg);
  if (onUndo) {
    const b = document.createElement("button");
    b.textContent = "Undo"; b.onclick = onUndo; toast.append(b);
  }
  toast.style.display = "flex";
  clearTimeout(hide);
  hide = setTimeout(() => { toast.style.display = "none"; }, 7000);
}
async function call(action, id) {
  const r = await fetch("/api/" + action, {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-Familiar-Token": TOKEN},
    body: JSON.stringify({id})
  });
  if (!r.ok) { say("That did not work: " + (await r.text())); return null; }
  return r.json();
}
function nameOf(el) {
  const h = el.querySelector("h3, .t");
  return h ? h.textContent.trim() : "this piece";
}
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-act]");
  if (!btn) return;
  e.preventDefault(); e.stopPropagation();
  const row = btn.closest("[data-id]");
  const act = btn.dataset.act, id = row.dataset.id;
  if (act === "delete") {
    const ok = confirm(
      "Delete \u201c" + nameOf(row) + "\u201d?\n\n" +
      "The whole piece folder goes: notes, outline, draft, edits. " +
      "This cannot be undone.\n\nArchive instead if you might want it back.");
    if (!ok) return;
    if (await call("delete", id)) location.reload();
    return;
  }
  const res = await call(act, id);
  if (!res) return;
  if (act === "archive") {
    say("Archived. It is in the archive at the bottom.", async () => {
      await call("restore", id); location.reload();
    });
    setTimeout(() => location.reload(), 1400);
  } else {
    location.reload();
  }
});
</script>
"""

# --------------------------------------------------------------------------

def build(dirs, out, stale_days, command, token=""):
    """Write index.html and a page per piece. Returns (pieces, archived, swept)."""
    GENERIC = {"pieces", "issues", "writing", "drafts", "posts", "content",
               "src", "docs", "documents", "projects"}
    def label(d):
        for part in [d.name] + [q.name for q in d.parents]:
            if part.lower() in GENERIC or re.match(r"^\d\d[-_]", part):
                continue
            return part
        return d.name

    source_of = {d: (label(d) if len(dirs) > 1 else "") for d in dirs}
    now = datetime.datetime.now().timestamp()
    pieces = []
    for d in dirs:
        src = source_of[d]
        for folder in sorted((f for f in d.iterdir()
                              if f.is_dir() and not f.name.startswith(".")),
                             key=lambda f: f.name, reverse=True):
            pieces.append(gather(folder, now, stale_days, src))
    pieces.sort(key=lambda q: q["slug"], reverse=True)
    archived = list_archive(dirs, source_of)

    prefix = command or command_prefix(dirs[0])
    out.mkdir(parents=True, exist_ok=True)
    for q in pieces:
        (out / f"{q['page']}.html").write_text(piece_page(q, prefix), encoding="utf-8")
    (out / "index.html").write_text(
        board_page(pieces, dirs, prefix, archived, token), encoding="utf-8")

    # A page for a piece that no longer exists is a link to a lie. Sweep them.
    keep = {"index.html"} | {f"{q['page']}.html" for q in pieces}
    swept = 0
    for old_page in out.glob("*.html"):
        if old_page.name not in keep:
            old_page.unlink(); swept += 1
    return pieces, archived, swept


def unique_dest(parent, name):
    dest = parent / name
    n = 2
    while dest.exists():
        dest = parent / f"{name}-{n}"; n += 1
    return dest


def apply_edit(action, folder, b):
    """Run one change from a piece's page against its folder. Returns extra JSON."""
    E = board_edit
    if action == "save":
        texts = [str(t) for t in b["blocks"]]
        r = E.save_blocks(folder, str(b["base"]), texts)
        return {"hash": r["hash"], "html": [md_to_html(t) for t in texts if t.strip()]}
    if action == "comment":
        flag = E.flag_field(folder, str(b["report"]), str(b["key"])) if b.get("report") else None
        return {"thread": E.comment(folder, str(b.get("text") or ""), str(b.get("quote") or ""),
                                    str(b.get("block") or ""), bool(b.get("own")),
                                    bool(b.get("whole")), flag, bool(b.get("send")))}
    if action == "send":
        threads = b.get("threads")
        return {"sent": E.send(folder, [str(t) for t in threads] if threads else None)}
    if action == "accept":
        E.accept(folder, str(b["thread"]), None if b.get("text") is None else str(b["text"]))
    elif action == "reply":
        E.again(folder, str(b["thread"]), str(b["text"]))
    elif action == "drop":
        E.drop(folder, str(b["thread"]))
    elif action == "choose":
        E.choose(folder, str(b["file"]), str(b["set"]), int(b["index"]),
                 str(b["letter"]), str(b["because"]))
    elif action == "answer":
        E.record_answer(folder, str(b["answer"]))
    else:
        raise LookupError(action)
    return {}


def make_server(dirs, out, stale_days, command, port=0):
    """A local server, so the board can be tidied and answered as well as read.

    Returns the server, not yet serving, and the token its pages carry.

    Safety, deliberately:
      - binds 127.0.0.1 only, so nothing off this machine can reach it
      - every request has to be addressed to that address and port. Otherwise
        a web page that points its own domain at 127.0.0.1 could read the
        board through the browser (DNS rebinding)
      - every write needs a token minted for this run, so another page open in
        the same browser cannot post to it
      - an action names a piece by the id the board itself generated, and the
        server resolves that against the pieces it just built. No path from
        the client is ever touched
      - archiving moves a folder; it never deletes
      - deleting is refused for any piece that has been sent, checked on the
        server against the folder rather than trusted from the page
      - every edit goes through board_edit, which keeps the version of
        draft.md a save replaces and refuses a save made against a version
        that has changed since the page was opened
    """
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    token = secrets.token_urlsafe(18)
    state = {"hosts": set()}
    lock = threading.Lock()
    prefix = command or command_prefix(dirs[0])

    def rebuild():
        pieces, archived, _ = build(dirs, out, stale_days, command, token)
        state["live"] = {q["page"]: q["folder"] for q in pieces}
        state["source"] = {q["page"]: q["source"] for q in pieces}
        state["archived"] = {a["id"]: (a["folder"], a["home"]) for a in archived}
        return pieces, archived

    rebuild()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body=b"", ctype="text/plain; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if body:
                self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj).encode(), "application/json")

        def _addressed_to_us(self):
            return self.headers.get("Host", "") in state["hosts"]

        def do_GET(self):
            if not self._addressed_to_us():
                return self._send(403, b"not this server")
            name = self.path.split("?")[0].lstrip("/") or "index.html"
            if name == "index.html":
                with lock:
                    rebuild()
            elif name.startswith("api/version/") and name[12:] in state["live"]:
                return self._json(200, rework_version(state["live"][name[12:]]))
            elif name.endswith(".html") and name[:-5] in state["live"]:
                pid = name[:-5]
                folder = state["live"][pid]
                if not folder.is_dir():
                    with lock:
                        rebuild()
                    return self._send(404, b"That piece is not where it was. Go back to the board.")
                # Read from the files now, not from the last build: the page is
                # a view of what is on disk, and something else may have written.
                q = gather(folder, datetime.datetime.now().timestamp(), stale_days,
                           state["source"][pid])
                return self._send(200, piece_page(q, prefix, token).encode("utf-8"),
                                  "text/html; charset=utf-8")
            target = (out / name).resolve()
            if out.resolve() not in target.parents or not target.is_file():
                return self._send(404, b"not found")
            ctype = "text/html; charset=utf-8" if target.suffix == ".html" else "text/plain"
            self._send(200, target.read_bytes(), ctype)

        def do_POST(self):
            if not self._addressed_to_us():
                return self._send(403, b"not this server")
            if self.headers.get("X-Familiar-Token") != token:
                return self._send(403, b"bad token")
            action = self.path.rsplit("/", 1)[-1]
            try:
                n = int(self.headers.get("Content-Length", 0))
                if n > 4_000_000:
                    return self._send(413, b"too large")
                body = json.loads(self.rfile.read(n) or b"{}")
                pid = body.get("id", "")
            except Exception:
                return self._send(400, b"bad request")

            result = {}
            with lock:
                try:
                    if action not in ("archive", "restore", "delete"):
                        folder = state["live"].get(pid)
                        if not folder:
                            return self._json(404, {"error": "That piece is not on the "
                                                    "board any more. Go back to it."})
                        result = apply_edit(action, folder, body)
                    elif action == "archive":
                        folder = state["live"].get(pid)
                        if not folder:
                            return self._send(404, b"no such piece")
                        arch = folder.parent / ".archive"
                        arch.mkdir(exist_ok=True)
                        shutil.move(str(folder), str(unique_dest(arch, folder.name)))
                    elif action == "restore":
                        entry = state["archived"].get(pid)
                        if not entry:
                            return self._send(404, b"not in the archive")
                        folder, home = entry
                        shutil.move(str(folder), str(unique_dest(home, folder.name)))
                    elif action == "delete":
                        entry = state["archived"].get(pid)
                        folder = entry[0] if entry else state["live"].get(pid)
                        if not folder:
                            return self._send(404, b"no such piece")
                        # Checked here as well as in the page, because the page
                        # is not what enforces it.
                        if not deletable(folder):
                            return self._send(403, b"refusing: this piece has been sent")
                        if folder.parent not in dirs and folder.parent.name != ".archive":
                            return self._send(400, b"refusing: unexpected location")
                        shutil.rmtree(folder)
                    rebuild()
                except board_edit.Conflict as exc:
                    return self._json(409, {"conflict": True,
                                            "hash": board_edit.digest(exc.current),
                                            "error": "draft.md changed since this page was opened."})
                except board_edit.Refused as exc:
                    return self._json(409, {"error": str(exc)})
                except KeyError as exc:
                    return self._json(400, {"error": f"bad request: missing {exc}"})
                except LookupError:
                    return self._json(404, {"error": "no such action"})
                except (TypeError, ValueError):
                    return self._json(400, {"error": "bad request"})
                except OSError as exc:
                    return self._send(500, str(exc).encode())
            self._json(200, {"ok": True, **result})

    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:                  # the usual port is taken, by another board perhaps
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_port
    state["hosts"] = {f"127.0.0.1:{port}", f"localhost:{port}"}
    return httpd, token


def serve(dirs, out, stale_days, command, open_browser):
    # The same address each run where it is free, so what the writer typed and
    # the browser kept is still there after a restart.
    httpd, _ = make_server(dirs, out, stale_days, command, port=47100)
    url = f"http://127.0.0.1:{httpd.server_port}/"
    print(f"Serving the board at {url}", flush=True)
    print("Open a piece to write in it. Comments sent to an agent are answered by a "
          "session running `familiar rework watch`.", flush=True)
    print("Earlier versions of each draft are kept in the piece's .versions/ folder.",
          flush=True)
    print("Archive moves a piece into .archive; it can be restored.", flush=True)
    print("Delete removes the folder. A piece that has been sent is refused.",
          flush=True)
    print("Ctrl-C to stop.", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped. The board is still readable at " + str(out / "index.html"))


def main():
    ap = argparse.ArgumentParser(description="Build a static board of every piece.")
    ap.add_argument("--pieces", action="append", default=[],
                    help="folder holding the piece folders; repeatable "
                         "(default: FAMILIAR_PIECES, .familiar, then ./pieces)")
    ap.add_argument("--out", default="", help="where to write the HTML (default: <first pieces>/.board)")
    ap.add_argument("--command", default="", help="how to invoke a stage in the hint")
    ap.add_argument("--stale-days", type=int, default=7)
    ap.add_argument("--serve", action="store_true",
                    help="serve it locally so pieces can be archived and restored")
    ap.add_argument("--open", action="store_true", help="open the board in a browser")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent
    # One resolver for every script: flags, then FAMILIAR_PIECES, then the
    # `pieces =` lines in a .familiar file, then the repo's own folder.
    dirs = resolved_pieces(args.pieces or None)
    missing = [d for d in dirs if not d.is_dir()]
    if missing:
        sys.exit("No such folder: " + ", ".join(str(m) for m in missing))
    out = pathlib.Path(args.out).expanduser() if args.out else dirs[0] / ".board"

    if args.serve:
        return serve(dirs, out, args.stale_days, args.command, args.open)

    pieces, archived, swept = build(dirs, out, args.stale_days, args.command)
    waiting = sum(1 for q in pieces if q["from_log"])
    note = f"{len(pieces)} piece{'s' if len(pieces) != 1 else ''}"
    if waiting:
        note += f", {waiting} with a note from you"
    if archived:
        note += f", {len(archived)} archived"
    if swept:
        note += f", {swept} stale page{'s' if swept != 1 else ''} removed"
    print(note)
    print(out / "index.html")
    if args.open:
        webbrowser.open((out / "index.html").as_uri())


if __name__ == "__main__":
    main()
