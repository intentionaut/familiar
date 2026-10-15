#!/usr/bin/env python3
"""Read a piece's research signals for the outline stage.

    python3 scripts/signals.py pieces/2026-01-01-slug          # for a person to read
    python3 scripts/signals.py pieces/2026-01-01-slug --json   # the same, for a stage to read

A research tool may leave a `signals.json` in the piece folder: at most five
signals drawn from the sources the writer kept. Each signal is one line, the
addresses of the sources it rests on, and one line on what it changes for the
piece. The file can also list what the research left unresolved or held back.

The file comes back in one of three states:

  none      no signals.json in the folder; the outline carries on without
  ok        the signals, numbered S1 to S5, and what is shown but never used
  refused   the file cannot be used; the reason says why, and nothing from it is

A file is refused whole, never trimmed or repaired: more than five signals, a
signal over one line, a signal with no source address, or anything that is not
the shape above. Picking which signals survive is the writer's call, not this
script's.

A signal is a note about the research. It is not the writer's decision and it
is not text for the piece. Nothing here writes.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

FILE = "signals.json"
CAP = 5


def _line(value, label, n):
    if not isinstance(value, str) or not value.strip():
        return f"signal {n} has no {label} line"
    if "\n" in value.strip():
        return f"signal {n}: {label} is more than one line"
    return None


def _is_address(value):
    if not isinstance(value, str):
        return False
    parts = urlparse(value)
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def _notes(items, keys):
    """Unresolved and held items: shown to the writer, never used. Anything unreadable is dropped from view, not guessed."""
    out = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict):
            out.append({k: " ".join(str(item.get(k, "")).split()) for k in keys})
    return out


def read(piece):
    """The piece's signals as a dict with a `state` of none, ok or refused."""
    path = Path(piece) / FILE
    if not path.is_file():
        return {"state": "none", "reason": f"no {FILE} in {Path(piece).name}"}

    def refused(reason):
        return {"state": "refused", "reason": reason}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return refused(f"{FILE} cannot be read: {type(e).__name__}")
    if not isinstance(data, dict) or not isinstance(data.get("signals"), list):
        return refused(f"{FILE} has no list of signals")
    if len(data["signals"]) > CAP:
        return refused(f"{FILE} has {len(data['signals'])} signals; the limit is {CAP}, and none are used")

    signals = []
    for n, s in enumerate(data["signals"], 1):
        if not isinstance(s, dict):
            return refused(f"signal {n} is not a signal")
        problem = _line(s.get("signal"), "signal", n) or _line(s.get("changes"), "what-it-changes", n)
        if problem:
            return refused(problem)
        sources = s.get("sources")
        if not isinstance(sources, list) or not sources:
            return refused(f"signal {n} has no source address")
        if not all(_is_address(u) for u in sources):
            return refused(f"signal {n} has a source that is not a web address")
        signals.append({"id": f"S{n}", "signal": " ".join(s["signal"].split()), "sources": sources,
                        "changes": " ".join(s["changes"].split())})
    return {"state": "ok", "lead": data.get("lead") if isinstance(data.get("lead"), str) else None,
            "distilled": data.get("distilled") if isinstance(data.get("distilled"), str) else None,
            "signals": signals, "unresolved": _notes(data.get("unresolved"), ("what", "reason")),
            "held": _notes(data.get("held"), ("url", "reason"))}


def render(result):
    if result["state"] != "ok":
        return f"Signals: {result['state']}. {result['reason']}."
    lines = [f"Signals: ok. {len(result['signals'])} of at most {CAP}"
             + (f", for {result['lead']}" if result["lead"] else "")
             + (f", from {result['distilled']}" if result["distilled"] else "") + "."]
    for s in result["signals"]:
        lines += [f"\n{s['id']}. {s['signal']}", *(f"    {u}" for u in s["sources"]), f"    Changes: {s['changes']}"]
    shown = [f"  unresolved: {u['what']} ({u['reason']})" for u in result["unresolved"]]
    shown += [f"  held back: {h['url']} ({h['reason']})" for h in result["held"]]
    if shown:
        lines += ["\nShown to the writer, never used:", *shown]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read a piece's research signals for the outline.")
    parser.add_argument("piece", type=Path, help="the piece folder")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = read(args.piece)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else render(result))
    return 1 if result["state"] == "refused" else 0


if __name__ == "__main__":
    sys.exit(main())
