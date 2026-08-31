#!/usr/bin/env python3
"""Report whether the coming week's social slots already hold scheduled posts.

Reads channels, ids and cadence from knowledge/social-schedule.md, so it works
for whatever channels and days a writer actually uses. Nothing here is specific
to one writer or one set of days.

Usage:  queue-check.py [YYYY-MM-DD]      a Monday; defaults to next Monday
        queue-check.py --config PATH     a social-schedule.md elsewhere

Prints one line per slot ("<channel> <day> <date>: scheduled|empty"), then a
final line "queue: full" or "queue: gaps". Exits 0 either way; exits 2 if it
could not check, which is not the same as empty.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys

HOME = pathlib.Path(__file__).resolve().parent.parent
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def find_config(explicit):
    """Familiar's config resolution order. The host is one location, not the one."""
    if explicit:
        return pathlib.Path(explicit)
    for candidate in [
        os.environ.get("FAMILIAR_CONFIG"),
        os.environ.get("FAMILIAR_HOST_CONFIG"),
        "./knowledge",
        os.path.expanduser("~/.familiar/knowledge"),
        HOME / "knowledge",
    ]:
        if not candidate:
            continue
        p = pathlib.Path(candidate) / "social-schedule.md"
        if p.is_file():
            return p
    return None


def section(text, heading):
    """Lines under a `## heading`, up to the next `## `."""
    out, capturing = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            capturing = line[3:].strip().lower().startswith(heading.lower())
            continue
        if capturing:
            out.append(line)
    return out


def rows(lines):
    """Markdown table rows, minus header and separator, minus unfilled placeholders."""
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or set("".join(cells)) <= set("-: "):
            continue
        if cells[0].lower() in ("channel", "name"):
            continue
        yield [c.strip("`") for c in cells]


def parse(config_path):
    text = config_path.read_text()
    ids, cadence = {}, {}
    for cells in rows(section(text, "Scheduler")):
        if len(cells) >= 2 and "[" not in cells[1] and cells[1]:
            ids[cells[0].lower()] = cells[1]
    for cells in rows(section(text, "Cadence")):
        if len(cells) >= 2:
            chan = cells[0].strip("[]").lower()
            days = [d for d in DAYS if d.lower() in cells[1].lower()]
            if chan and days:
                cadence[chan] = days
    # Only the setting line counts. Prose that mentions the flag (the block
    # explains `scheduler: none`) must not be read as the setting.
    scheduler = "none"
    for line in section(text, "Scheduler"):
        m = re.match(r"\s*[-*]?\s*\**scheduler\**\s*:\s*\**\s*`?([a-z]+)`?", line, re.I)
        if m:
            scheduler = m.group(1).lower()
            break
    return scheduler, ids, cadence


def next_monday(today=None):
    today = today or dt.date.today()
    ahead = (7 - today.weekday()) % 7 or 7
    return today + dt.timedelta(days=ahead)


def query(channel_id):
    """Ask the scheduler for this channel's scheduled posts. Returns raw text."""
    req = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "familiar-queue-check", "version": "1.0"}}}),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "list_posts",
            # Buffer wants status as an array; a bare string is rejected.
            "arguments": {"channelId": channel_id, "status": ["scheduled"]}}}),
    ]) + "\n"
    try:
        proc = subprocess.run(
            [str(HOME / "scripts" / "buffer-mcp.sh")],
            input=req, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    if proc.returncode != 0 and not proc.stdout:
        return None, proc.stderr.strip().splitlines()[0] if proc.stderr else "no response"
    return proc.stdout, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("monday", nargs="?")
    ap.add_argument("--config")
    args = ap.parse_args()

    config = find_config(args.config)
    if not config:
        print("could not check: no social-schedule.md found", file=sys.stderr)
        return 2
    scheduler, ids, cadence = parse(config)
    if scheduler == "none" or not ids:
        print(f"could not check: no scheduler configured in {config}", file=sys.stderr)
        return 2

    monday = dt.date.fromisoformat(args.monday) if args.monday else next_monday()
    dates = {DAYS[i]: monday + dt.timedelta(days=i) for i in range(7)}

    gaps = False
    unchecked = False
    for channel, days in cadence.items():
        cid = ids.get(channel)
        if not cid:
            print(f"{channel}: not connected (no channel id in {config.name})")
            unchecked = True
            continue
        body, err = query(cid)
        if body is None:
            print(f"{channel}: could not check ({err})")
            unchecked = True
            continue
        for day in days:
            date = dates[day].isoformat()
            state = "scheduled" if date in body else "empty"
            if state == "empty":
                gaps = True
            print(f"{channel} {day} {date}: {state}")

    if unchecked:
        print("queue: unknown")
        return 2
    print("queue: gaps" if gaps else "queue: full")
    return 0


if __name__ == "__main__":
    sys.exit(main())
