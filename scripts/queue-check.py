#!/usr/bin/env python3
"""Report whether the coming week's social slots already hold scheduled posts.

Reads channels, ids and cadence from knowledge/social-schedule.md, so it works
for whatever channels and days a writer actually uses. Nothing here is specific
to one writer or one set of days.

Usage:  queue-check.py [YYYY-MM-DD]      a Monday; defaults to next Monday
        queue-check.py --config PATH     a social-schedule.md elsewhere

Prints one line per slot ("<channel> <day> <date>: scheduled|empty"), then a
final line:

    queue: full      every checked slot has a scheduled post
    queue: gaps      at least one slot is genuinely empty
    queue: unknown   the scheduler could not be read; slot states are NOT known

Exits 0 for full or gaps, 2 for unknown. Unknown is never reported as empty: a
check that cannot see the queue says so, rather than telling a planner that a
full week is waiting to be filled.

One scheduler session serves the whole check: the account is read once for the
organisation id the post listing needs, then each channel is listed in turn.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import select
import subprocess
import sys

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

HOME = pathlib.Path(__file__).resolve().parent.parent
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def find_config(explicit):
    """Familiar's config resolution order. The host is one location, not the one."""
    if explicit:
        return pathlib.Path(explicit)
    candidates = [
        os.environ.get("FAMILIAR_KNOWLEDGE"),
        os.environ.get("FAMILIAR_CONFIG"),
        os.environ.get("FAMILIAR_HOST_CONFIG"),
    ]
    # The per-install `.familiar` file, same as paths.py reads.
    for base in (pathlib.Path.cwd(), HOME):
        f = base / ".familiar"
        if f.is_file():
            for line in f.read_text().splitlines():
                line = line.split("#", 1)[0].strip()
                if line.lower().startswith("knowledge") and "=" in line:
                    candidates.append(os.path.expanduser(line.split("=", 1)[1].strip()))
    candidates += ["./knowledge", os.path.expanduser("~/.familiar/knowledge"), HOME / "knowledge"]
    for candidate in candidates:
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


def header_of(lines):
    """The column names of the first table under a heading, as written."""
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].lower() in ("channel", "name"):
            return cells
    return []


def timezone_of(text):
    """The zone slot times are written in.

    A `Timezone` column in the Cadence table wins. Failing that, a zone named in
    a column header, as in "Default time (Europe/London)". Failing both, UTC,
    and the day boundary is then only right for writers in UTC.
    """
    lines = section(text, "Cadence")
    header = header_of(lines)
    if not header:
        return "UTC"
    for cells in rows(lines):
        for i, name in enumerate(header):
            if name.lower().startswith("timezone") and i < len(cells) and "/" in cells[i] and "[" not in cells[i]:
                return cells[i]
        break
    for name in header:
        m = re.search(r"\(([A-Za-z_]+/[A-Za-z_]+)\)", name)
        if m:
            return m.group(1)
    return "UTC"


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


def rpc(id_, method, params=None):
    msg = {"jsonrpc": "2.0", "method": method}
    if id_ is not None:
        msg["id"] = id_
    if params is not None:
        msg["params"] = params
    return json.dumps(msg)


INIT = {"protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "familiar-queue-check", "version": "2.0"}}


def list_request(channel_id, organization_id=None):
    """The JSON-RPC lines that ask a scheduler for a channel's queue.

    Split out from the session so its shape can be checked without a network
    call. The scheduler wants `status` as an array and `channelIds` as a list,
    and requires the organisation id on every listing.
    """
    args = {"channelIds": [channel_id], "status": ["scheduled"]}
    if organization_id:
        args["organizationId"] = organization_id
    return "\n".join([
        rpc(1, "initialize", INIT),
        rpc(None, "notifications/initialized"),
        rpc(2, "tools/call", {"name": "list_posts", "arguments": args}),
    ]) + "\n"


def tool_payload(response):
    """The JSON a tool call returned, or None. Tools answer with their result
    as text inside content[0]; that text is itself JSON."""
    if not isinstance(response, dict) or "error" in response:
        return None
    content = (response.get("result") or {}).get("content") or []
    if not content:
        return None
    text = content[0].get("text", "")
    try:
        return json.loads(text)
    except ValueError:
        return None


def organization_id(payload):
    """First organisation id in an account payload, walking whatever shape it has."""
    if isinstance(payload, dict):
        orgs = payload.get("organizations")
        if isinstance(orgs, list) and orgs and isinstance(orgs[0], dict) and orgs[0].get("id"):
            return orgs[0]["id"]
        for v in payload.values():
            found = organization_id(v)
            if found:
                return found
    elif isinstance(payload, list):
        for v in payload:
            found = organization_id(v)
            if found:
                return found
    return None


def posts_of(payload):
    """Posts from a listing, whichever shape the scheduler used.

    A GraphQL connection ({"edges": [{"node": {...}}]}) is the current shape.
    A plain list, or a dict holding one under posts/data/items, is tolerated so
    the check keeps working if that changes back.
    """
    if isinstance(payload, dict):
        if "edges" in payload:
            return [e.get("node", {}) for e in payload["edges"] if isinstance(e, dict)]
        for key in ("posts", "data", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return []
    if isinstance(payload, list):
        return payload
    return []


def local_dates(posts, zone):
    """The local calendar dates the posts are due on.

    Due times come back in UTC. An 08:30 London post is 07:30Z in summer and a
    23:30 post is next-day UTC in winter, so the conversion is what decides
    which day a slot counts as filled.
    """
    tz = ZoneInfo(zone) if ZoneInfo and zone != "UTC" else dt.timezone.utc
    out = set()
    for p in posts:
        due = p.get("dueAt") or p.get("due_at") or p.get("scheduledAt")
        if not due:
            continue
        try:
            when = dt.datetime.fromisoformat(str(due).replace("Z", "+00:00"))
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=dt.timezone.utc)
        out.add(when.astimezone(tz).date())
    return out


class Session:
    """One scheduler session over stdio, with a deadline on every answer."""

    def __init__(self, timeout=90):
        self.deadline = dt.datetime.now() + dt.timedelta(seconds=timeout)
        self.proc = subprocess.Popen(
            [str(HOME / "scripts" / "buffer-mcp.sh")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.answers = {}

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def wait_for(self, id_):
        while id_ not in self.answers:
            remaining = (self.deadline - dt.datetime.now()).total_seconds()
            if remaining <= 0 or self.proc.poll() is not None:
                return None
            ready, _, _ = select.select([self.proc.stdout], [], [], min(remaining, 5))
            if not ready:
                continue
            line = self.proc.stdout.readline()
            if not line:
                return None
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if isinstance(msg.get("id"), int):
                self.answers[msg["id"]] = msg
        return self.answers[id_]

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.terminate()
        except OSError:
            pass


def query_all(ids):
    """Ask the scheduler for every channel's queue. Returns ({channel: posts}, error)."""
    try:
        session = Session()
    except OSError as exc:
        return None, str(exc)
    try:
        session.send(rpc(1, "initialize", INIT))
        session.send(rpc(None, "notifications/initialized"))
        if session.wait_for(1) is None:
            return None, "no response to initialize (the bridge timed out, or the key is missing)"
        session.send(rpc(10, "tools/call", {"name": "get_account", "arguments": {}}))
        account = session.wait_for(10)
        if account is None:
            return None, "no response from get_account"
        if "error" in account:
            return None, f"get_account: {account['error'].get('message', '?')}"
        org = organization_id(tool_payload(account))
        if not org:
            return None, "no organisation id in the account payload"
        results = {}
        for n, (channel, cid) in enumerate(sorted(ids.items()), start=11):
            args = {"organizationId": org, "channelIds": [cid], "status": ["scheduled"]}
            session.send(rpc(n, "tools/call", {"name": "list_posts", "arguments": args}))
            answer = session.wait_for(n)
            if answer is None:
                return None, f"no response from list_posts for {channel}"
            if "error" in answer:
                return None, f"list_posts for {channel}: {answer['error'].get('message', '?')}"
            payload = tool_payload(answer)
            if payload is None:
                return None, f"list_posts for {channel} returned something that is not JSON"
            results[channel] = posts_of(payload)
        return results, None
    finally:
        session.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("monday", nargs="?")
    ap.add_argument("--config")
    args = ap.parse_args()

    config = find_config(args.config)
    if not config:
        print("could not check: no social-schedule.md found", file=sys.stderr)
        print("queue: unknown")
        return 2
    scheduler, ids, cadence = parse(config)
    if scheduler == "none" or not ids:
        print(f"could not check: no scheduler configured in {config}", file=sys.stderr)
        print("queue: unknown")
        return 2

    zone = timezone_of(config.read_text())
    monday = dt.date.fromisoformat(args.monday) if args.monday else next_monday()
    dates = {DAYS[i]: monday + dt.timedelta(days=i) for i in range(7)}

    wanted = {ch: ids[ch] for ch in cadence if ch in ids}
    missing = [ch for ch in cadence if ch not in ids]
    for ch in missing:
        print(f"{ch}: not connected (no channel id in {config.name})")

    queues, err = (query_all(wanted) if wanted else ({}, None))
    if queues is None:
        print(f"could not check: {err}", file=sys.stderr)
        print("queue: unknown")
        return 2

    gaps = False
    for channel, days in cadence.items():
        if channel not in queues:
            continue
        have = local_dates(queues[channel], zone)
        for day in days:
            date = dates[day]
            state = "scheduled" if date in have else "empty"
            if state == "empty":
                gaps = True
            print(f"{channel} {day} {date.isoformat()}: {state}")

    if missing:
        print("queue: unknown")
        return 2
    print("queue: gaps" if gaps else "queue: full")
    return 0


if __name__ == "__main__":
    sys.exit(main())
