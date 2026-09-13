#!/usr/bin/env python3
"""What the board writes, and the rules it writes by.

board.py reads piece folders and shows them. This is the other half: the
changes a writer makes from the board when it runs with --serve. Every function
here takes a piece folder the server has already resolved from the board's own
ids. No path from the page is ever used.

The rules, and they are why this is a file of its own:

  - draft.md changes only by the writer: typed on the board, or a suggestion
    accepted. A version of what is replaced is kept first, in .versions/
    inside the piece folder: at most every ten minutes while typing, every
    time for a suggestion.
  - a save names the version of draft.md it was made against, and a
    suggestion names the text it replaces. If either has changed since (an
    edit in another editor, a stage running), the write is refused and nothing
    is written. Two editors saving one file lose work without anyone
    noticing; this makes it loud instead.
  - an agent answers a comment with a suggestion and never writes draft.md.
  - everything else lands in a form Familiar already reads: an answer in the
    context log, Chosen and Because under an option set, and requests and
    comments and suggestions in edits/rework.md.
  - nothing is deleted. A comment only gains rounds; the history stays.
  - a change that names something by position (the second option set called
    "opening") also names what it expects to find there, and is refused if the
    file has moved underneath it.
"""
import datetime
import hashlib
import os
import pathlib
import re
import tempfile
import time

REWORK = pathlib.Path("edits") / "rework.md"
VERSIONS = ".versions"


class Conflict(Exception):
    """draft.md changed after the page that is saving was opened."""

    def __init__(self, current):
        super().__init__("draft.md changed since this page was opened")
        self.current = current


class Refused(Exception):
    """A write the rules do not allow. The message is shown to the writer."""


# --------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------

def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_exact(path):
    """The file as it is on disk, line endings and all, or '' if it is absent.

    Exact, because the version check compares what the page was given with
    what is on disk now, and a read that tidied line endings would make every
    Windows-edited draft look changed.
    """
    try:
        return path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        raise Refused(f"{path.name} is not UTF-8 text, so the board will not write to it.")


def read_soft(path):
    """For showing, never for writing: a file that is not UTF-8 still reads."""
    try:
        return read_exact(path)
    except Refused:
        return path.read_text(encoding="utf-8", errors="replace")


def write_atomic(path, text):
    """Replace a file in one step, so nothing ever reads half of it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".board-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append(path, text, head=""):
    """Add to the end of a file, starting it with head if it is new."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or not path.read_bytes().strip()
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write((head if new else "") + text)


def stamp(now=None):
    return (now or datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")


def one_line(text):
    return " ".join((text or "").split())


# --------------------------------------------------------------------------
# The draft
# --------------------------------------------------------------------------

def keep_version(folder, text, now=None):
    """Copy what is about to be replaced into .versions/, and return its path."""
    now = now or datetime.datetime.now()
    d = folder / VERSIONS
    d.mkdir(exist_ok=True)
    base = "draft-" + now.strftime("%Y-%m-%d-%H%M%S")
    dest, n = d / f"{base}.md", 2
    while dest.exists():
        dest, n = d / f"{base}-{n}.md", n + 1
    with open(dest, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return dest


def versions(folder):
    d = folder / VERSIONS
    return sorted(d.glob("draft-*.md")) if d.is_dir() else []


def save_draft(folder, base, text, start=None, end=None, now=None, keep_after=None):
    """Write the writer's edit to draft.md. Returns the new hash and the kept copy.

    With start and end, text replaces those lines (end exclusive) and nothing
    else in the file moves. Without them, text is the whole file.

    base is the hash of draft.md as the page received it. If the file on disk
    is not that version any more, Conflict is raised and nothing is written.
    """
    if (folder / "final.md").exists():
        raise Refused("This piece has been sent. draft.md is what learn diff compares "
                      "with what went out, so the board leaves it as it is.")
    path = folder / "draft.md"
    current = read_exact(path)
    if digest(current) != base:
        raise Conflict(current)
    if start is None:
        new = text
    else:
        lines = current.split("\n")
        if not (0 <= start <= end <= len(lines)):
            raise Refused("That passage is not where it was. Reload the page.")
        new = "\n".join(lines[:start] + (text.split("\n") if text else []) + lines[end:])
    if new == current:
        return {"hash": digest(current), "kept": None}
    # keep_after: seconds within which a version already kept is enough. Typing
    # saves every pause, and one version per pause would bury the ones that matter.
    recent = [v.stat().st_mtime for v in versions(folder)]
    fresh = keep_after is not None and recent and time.time() - max(recent) < keep_after
    kept = keep_version(folder, current, now) if current and not fresh else None
    # Checked again just before writing: another editor may have saved while
    # this one was working. The gap left is one os.replace.
    again = read_exact(path)
    if digest(again) != base:
        raise Conflict(again)
    write_atomic(path, new)
    return {"hash": digest(new), "kept": kept}


# --------------------------------------------------------------------------
# Findings in the edit reports
# --------------------------------------------------------------------------

# The six sections every dev-edit report has, and the headings line edits put
# around their findings. A numbered heading with one of these names is a
# section, not a finding.
SECTIONS = {"spark assessment", "thesis check", "critical fixes",
            "line-level refinement map", "implementation roadmap", "gut check",
            "findings", "summary"}


def reports(folder):
    """Edit reports in the piece, as paths relative to the folder."""
    d = folder / "edits"
    if not d.is_dir():
        return []
    return sorted(p.relative_to(folder).as_posix() for p in d.glob("*-report*.md"))


def findings(text):
    """Each finding an edit report makes, in the order it makes them.

    Three shapes turn up, and all three are read: a numbered heading
    (`### 3a. ...`), a numbered bold line (`**1. ...**`), and a bare
    `[line 31] "..."` paragraph with Issue and Fix lines under it. Anything
    inside a code block belongs to the finding above it.

    Each gets a key built from its own first line, not from its position, so a
    verdict stays with its finding when a later look is added to the report.
    """
    lines = text.split("\n")
    fenced, starts, heads, numbered = False, [], [], False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        h = re.match(r"^(#{1,6})\s+(.*)", line)
        if h:
            heads.append((i, len(h.group(1))))
        # `### 3a.` and `### 3.1` both number a finding. A bare number with no
        # full stop (`## 2026 plans`) does not.
        m = re.match(r"^(#{2,4})\s+(\d+[a-z]?\.|\d+\.\d+\.?)\s+(.+?)\s*$", line)
        if m and m.group(3).strip().rstrip(".").lower() not in SECTIONS:
            starts.append((i, m.group(2).rstrip("."), m.group(3), len(m.group(1))))
            numbered = True
            continue
        if h:
            numbered = False            # a section heading ends a numbered finding
            continue
        m = re.match(r"^\*\*(\d+[a-z]?)\.\s+(.+?)\*\*\s*$", line)
        if m:
            # Bold findings keep their [line N] block inside a code block, so
            # a bare one after them is a finding of its own.
            starts.append((i, m.group(1), m.group(2), 7))
            numbered = False
            continue
        # A bare `[line N]` is a finding of its own only where no numbered
        # heading has claimed it: under `### 1. Em dash` it is that finding's body.
        m = re.match(r"^\[line (\d+)\]\s*(.*)$", line)
        if m and not numbered:
            starts.append((i, f"line {m.group(1)}", m.group(2), 7))

    out, seen = [], {}
    for n, (i, label, title, level) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        for hi, hlevel in heads:
            if i < hi < end and hlevel <= min(level, 6):
                end = hi
                break
        body = "\n".join(lines[i + 1:end]).strip("\n")
        if label.startswith("line "):
            issue = re.search(r"(?m)^Issue:\s*(.+)$", body)
            title = f"{issue.group(1).strip()}: {title}" if issue else title
        base = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        key = f"{base}-{hashlib.sha1(lines[i].strip().encode()).hexdigest()[:6]}"
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            key = f"{key}-{seen[key]}"
        out.append({"key": key, "label": label, "title": title.strip().rstrip(".*").strip(),
                    "body": body, "line": i})
    return out


# --------------------------------------------------------------------------
# Option sets
# --------------------------------------------------------------------------

OPTION = re.compile(r"^(?:#{2,6}\s+|\*\*)([A-F])\.\s+(.+?)(?:\*\*)?\s*$")


def option_sets(text):
    """Every `Option set:` block in a file, whether or not it has been chosen."""
    lines = text.split("\n")
    out, fenced, i = [], False, 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            fenced = not fenced
        m = None if fenced else re.match(r"^(#{2,4})\s+Option set:\s*(.+?)\s*$", line)
        if not m:
            i += 1
            continue
        level, title = len(m.group(1)), m.group(2)
        opts, chosen, because, costs, j, inner = [], None, None, None, i + 1, False
        end = len(lines)
        while j < len(lines):
            s = lines[j]
            if s.strip().startswith("```"):
                inner = not inner
            if not inner:
                h = re.match(r"^(#{1,6})\s", s)
                o = OPTION.match(s)
                if o:
                    opts.append({"letter": o.group(1), "label": o.group(2).strip().rstrip("."),
                                 "start": j})
                elif h and len(h.group(1)) <= level:
                    end = j
                    break
                elif s.startswith("Chosen:"):
                    chosen = s.split(":", 1)[1].strip()
                elif s.startswith("Because:"):
                    because = s.split(":", 1)[1].strip()
                    end = j + 1
                    break
                elif s.startswith("Costs:"):
                    costs = j
            j += 1
        if chosen is not None and because is None:
            end = j
        for n, o in enumerate(opts):
            stop = opts[n + 1]["start"] if n + 1 < len(opts) else (
                costs + 1 if costs is not None and costs > o["start"] else end)
            o["body"] = "\n".join(lines[o["start"] + 1:stop]).strip("\n")
        out.append({"title": re.sub(r"\s*\[stage:.*\]\s*$", "", title).strip(),
                    "line": i, "options": opts, "chosen": chosen, "because": because,
                    "insert_at": (costs + 1) if costs is not None else end})
        i = max(end, i + 1)
    return out


def option_files(folder):
    """Files in a piece that can hold an option set, relative to the folder."""
    names = [p for p in folder.glob("*.md") if p.name not in ("draft.md", "SESSION-CONTEXT.md")]
    names += list((folder / "edits").glob("*.md")) if (folder / "edits").is_dir() else []
    return sorted(p.relative_to(folder).as_posix() for p in names
                  if p.name != REWORK.name)


def open_option_sets(folder):
    """[(file, index among sets with that title, set)] still waiting for a pick."""
    out = []
    for rel in option_files(folder):
        text = read_soft(folder / rel)
        if "Option set:" not in text:
            continue
        count = {}
        for s in option_sets(text):
            count[s["title"]] = count.get(s["title"], 0) + 1
            if s["chosen"] is None and len(s["options"]) >= 2:
                out.append((rel, count[s["title"]] - 1, s))
    return out


def choose(folder, rel, title, index, letter, because, now=None):
    """Write Chosen and Because under an option set, and log it."""
    if rel not in option_files(folder):
        raise Refused("That file is not in this piece any more. Reload the page.")
    because = one_line(because)
    if not because:
        raise Refused("A pick needs a Because. Tick 'no reason given' to record that instead.")
    path = folder / rel
    text = read_exact(path)
    same = [s for s in option_sets(text) if s["title"] == title]
    if index >= len(same):
        raise Refused("That option set is not where it was. Reload the page.")
    s = same[index]
    if s["chosen"] is not None:
        raise Refused(f"That one is already chosen: {s['chosen']}.")
    picked = [o for o in s["options"] if o["letter"] == letter]
    if not picked:
        raise Refused(f"There is no option {letter} in that set.")
    lines = text.split("\n")
    at = s["insert_at"]
    while at > s["line"] + 1 and not lines[at - 1].strip():
        at -= 1
    lines[at:at] = ["", f"Chosen: {letter}", f"Because: {because}"]
    write_atomic(path, "\n".join(lines))
    log_entry(folder, rel,
              f'option {letter} picked for "{title}" on the board. Nothing else was\n'
              f"  touched and no stage was run.",
              extra=f"Chosen: {letter}. {picked[0]['label']}\nBecause: {because}\n",
              now=now)


# --------------------------------------------------------------------------
# The draft as a document of blocks, and comments on it
# --------------------------------------------------------------------------

REWORK_HEAD = """# Comments

Comments left on the draft from the board, and the suggestions that answer
them. Each comment is a thread and each exchange a round, newest last, and
nothing here is removed. A `noted` round is a comment the writer has not sent
yet; `asked` is one waiting for an agent, who answers with a `proposed` round
through `familiar rework propose` and never edits draft.md. The writer accepts
a suggestion on the board, which writes it into draft.md after keeping the
version it replaces. A later round's text is the writer's reply to the last
suggestion.
"""
ENTRY = re.compile(r"(?m)^### (r\d+)\.(\d+) · (noted|asked|proposed|taken|dropped) · (.+)$")
OPEN_KINDS = ("noted", "asked", "proposed")


def blocks(raw):
    """(first line of the body, [block]) for a draft.

    A block is a run of lines with no blank line in it, which is what a
    markdown paragraph, heading, list or quote is. A fenced code block is one
    block however many blank lines it holds. Each is {"start", "end", "text"},
    as line numbers in the file with end exclusive. The frontmatter belongs to
    none of them.
    """
    from board import frontmatter_span  # board imports this module
    lines = raw.split("\n")
    span, _ = frontmatter_span(raw)
    first = span[1] + 1 if span else 0
    out, i = [], first
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        start, fenced = i, False
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith("```"):
                fenced = not fenced
            elif not s and not fenced:
                break
            i += 1
        out.append({"start": start, "end": i, "text": "\n".join(lines[start:i])})
    return first, out


def compose(raw, texts):
    """The draft with its body replaced by these blocks, a blank line between
    each. Everything before the body, the frontmatter, is kept as it was."""
    first, _ = blocks(raw)
    head = "\n".join(raw.split("\n")[:first]).rstrip("\n")
    body = "\n\n".join(t.strip("\n") for t in texts if t.strip())
    return (head + "\n\n" if head else "") + body + "\n"


def save_blocks(folder, base, texts, now=None):
    """Save the document as typed on the board.

    A version is kept at most every ten minutes, so an afternoon of typing
    leaves a handful of versions rather than one per pause.
    """
    raw = read_exact(folder / "draft.md")
    if digest(raw) != base:
        raise Conflict(raw)
    return save_draft(folder, base, compose(raw, texts), now=now, keep_after=600)


def whole(raw):
    """The whole body as one passage, for a comment on the whole draft."""
    _, bl = blocks(raw)
    if not bl:
        return None
    lines = raw.split("\n")
    s, e = bl[0]["start"], bl[-1]["end"]
    return {"start": s, "end": e, "text": "\n".join(lines[s:e]), "whole": True}


def plain(text):
    """Words only, for finding quoted words in markdown: no link targets, no marks."""
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    t = re.sub(r"[*_`#>]", "", t)
    return " ".join(t.split()).lower()


def locate(raw, source="", quote="", is_whole=False):
    """The passage a comment is about.

    The block whose text is exactly `source` first; else the one holding the
    quoted words, which is how a comment follows its words when the paragraph
    has moved or been edited around them; else nothing.
    """
    if is_whole:
        return whole(raw)
    _, bl = blocks(raw)
    for b in bl:
        if source and digest(b["text"]) == source:
            return b
    q = plain(quote).strip(".… ")[:80]
    if q:
        for b in bl:
            if q in plain(b["text"]):
                return b
    return None


def read_rework(folder):
    """{thread id: [round, ...]}, each round {"id", "n", "kind", "when", "fields", "body"}."""
    raw = read_soft(folder / REWORK)
    marks = list(ENTRY.finditer(raw))
    threads = {}
    for k, m in enumerate(marks):
        chunk = raw[m.end() + 1:marks[k + 1].start() if k + 1 < len(marks) else len(raw)]
        head, sep, body = chunk.partition("\n\n")
        if not sep:
            head, body = chunk, ""
        threads.setdefault(m.group(1), []).append({
            "id": m.group(1), "n": int(m.group(2)), "kind": m.group(3),
            "when": m.group(4).strip(),
            "fields": dict(re.findall(r"(?m)^([A-Z][A-Za-z ]*):[ \t]*(.*)$", head)),
            "body": body.rstrip("\n"),
        })
    return threads


def state(rounds):
    """What a thread waits for: "noted" (sending), "asked" (an agent),
    "proposed" (the writer), or "closed"."""
    return rounds[-1]["kind"] if rounds and rounds[-1]["kind"] in OPEN_KINDS else "closed"


def open_threads(folder):
    return {t: r for t, r in read_rework(folder).items() if state(r) != "closed"}


def _round(folder, tid, n, kind, fields, body="", now=None):
    """Append one round. Every round carries at least one field, which is how the
    reader tells its fields from its text."""
    head = "".join(f"{k}: {one_line(v)}\n" for k, v in fields.items() if v)
    append(folder / REWORK,
           f"\n### {tid}.{n} · {kind} · {stamp(now)}\n{head}"
           + (f"\n{body.rstrip()}\n" if body.strip() else ""),
           REWORK_HEAD)


def _last(folder, tid, kind, refusal):
    rounds = read_rework(folder).get(tid)
    if not rounds:
        raise Refused("That comment is not in rework.md any more. Reload the page.")
    if rounds[-1]["kind"] != kind:
        raise Refused(refusal)
    return rounds


def target_of(raw, rounds):
    """The passage a thread is about, in the draft as it is now."""
    first, last = rounds[0]["fields"], rounds[-1]["fields"]
    return locate(raw, last.get("Against") or last.get("Block") or first.get("Block", ""),
                  first.get("Quote", ""), first.get("Whole") == "yes")


def flag_field(folder, report, key):
    """How a finding the writer sent is named in the comment, checked first."""
    if report not in reports(folder):
        raise Refused("That report is not in this piece any more. Reload the page.")
    found = {f["key"]: f for f in findings(read_exact(folder / report))}
    if key not in found:
        raise Refused("That finding is not in the report any more. Reload the page.")
    return f"{report} · {key} · {found[key]['label']}. {one_line(found[key]['title'])}"


def comment(folder, text, quote="", block="", own=False, is_whole=False, flag=None,
            send=False, now=None):
    """Leave a comment on words the writer selected, or on the whole draft.

    block is the paragraph's text as the page had it, which finds it exactly;
    the quoted words find it when it has moved since. The comment waits as
    `noted` until it is sent to an agent, unless send is set.
    """
    if (folder / "final.md").exists():
        raise Refused("This piece has been sent, so its draft takes no comments here.")
    text = (text or "").strip()
    if not text and not flag:
        raise Refused("Say what should change, or write your version.")
    target = locate(read_exact(folder / "draft.md"), digest(block) if block else "",
                    quote, is_whole)
    if not target:
        raise Refused("Those words are not in the draft as it is now. Select them again.")
    threads = read_rework(folder)
    tid = f"r{max((int(t[1:]) for t in threads), default=0) + 1}"
    fields = {"Quote": one_line(quote)[:300], "Block": digest(target["text"]),
              "Whole": "yes" if is_whole else "", "Own wording": "yes" if own else "no",
              "Flag": flag}
    body = text or "Work this flag in."
    _round(folder, tid, 1, "noted", fields, body, now)
    if send:
        _round(folder, tid, 1, "asked", fields, body, now)
    return tid


def send(folder, tids=None, now=None):
    """Send comments to an agent: the ones named, or every one not sent yet."""
    sent = []
    for tid, rounds in read_rework(folder).items():
        last = rounds[-1]
        if last["kind"] == "noted" and (tids is None or tid in tids):
            _round(folder, tid, last["n"], "asked", last["fields"], last["body"], now)
            sent.append(tid)
    if tids and not sent:
        raise Refused("Nothing there was waiting to be sent. Reload the page.")
    return sent


def propose(folder, tid, text, note="", now=None):
    """An agent's suggestion for the passage a comment is about. Never touches draft.md."""
    rounds = _last(folder, tid, "asked", "That comment is not waiting for a suggestion.")
    if not (text or "").strip():
        raise Refused("A suggestion needs text.")
    target = target_of(read_exact(folder / "draft.md"), rounds)
    if not target:
        raise Refused("The words that comment is about are not in the draft any more. "
                      "Suggest nothing and tell the writer.")
    _round(folder, tid, rounds[-1]["n"], "proposed",
           {"Against": digest(target["text"]), "Note": note}, text.strip("\n"), now)


def again(folder, tid, why, now=None):
    """Reply to a suggestion with what should change, as the next round."""
    rounds = _last(folder, tid, "proposed", "That comment has no suggestion waiting.")
    why = (why or "").strip()
    if not why:
        raise Refused("Say what should change this time.")
    first = rounds[0]["fields"]
    _round(folder, tid, rounds[-1]["n"] + 1, "asked",
           {"Quote": first.get("Quote"), "Block": rounds[-1]["fields"].get("Against"),
            "Whole": first.get("Whole"), "Own wording": "no", "Flag": first.get("Flag")},
           why, now)


def accept(folder, tid, text=None, now=None):
    """Put a suggestion, or the writer's edit of it, in place of its passage."""
    rounds = _last(folder, tid, "proposed", "That comment has no suggestion waiting.")
    proposal = rounds[-1]
    new = proposal["body"] if text is None else text.strip("\n")
    if not new.strip():
        raise Refused("There is nothing to put in its place.")
    raw = read_exact(folder / "draft.md")
    against = proposal["fields"].get("Against", "")
    target = locate(raw, against, "", rounds[0]["fields"].get("Whole") == "yes")
    if not target or digest(target["text"]) != against:
        raise Refused("That passage has changed since this was suggested. Reply to have it "
                      "suggested again.")
    save_draft(folder, digest(raw), new, target["start"], target["end"], now)
    _round(folder, tid, proposal["n"], "taken",
           {"Edited": "yes" if new != proposal["body"] else "no"}, "", now)
    n = proposal["n"]
    log_entry(folder, "draft.md",
              f"a suggestion was accepted on the board after {n} round"
              f"{'s' if n != 1 else ''}. No stage was run.", now=now)


def drop(folder, tid, now=None):
    """Close a comment without changing the draft: deleted, withdrawn or rejected."""
    rounds = read_rework(folder).get(tid)
    if not rounds or state(rounds) == "closed":
        raise Refused("That comment is already closed. Reload the page.")
    _round(folder, tid, rounds[-1]["n"], "dropped", {"By": "the writer"}, "", now)


def report_flags(folder):
    """[(report, findings)] for every edit report in the piece."""
    return [(r, findings(read_soft(folder / r))) for r in reports(folder)]


def flag_block(finding, bl):
    """Which block a finding is about: by what it quotes, else by the line it names.

    The quote comes first because it stays true after the draft moves; a line
    number is where the text sat when the report was written. None means the
    whole piece, or words no longer in it.
    """
    quotes = re.findall(r'"([^"\n]{20,})"|“([^”\n]{20,})”|^>\s*(.{20,})$',
                        finding["body"], re.M)
    for q in quotes:
        q = plain(next(x for x in q if x)).strip(".… ")[:60]
        for k, b in enumerate(bl):
            if q and q in plain(b["text"]):
                return k
    m = re.search(r"\bline (\d+)\b", f"{finding['label']} {finding['title']}\n{finding['body']}", re.I)
    if m:
        n = int(m.group(1)) - 1
        for k, b in enumerate(bl):
            if b["start"] <= n < b["end"]:
                return k
    return None


# --------------------------------------------------------------------------
# The context log, and answering the open gate
# --------------------------------------------------------------------------

def log_entry(folder, files, changed, extra="", now=None):
    """A board entry in the piece's own log, carrying the open gate forward.

    The last entry is what the board and `familiar decisions` read. Picking an
    option does not answer a question the writer has not answered, so the gate
    that was open stays open.
    """
    from board import last_context_entry  # board imports this module
    ctx = last_context_entry(folder)
    append(folder / "SESSION-CONTEXT.md",
           f"\n## {stamp(now)}  board  {folder.name}\n\n"
           f"Status: {ctx.get('Status') or 'waiting on the writer'}\n"
           f"Files: {files}\n"
           f"What changed: {changed}\n"
           f"{extra}"
           f"Decision gate: {ctx.get('Decision gate') or 'none'}\n"
           f"Next stage: {ctx.get('Next stage') or 'the writer decides'}\n")


def record_answer(piece, answer, now=None):
    """Append the writer's answer to the piece's context log, verbatim.

    Their words, not a summary of them. `learn decisions` reads exactly these
    for the reasoning behind a choice, and a paraphrase is worth nothing to it.
    Returns the last context entry as it stood, so a caller can say what the
    piece was waiting on.
    """
    from board import last_context_entry  # board imports this module
    answer = (answer or "").strip()
    if not answer:
        raise Refused("An answer needs something in it.")
    ctx = last_context_entry(piece)
    gate = (ctx.get("Decision gate") or "").strip()
    with open(piece / "SESSION-CONTEXT.md", "a", encoding="utf-8") as f:
        f.write(
            f"\n## {stamp(now)}  decision  {piece.name}\n\n"
            f"Status: answered, waiting on the writer to start the next stage\n"
            f"Files: none\n"
            f"What changed: the open gate was answered. Nothing else was touched and\n"
            f"  no stage was run.\n"
            f"Gate: {gate or '(none recorded)'}\n"
            f"Answer: {answer}\n"
            f"Decision gate: none, until the next stage sets one\n"
            f"Next stage: {ctx.get('Next stage') or 'the writer decides'}\n"
        )
    return ctx
