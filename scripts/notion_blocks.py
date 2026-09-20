#!/usr/bin/env python3
"""Markdown to Notion blocks and back, for a draft.

Nothing here talks to Notion. It turns the body of a draft into the block shapes
Notion's API takes, and turns blocks read from Notion into markdown, so the two
can be compared and a draft can travel both ways.

What travels: paragraphs, headings 1 to 3, bullets, numbers, task items (each
nested up to three levels), block quotes, code fences, dividers, tables, external
images, and bold, italic, strikethrough, inline code and links.

What does not, and is refused rather than dropped:
  - on the way out: headings deeper than 3, a numbered list that starts above 1,
    lists nested deeper than three levels
  - on the way in: any block the draft has no form for (toggles, callouts,
    columns, embeds, files, uploaded images, and the like)

Formatting with no markdown form (underline, colour) is dropped on the way in and
counted, so it can be reported. The text is kept.

`canon(md)` is a draft's body after one trip through blocks. Two drafts that
canonise the same are the same draft, whatever markers they use.
"""
import re

LANGUAGES = frozenset(
    "abap arduino bash basic c clojure coffeescript c++ c# css dart diff docker elixir elm "
    "erlang flow fortran f# gherkin glsl go graphql groovy haskell html java javascript json "
    "julia kotlin latex less lisp livescript lua makefile markdown markup matlab mermaid nix "
    "objective-c ocaml pascal perl php powershell prolog protobuf python r reason ruby rust "
    "sass scala scheme scss shell sql swift typescript vb.net verilog vhdl visual basic "
    "webassembly xml yaml".split()) | {"plain text", "visual basic", "java/c/c++/c#"}
ALIASES = {"js": "javascript", "ts": "typescript", "py": "python", "sh": "shell", "zsh": "shell",
           "yml": "yaml", "md": "markdown", "text": "plain text", "txt": "plain text",
           "rb": "ruby", "rs": "rust", "cpp": "c++", "cs": "c#", "objc": "objective-c"}
TEXT_LIMIT = 2000
MAX_DEPTH = 3          # a list item and two levels of children
LIST_TYPES = ("bulleted_list_item", "numbered_list_item", "to_do")


class Unsupported(Exception):
    """Content that has no form on the other side. `items` says what, and how many."""

    def __init__(self, items):
        self.items = sorted(items)
        super().__init__("; ".join(self.items))


# -- inline ----------------------------------------------------------------

_ESC = re.compile(r"\\([\\`*_{}\[\]()#+\-.!~|>])")
_INLINE = re.compile(
    r"(\*\*(?P<b>.+?)\*\*|(?<![_\w])__(?P<b2>.+?)__(?![_\w])|`(?P<c>[^`]+)`|\[(?P<lt>[^\]\n]+)\]\((?P<lu>[^)\s]+)\)"
    r"|~~(?P<s>.+?)~~|(?<![*\w])\*(?P<i>[^*\n]+)\*(?![*\w])|(?<![_\w])_(?P<i2>[^_\n]+)_(?![_\w]))")


def _ann(**kw):
    a = {"bold": False, "italic": False, "strikethrough": False, "underline": False,
         "code": False, "color": "default"}
    a.update(kw)
    return a


def _runs(s, ann=None, link=None):
    """[(text, annotations, link)] for one line of markdown."""
    ann = ann or {}
    out, pos = [], 0
    for m in _INLINE.finditer(s):
        if m.start() > pos:
            out.append((_unescape(s[pos:m.start()]), dict(ann), link))
        if m.group("b") is not None or m.group("b2") is not None:
            out += _runs(m.group("b") or m.group("b2"), {**ann, "bold": True}, link)
        elif m.group("c") is not None:
            out.append((m.group("c"), {**ann, "code": True}, link))
        elif m.group("lt") is not None:
            out += _runs(m.group("lt"), ann, m.group("lu"))
        elif m.group("s") is not None:
            out += _runs(m.group("s"), {**ann, "strikethrough": True}, link)
        else:
            out += _runs(m.group("i") or m.group("i2"), {**ann, "italic": True}, link)
        pos = m.end()
    if pos < len(s):
        out.append((_unescape(s[pos:]), dict(ann), link))
    return out


def _unescape(t):
    return _ESC.sub(r"\1", t)


def rich_from_md(s):
    els = []
    for text, ann, link in _runs(s):
        for i in range(0, max(len(text), 1), TEXT_LIMIT):
            chunk = text[i:i + TEXT_LIMIT]
            if not chunk and els:
                continue
            els.append({"type": "text", "text": {"content": chunk, "link": {"url": link} if link else None},
                        "annotations": _ann(**{k: v for k, v in ann.items() if v})})
    return [e for e in els if e["text"]["content"]]


def _plain_text(e):
    return e.get("plain_text") if e.get("plain_text") is not None else e.get("text", {}).get("content", "")


def _protect(text):
    """Escape what would be read back as formatting, and only that."""
    if [t for t, a, l in _runs(text) if t] == [text] and all(not a and not l for _, a, l in _runs(text)):
        return text
    return re.sub(r"([\\`*_\[\]~])", r"\\\1", text)


def md_from_rich(els, notes=None):
    runs = []
    for e in els or []:
        a = e.get("annotations", {})
        link = (e.get("text", {}).get("link") or {}).get("url") or e.get("href")
        if notes is not None:
            if a.get("underline"):
                notes["underline"] = notes.get("underline", 0) + 1
            if a.get("color", "default") != "default":
                notes["colour"] = notes.get("colour", 0) + 1
        runs.append((_plain_text(e), {k: bool(a.get(k)) for k in ("bold", "italic", "strikethrough", "code")}, link))
    return _emit(runs)


def _emit(runs):
    out, i = "", 0
    while i < len(runs):
        t, a, link = runs[i]
        key = next((k for k in ("link", "strikethrough", "bold", "italic") if (link if k == "link" else a.get(k))), None)
        if key is None:
            out += f"`{t}`" if a.get("code") else _protect(t)
            i += 1
            continue
        j = i
        while j < len(runs) and ((runs[j][2] == link) if key == "link" else runs[j][1].get(key)):
            j += 1
        inner = [(r[0], {k: v for k, v in r[1].items() if k != key}, None if key == "link" else r[2])
                 for r in runs[i:j]]
        body = _emit(inner)
        out += {"link": f"[{body}]({link})", "strikethrough": f"~~{body}~~",
                "bold": f"**{body}**", "italic": f"*{body}*"}[key]
        i = j
    return out


# -- markdown to blocks ----------------------------------------------------

_LIST = re.compile(r"^( *)([-*+]|\d+\.)\s+(.*)$")
_STOP = re.compile(r"^(#{1,6}\s|```|>|(-{3,}|\*{3,}|_{3,})\s*$)")


def _block(kind, payload, children=None):
    body = dict(payload)
    if children:
        body["children"] = children
    return {"object": "block", "type": kind, kind: body}


def md_to_blocks(md):
    lines = md.replace("\r\n", "\n").split("\n")
    problems = set()
    blocks, _ = _parse(lines, 0, 0, problems)
    if problems:
        raise Unsupported(problems)
    return blocks


def _parse_list(lines, i, indent, depth, problems):
    items = []
    while i < len(lines):
        m = _LIST.match(lines[i])
        if not m or len(m.group(1)) < indent:
            break
        if len(m.group(1)) > indent:
            if not items:
                break
            if depth + 1 >= MAX_DEPTH:
                problems.add("lists nested more than three levels")
            kids, i = _parse_list(lines, i, len(m.group(1)), depth + 1, problems)
            items[-1][items[-1]["type"]].setdefault("children", []).extend(kids)
            continue
        marker, body = m.group(2), m.group(3)
        td = re.match(r"^\[( |x)\]\s+(.*)$", body)
        if marker[0].isdigit():
            kind = "numbered_list_item"
            if not items and int(marker[:-1]) != 1:
                problems.add(f"a numbered list that starts at {int(marker[:-1])}")
        else:
            kind = "to_do" if td else "bulleted_list_item"
        i += 1
        text = td.group(2) if td else body
        while i < len(lines) and lines[i].strip() and not _LIST.match(lines[i]) \
                and len(lines[i]) - len(lines[i].lstrip()) > indent:
            text += "\n" + lines[i].strip()          # a wrapped line of the same item
            i += 1
        payload = {"rich_text": rich_from_md(text)}
        if kind == "to_do":
            payload["checked"] = bool(td and td.group(1) == "x")
        items.append(_block(kind, payload))
    return items, i


def _parse(lines, i, indent, problems):
    blocks = []
    while i < len(lines):
        L = lines[i]
        if not L.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", L)
        if m:
            depth = len(m.group(1))
            if depth > 3:
                problems.add(f"a level {depth} heading")
            blocks.append(_block(f"heading_{min(depth, 3)}", {"rich_text": rich_from_md(m.group(2)),
                                                            "is_toggleable": False}))
            i += 1
            continue
        if L.startswith("```"):
            info, j = L[3:].strip(), i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            code = "\n".join(lines[i + 1:j])
            lang = info.lower()
            mapped = ALIASES.get(lang, lang) if lang else "plain text"
            if mapped not in LANGUAGES:
                mapped = "plain text"
            payload = {"rich_text": [{"type": "text", "text": {"content": code[k:k + TEXT_LIMIT]}}
                                     for k in range(0, len(code), TEXT_LIMIT)] or [],
                       "language": mapped}
            if info and info != mapped:                # keep what was written, so it comes back
                payload["caption"] = [{"type": "text", "text": {"content": info}}]
            blocks.append(_block("code", payload))
            i = j + 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})\s*$", L):
            blocks.append(_block("divider", {}))
            i += 1
            continue
        if L.startswith(">"):
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            blocks.append(_block("quote", {"rich_text": rich_from_md("\n".join(q))}))
            continue
        if "|" in L and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]) \
                and "|" in lines[i + 1]:
            rows = []
            while i < len(lines) and "|" in lines[i]:
                if not re.match(r"^\s*\|?\s*:?-{2,}[:\-|\s]*$", lines[i]):
                    rows.append([rich_from_md(c.strip()) for c in lines[i].strip().strip("|").split("|")])
                i += 1
            width = max(len(r) for r in rows)
            rows = [r + [[] for _ in range(width - len(r))] for r in rows]
            blocks.append(_block("table", {"table_width": width, "has_column_header": True, "has_row_header": False},
                                 [_block("table_row", {"cells": r}) for r in rows]))
            continue
        im = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", L)
        if im:
            payload = {"type": "external", "external": {"url": im.group(2)}}
            if im.group(1):
                payload["caption"] = [{"type": "text", "text": {"content": im.group(1)}}]
            blocks.append(_block("image", payload))
            i += 1
            continue
        if _LIST.match(L):
            items, i = _parse_list(lines, i, len(_LIST.match(L).group(1)), 0, problems)
            blocks += items
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not _STOP.match(lines[i]) and not _LIST.match(lines[i]) \
                and not (para and "|" in lines[i] and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1])):
            para.append(lines[i])
            i += 1
        if not para:                                   # a line that would start no block
            para, i = [lines[i]], i + 1
        blocks.append(_block("paragraph", {"rich_text": rich_from_md("\n".join(para))}))
    return blocks, i


# -- blocks to markdown ----------------------------------------------------

SUPPORTED = {"paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item",
             "to_do", "quote", "code", "divider", "table", "table_row", "image"}


def _children(b):
    return b.get("children") or b.get(b.get("type"), {}).get("children") or []


def _check(blocks, problems):
    for b in blocks:
        t = b.get("type")
        if t not in SUPPORTED:
            problems.add(f"a {t} block" if t else "a block of unknown type")
        elif t == "image" and b["image"].get("type") not in ("external", None):
            problems.add("an image uploaded to Notion")
        elif t.startswith("heading") and b[t].get("is_toggleable"):
            problems.add("a toggle heading")
        _check(_children(b), problems)


def blocks_to_md(blocks, notes=None):
    problems = set()
    _check(blocks, problems)
    if problems:
        raise Unsupported(problems)
    return _render(blocks, "", notes)


def _escape_start(line):
    """A line that would open a block when read back gets its opening mark escaped."""
    m = re.match(r"^(\d+)(\.\s)", line)
    if m:
        return m.group(1) + "\\" + line[len(m.group(1)):]
    if re.match(r"^(#{1,6}\s|>|(-{3,}|\*{3,}|_{3,})\s*$|[-*+]\s|```)", line):
        return "\\" + line
    return line


def _render(blocks, pad, notes):
    out, n, prev_t = [], 0, None
    for b in blocks:
        t = b["type"]
        is_list = t in LIST_TYPES
        n = (n + 1 if prev_t == "numbered_list_item" else 1) if t == "numbered_list_item" else 0
        prev_t = t
        if t.startswith("heading"):
            text = "#" * int(t[-1]) + " " + md_from_rich(b[t]["rich_text"], notes)
        elif t == "paragraph":
            text = "\n".join(_escape_start(l) if i == 0 else l
                             for i, l in enumerate(md_from_rich(b[t]["rich_text"], notes).split("\n")))
            if not text.strip() and not _children(b):
                continue                       # a spacer left by editing carries no text
        elif is_list:
            if t == "to_do":
                mark = "- [x]" if b["to_do"].get("checked") else "- [ ]"
            else:
                mark = "-" if t == "bulleted_list_item" else f"{n}."
            width = " " * (len(mark) + 1)
            text = pad + f"{mark} " + md_from_rich(b[t]["rich_text"], notes).replace("\n", "\n" + pad + width)
            kids = _children(b)
            if kids:
                text += "\n" + _render(kids, pad + width, notes)
        elif t == "quote":
            text = "\n".join("> " + l for l in md_from_rich(b[t]["rich_text"], notes).split("\n"))
        elif t == "code":
            c = b["code"]
            code = "".join(_plain_text(e) for e in c.get("rich_text", []))
            cap = "".join(_plain_text(e) for e in c.get("caption", []) or [])
            lang = cap or ("" if c.get("language") in (None, "plain text") else c["language"])
            text = "```" + lang + "\n" + code + "\n```"
        elif t == "divider":
            text = "---"
        elif t == "image":
            img = b["image"]
            cap = "".join(_plain_text(e) for e in img.get("caption", []) or [])
            text = f"![{cap}]({img['external']['url']})"
        else:                                          # table
            rows = [[md_from_rich(c, notes).replace("|", "\\|") for c in r["table_row"]["cells"]]
                    for r in _children(b)]
            text = "\n".join(["| " + " | ".join(rows[0]) + " |",
                              "| " + " | ".join("---" for _ in rows[0]) + " |"]
                             + ["| " + " | ".join(r) + " |" for r in rows[1:]])
        out.append((text, t, is_list))
    family = lambda t: "numbers" if t == "numbered_list_item" else "bullets"
    body = ""
    for k, (text, t, is_list) in enumerate(out):
        if k:
            same_list = is_list and out[k - 1][2] and family(t) == family(out[k - 1][1])
            body += "\n" if same_list else "\n\n"
        body += text
    return body


def canon(md):
    """A body after one trip through blocks. Raises Unsupported when it cannot make the trip."""
    return blocks_to_md(md_to_blocks(md))


def signature(block):
    """One top-level block as canonical markdown; equal signatures mean equal blocks."""
    return blocks_to_md([block])


def words(md):
    return len(md.split())
