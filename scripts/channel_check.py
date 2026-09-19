#!/usr/bin/env python3
"""Hold the channel registry to one answer, across the files that use it.

Reads `knowledge/channels.md` and checks the four failures a split channel
model invites:

  unknown        a channel used in social-schedule.md or a piece's social.md
                 that the registry does not declare
  missing        a channel block with no destination rule, or a `## Chosen`
                 post with no `destination:` line
  duplicate      one post naming two destinations, against the
                 one-post-one-destination rule
  contradictory  the registry and social-schedule.md disagreeing on a
                 channel's weekly count or character limit, or a utm_source
                 that breaks the links.md hostname convention

It reports and never edits, and it invents nothing: a file that is absent
or still the template is a supported way to work and gets one quiet line.

Usage:
  channel_check.py [--config DIR] [--piece DIR ...]

Exit 0 clean or unconfigured, 1 findings, 2 could not run.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import knowledge_dir, pieces_dirs  # noqa: E402

REQUIRED = ("Job", "Default CTA and destination", "Review and publish gate")


def parse_registry(path):
    """Parse channels.md into {id: {field: value}}. Empty dict when the
    file is absent, still the template, or declares no channels."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    channels = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^## Channel: (\S+)\s*$", line)
        if m:
            current = m.group(1)
            channels[current] = {}
            continue
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", line)
        if m and current:
            channels[current][m.group(1)] = m.group(2).strip()
    return channels


def schedule_tables(path):
    """The channel names in social-schedule.md's tables: (channels, cadence
    {name: count per week}, limits {name: limit}). Empty when the file is
    absent or its tables are unfilled placeholders."""
    names, cadence, limits = [], {}, {}
    if not path.is_file():
        return names, cadence, limits
    text = path.read_text(encoding="utf-8", errors="replace")
    in_table = None
    for line in text.splitlines():
        h = re.match(r"^## (Channels|Cadence|Scheduler)\s*$", line)
        if h:
            in_table = h.group(1)
            continue
        if line.startswith("## "):
            in_table = None
        if not line.startswith("|") or in_table is None:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or set(cells[0]) <= set("-: ") or cells[0].lower() == "channel":
            continue
        name = cells[0]
        if name.startswith("[") and name.endswith("]"):
            continue  # an unfilled placeholder row
        if any(c.startswith("[") and c.endswith("]") for c in cells[1:]):
            continue  # a template row: bracketed cells mean not filled in
        names.append(name)
        if in_table == "Cadence" and len(cells) >= 3:
            m = re.search(r"(\d+)", cells[2])
            if m:
                cadence[name] = int(m.group(1))
        if in_table == "Scheduler" and len(cells) >= 3:
            m = re.search(r"(\d+)", cells[2])
            if m:
                limits[name] = int(m.group(1))
    return names, cadence, limits


def links_destinations(path):
    """The destination names declared in links.md's Destinations table."""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    in_table = False
    for line in text.splitlines():
        if re.match(r"^## Destinations\s*$", line):
            in_table = True
            continue
        if line.startswith("## "):
            in_table = False
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] and cells[0].lower() not in ("name",) \
                    and not set(cells[0]) <= set("-: ") \
                    and not cells[0].startswith("["):
                out.append(cells[0])
    return out


def chosen_items(path):
    """The posts under `## Chosen` in a piece's social.md: a list of
    {heading, channels, destinations}. Sections named held or candidate
    pool are not input, per prompts/publish.md."""
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_chosen = False
    items, current = [], None
    for line in lines:
        h = re.match(r"^(##+)\s+(.*)$", line)
        if h:
            level, title = len(h.group(1)), h.group(2).strip()
            if level == 2:
                in_chosen = title.lower().startswith("chosen")
                if current:
                    items.append(current)
                current = None
                continue
            if in_chosen and level >= 3:
                if current:
                    items.append(current)
                current = {"heading": title, "channels": [], "destinations": []}
            continue
        if in_chosen and current is not None:
            m = re.match(r"^channel:\s*(\S+)\s*$", line)
            if m:
                current["channels"].append(m.group(1))
            m = re.match(r"^destination:\s*(.+)$", line)
            if m:
                current["destinations"].append(m.group(1).strip())
    if current:
        items.append(current)
    return items


def check(cfg, extra_pieces=None):
    """Return (problems, warnings). Never raises on a missing file."""
    cfg = Path(cfg)
    problems, warnings = [], []
    registry = parse_registry(cfg / "channels.md")
    if not registry:
        return problems, warnings

    # missing: every channel declares the fields the stages rely on
    for cid, fields in sorted(registry.items()):
        for req in REQUIRED:
            if not fields.get(req):
                problems.append(
                    f"channels.md: channel '{cid}' has no '{req}' - "
                    f"stages cannot route to it without one")

    # unknown + contradictory, against the schedule
    names, cadence, limits = schedule_tables(cfg / "social-schedule.md")
    by_schedule = {f.get("Schedule name"): cid
                   for cid, f in registry.items() if f.get("Schedule name")}
    for name in names:
        if name not in by_schedule and name not in registry:
            problems.append(
                f"social-schedule.md: channel '{name}' is not declared in "
                f"channels.md - declare it or remove the row")
    for name, cid in by_schedule.items():
        fields = registry[cid]
        m = re.search(r"(\d+)", fields.get("Cadence", ""))
        if name in cadence and m and cadence[name] != int(m.group(1)):
            problems.append(
                f"channel '{cid}': registry cadence says {m.group(1)} a "
                f"week but social-schedule.md says {cadence[name]} - one "
                f"answer, declared once")
        form = fields.get("Form and length", "")
        # The hard limit is the ceiling publish counts against; a channel
        # that only gives a comfortable length has nothing to contradict.
        m = re.search(r"([\d,]+)\s*hard", form) or \
            re.search(r"([\d,]+)\s*(?:characters|chars)", form)
        if name in limits and m:
            reg_limit = int(m.group(1).replace(",", ""))
            if limits[name] != reg_limit:
                problems.append(
                    f"channel '{cid}': registry limit says {reg_limit} but "
                    f"social-schedule.md says {limits[name]} - one answer, "
                    f"declared once")

    # contradictory: utm_source against the links.md hostname convention
    for cid, fields in sorted(registry.items()):
        utm = fields.get("utm", "")
        m = re.search(r"source `([^`]+)`", utm)
        if m and "." not in m.group(1):
            warnings.append(
                f"channel '{cid}': utm_source '{m.group(1)}' is not a "
                f"hostname - links.md says source is the hostname, one "
                f"property, one spelling")

    # unknown, missing, duplicate, across every piece's social.md
    dest_names = links_destinations(cfg / "links.md")
    piece_dirs = [Path(p) for p in (extra_pieces or [])] or pieces_dirs()
    for pdir in piece_dirs:
        if not pdir.is_dir():
            continue
        for piece in pdir.iterdir():
            if not piece.is_dir() or piece.name.startswith((".", "_")):
                continue
            for item in chosen_items(piece / "social.md"):
                where = f"{piece.name}: '{item['heading']}'"
                for cid in item["channels"]:
                    if cid not in registry:
                        problems.append(
                            f"{where}: channel '{cid}' is not declared in "
                            f"channels.md")
                if not item["destinations"]:
                    problems.append(
                        f"{where}: no destination - one post, one "
                        f"destination, declared before scheduling")
                if len(item["destinations"]) > 1:
                    problems.append(
                        f"{where}: {len(item['destinations'])} destinations "
                        f"- one post sends the reader to one place")
                elif item["destinations"]:
                    d = item["destinations"][0].lower()
                    named = [n for n in dest_names if n.lower() in d]
                    if len(named) > 1:
                        problems.append(
                            f"{where}: destination names {named} - one "
                            f"post sends the reader to one place")
    return problems, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="a knowledge folder to check instead")
    ap.add_argument("--piece", action="append", default=[],
                    help="a piece folder to check; repeatable")
    args = ap.parse_args()
    cfg, _ = knowledge_dir(args.config)

    if not (Path(cfg) / "channels.md").is_file() or not parse_registry(
            Path(cfg) / "channels.md"):
        print("  Channels: not configured (declare them in channels.md)")
        return 0

    problems, warnings = check(cfg, args.piece)
    for w in warnings:
        print(f"  warning: {w}")
    for p in problems:
        print(f"  problem: {p}")
    if problems:
        return 1
    print("  Channels: consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
