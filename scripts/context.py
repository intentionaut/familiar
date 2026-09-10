#!/usr/bin/env python3
"""What Familiar has to work from, counted.

The first job is gathering context, not writing. This module counts the
context a house holds so that `familiar`, `familiar status` and the skill can
say the same thing about it: how many projects have been read, how many keep a
build log, how many reflections there are, whether past writing has been
ingested. Counts, from the filesystem, never a feeling about readiness.

Everything here reads; nothing writes.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

PLACEHOLDER = re.compile(r"\[[^\]\n]{1,80}\]")
DATED = re.compile(r"^## \d{4}-\d{2}-\d{2}", re.M)


def _read(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _is_template(path, shipped):
    """A file is still a template while it shares a bracketed prompt with the
    shipped one. Missing counts as template."""
    text = _read(path)
    if not text:
        return True
    found = set(PLACEHOLDER.findall(text))
    if shipped.is_file() and shipped.resolve() != Path(path).resolve():
        found &= set(PLACEHOLDER.findall(_read(shipped)))
    return bool(found)


def _section(text, heading, stop=None):
    """The body under a heading, to the next heading of the same depth."""
    depth = heading.split(" ")[0]
    m = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^{depth} |\Z)", text, re.M | re.S)
    body = m.group(1) if m else ""
    if stop and stop in body:
        body = body.split(stop, 1)[0]
    return body


def reader_state(cfg):
    """Whether the writer has said who they write for. Three states.

    SECTION LEVEL, NOT FILE LEVEL, and that is the whole point of doing it
    here. `positioning.md` can be well filled in while `## Audience` is still
    the shipped `[your reader]`, and a file-level check calls that ready.

    Only the part above the first subheading counts. Segments are the second
    step, and a writer who has described one reader has answered this question
    whatever they called the section under it.
    """
    text = _read(Path(cfg) / "positioning.md")
    if not text:
        return "missing"
    body = _section(text, "## Audience", stop="\n### ")
    if not body.strip():
        return "missing"
    shipped = _section(_read(ROOT / "knowledge" / "positioning.md"),
                       "## Audience", stop="\n### ")
    shared = set(PLACEHOLDER.findall(body)) & set(PLACEHOLDER.findall(shipped))
    return "template" if shared else "declared"


def segment_count(cfg):
    """Declared segments, counted by the id in backticks the house asks for.

    Matches both shapes the file invites: a bullet per segment, and a table
    with a row each. A backticked id in prose is not counted, because a
    sentence mentioning `builders` is not a declaration.

    THE WHOLE AUDIENCE SECTION IS SCANNED, not a subsection with a fixed name.
    The shipped file calls it Segments and this house calls it "The segments,
    declared once"; a check keyed to one wording reports zero for the other and
    then offers a writer a step they finished weeks ago.

    `id` is the shipped example and never counts as a declaration.
    """
    body = _section(_read(Path(cfg) / "positioning.md"), "## Audience")
    seen = set()
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith(("-", "|")):
            continue
        m = re.match(r"^[-|]\s*\|?\s*`([a-z0-9][a-z0-9-]*)`", line)
        if m and m.group(1) != "id":
            seen.add(m.group(1))
    return len(seen)


def context_counts(cfg):
    """Return a dict of what the house at `cfg` holds.

    projects: digests written under knowledge/digests/
    logs: projects registered in build-logs.md as keeping a log
    reflections: dated entries across the reflections folder, or None when
                 reflection is off or unset, with `reflection_state` saying which
    past_writing: True when voice-guide.md is no longer the shipped template,
                  which is what `learn ingest` leaves behind
    """
    cfg = Path(cfg)
    shipped = ROOT / "knowledge"
    digests = sorted((cfg / "digests").glob("*.md")) if (cfg / "digests").is_dir() else []

    logs = 0
    for line in _read(cfg / "build-logs.md").splitlines():
        if re.match(r"\s*-\s+`[^`]+`\s*:\s*`[^`]+`", line):
            logs += 1

    refl_text = _read(cfg / "reflection.md")
    setting = re.search(r"^- Reflection:\s*(on|off)\s*$", refl_text, re.M | re.I)
    reflections = None
    if not setting:
        reflection_state = "unset"
    elif setting.group(1).lower() == "off":
        reflection_state = "off"
    else:
        reflection_state = "on"
        m = re.search(r"^- Reflections live in:\s*(.+?)\s*$", refl_text, re.M)
        folder = Path(m.group(1)).expanduser() if m and not m.group(1).startswith("[") else None
        reflections = 0
        if folder and folder.is_dir():
            for f in folder.glob("*.md"):
                if f.stem.lower() in ("threads", "readme"):
                    continue
                reflections += len(DATED.findall(_read(f)))

    past_writing = not _is_template(cfg / "voice-guide.md", shipped / "voice-guide.md")

    return dict(projects=len(digests), project_names=[d.stem for d in digests], logs=logs,
                reflections=reflections, reflection_state=reflection_state,
                past_writing=past_writing, reader=reader_state(cfg),
                segments=segment_count(cfg))


def context_lines(counts):
    """The block both the CLI and status print, indented two spaces."""
    r = counts["reflections"]
    if counts["reflection_state"] == "on":
        refl = f"{r} entr{'y' if r == 1 else 'ies'}"
    elif counts["reflection_state"] == "off":
        refl = "off"
    else:
        refl = "not turned on"
    reader = {"declared": "described", "template": "not said yet",
              "missing": "not said yet"}[counts.get("reader", "missing")]
    if counts.get("segments"):
        n = counts["segments"]
        reader = f"described, {n} segment{'' if n == 1 else 's'}"
    return [
        "  What I have to work from:",
        f"    Reader               {reader}",
        f"    Projects read        {counts['projects']}",
        f"    Build logs           {counts['logs']}",
        f"    Reflections          {refl}",
        f"    Past writing         {'ingested' if counts['past_writing'] else 'none ingested'}",
    ]


def gathering_offers(counts, project=None, asked_reader=False):
    """The commands that gather more, only the ones that would add something.

    Ordered by how much each adds to the next tier: the reader first when it
    is missing, because it is the only one that needs no history; then other
    projects, because themes need more than one; then the loop that captures
    every session from now on; then what has already been published; then
    reflection. Nothing is offered that is already in place.

    `asked_reader` says the caller already put the question in front of the
    writer on this screen. Asking twice in one breath is how a list of offers
    turns into a list of nags, and the second ask is the one people learn to
    scroll past.
    """
    lines = []
    # FIRST WHEN IT IS MISSING, AND THE REASON IS WORTH KEEPING HERE. Every
    # other offer below needs something to have accumulated: another project
    # read, a session logged, writing already published. This one needs no
    # history at all, so it is the only rung a writer can climb on their first
    # evening, and it is what sorts everything the other four produce.
    if counts.get("reader", "missing") != "declared" and not asked_reader:
        lines.append("    knowledge/positioning.md         who you write for, in two or three lines")
    if counts["projects"] <= 1:
        lines.append("    familiar engage --all            read your other projects (asks first)")
    if project and counts["logs"] == 0:
        lines.append(f"    familiar log add {project:<15} capture what ships, every session, from now on")
    elif counts["logs"] == 0:
        lines.append("    familiar log add <project>       capture what ships, every session, from now on")
    if not counts["past_writing"]:
        lines.append("    learn ingest <past writing>      what you have already published, for voice and themes")
    if counts["reflection_state"] != "on":
        lines.append("    knowledge/reflection.md          two questions a week, in your words")
    return lines


def enough_for_themes(counts):
    """Themes need more than one source. Two projects, or one project plus any
    of a log, a reflection entry or ingested writing.

    Sources only. Whether anybody knows who the writing is for is a separate
    question, answered by `reader_state`, and kept separate on purpose: a
    writer with the material and no reader has enough to harvest, and should
    be told what they are missing rather than blocked."""
    others = (counts["logs"] > 0) + bool(counts["reflections"]) + counts["past_writing"]
    return counts["projects"] >= 2 or (counts["projects"] >= 1 and others >= 1)


if __name__ == "__main__":
    from paths import knowledge_dir
    cfg, _ = knowledge_dir(None)
    c = context_counts(cfg)
    print("\n".join(context_lines(c)))
    for l in gathering_offers(c):
        print(l)
