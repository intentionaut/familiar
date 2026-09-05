#!/usr/bin/env python3
"""Whether today's session earns a check-in offer, and the two clocks that
decide it.

`knowledge/checkin.md` holds the setting: on/off, cadence, and two dates this
module owns. `Last engaged` moves only on real engagement (a `familiar` run,
`engage --all`, or a check-in the writer said yes to) — it is what makes "it's
been a while" a true claim about the work. `Last offered` moves every time the
offer is actually said, yes or no — it is what stops the same quiet week being
mentioned every session between now and the next one.

A repo takes itself out with `engage = off` in its own `.familiar`, checked
against the session's own working directory, never the Familiar house.

Everything that decides whether to speak lives here so the SessionStart hook
(hooks/session-checkin.sh) and the CLI (which calls `mark_engaged` after a
real run) agree on what the clocks mean.
"""
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CADENCE_DAYS = {"weekly": 7, "fortnightly": 14, "monthly": 30}


def _read(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _git_top(path):
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(path),
                        capture_output=True, text=True)
    return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def _has_commits(top):
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(top),
                        capture_output=True, text=True)
    return r.returncode == 0


def repo_opted_out(start_dir):
    """True when start_dir, or its git top-level, has a `.familiar` naming
    `engage = off`. Checked against the session's own directory, not HOME."""
    top = _git_top(start_dir)
    for d in (Path(start_dir), top):
        if not d:
            continue
        f = d / ".familiar"
        if not f.is_file():
            continue
        for line in _read(f).splitlines():
            line = line.split("#", 1)[0].strip()
            if "=" not in line:
                continue
            k, v = (p.strip().lower() for p in line.split("=", 1))
            if k == "engage" and v == "off":
                return True
    return False


def settings(cfg):
    """Parse checkin.md: on/off, cadence in days, and the two clocks."""
    text = _read(Path(cfg) / "checkin.md")
    on = bool(re.search(r"^- Check-in:\s*on\s*$", text, re.M | re.I))
    m = re.search(r"^- Cadence:\s*(weekly|fortnightly|monthly)\s*$", text, re.M | re.I)
    days = CADENCE_DAYS.get(m.group(1).lower() if m else "weekly", 7)

    def _d(field):
        dm = re.search(rf"^- {field}:\s*(\d{{4}}-\d{{2}}-\d{{2}})\s*$", text, re.M)
        return date.fromisoformat(dm.group(1)) if dm else None

    return dict(on=on, cadence_days=days,
                last_engaged=_d("Last engaged"), last_offered=_d("Last offered"))


def _elapsed(clock, cadence_days):
    """True when `clock` is unset, or the cadence has passed since it."""
    return clock is None or (date.today() - clock).days >= cadence_days


def due(cfg, start_dir):
    """(due, first_time, project_name) for a session starting in start_dir.

    due is False whenever check-in is off, the cadence has not elapsed since
    Last engaged, the cadence has not elapsed since Last offered (already
    asked this window), start_dir is not inside a git repository with
    commits, or that repository has opted itself out.
    """
    s = settings(cfg)
    if not s["on"]:
        return False, False, None
    if not _elapsed(s["last_engaged"], s["cadence_days"]):
        return False, False, None
    if not _elapsed(s["last_offered"], s["cadence_days"]):
        return False, False, None
    top = _git_top(start_dir)
    if not top or not _has_commits(top):
        return False, False, None
    if repo_opted_out(start_dir):
        return False, False, None
    name = top.name
    first_time = not (Path(cfg) / "digests" / f"{name}.md").is_file()
    return True, first_time, name


def _set_field(cfg, field, value):
    p = Path(cfg) / "checkin.md"
    if not p.is_file():
        return
    text = _read(p)
    pat = re.compile(rf"^(- {re.escape(field)}:).*$", re.M)
    line = f"- {field}: {value}"
    text = pat.sub(line, text, count=1) if pat.search(text) else text.rstrip("\n") + f"\n{line}\n"
    try:
        p.write_text(text, encoding="utf-8")
    except OSError:
        pass


def mark_offered(cfg):
    _set_field(cfg, "Last offered", date.today().isoformat())


def mark_engaged(cfg):
    today = date.today().isoformat()
    _set_field(cfg, "Last engaged", today)
    _set_field(cfg, "Last offered", today)


def cmd_hook():
    """Entry point for the SessionStart hook. Reads the hook JSON on stdin,
    prints additionalContext JSON on stdout when an offer is due, prints
    nothing otherwise. Never raises: a session with nothing to do with
    Familiar must see no trace of this running."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return
    cwd = payload.get("cwd") or os.getcwd()
    try:
        os.chdir(cwd)
    except OSError:
        return
    try:
        from paths import knowledge_dir
        cfg, whose = knowledge_dir(None)
        if whose == "the shipped templates":
            return  # no house configured; nothing to offer against
        is_due, first_time, name = due(cfg, cwd)
    except Exception:
        return
    if not is_due:
        return
    mark_offered(cfg)
    if first_time:
        context = (
            f"Familiar has not read {name} yet. Offer, in one line, to run "
            f"`familiar` and see what its history says. Nothing is drafted "
            f"until the writer says so."
        )
    else:
        context = (
            f"It has been a while since the last check-in through Familiar "
            f"in {name}. Offer, in one line, to run `familiar` and see "
            f"what's changed. Nothing is drafted until the writer says so."
        )
    try:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": context}}))
    except Exception:
        return


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "hook":
        cmd_hook()
