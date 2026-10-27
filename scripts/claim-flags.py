#!/usr/bin/env python3
"""Show a piece's open claim flags before it is finalised.

    python3 scripts/claim-flags.py pieces/2026-01-01-slug          # for a person to read
    python3 scripts/claim-flags.py pieces/2026-01-01-slug --json   # the same, for a stage to read

A research tool may leave a `flags.md` in the piece folder: claims in the draft
that need a source, one entry each, and the writer's Keep or Drop on each one,
appended underneath. The shape it reads:

    ## F-001
    - claim: "the exact words from the draft"
    - reason: why it was flagged
    - route: search | ask the writer
    ...
    ## Decisions
    - F-001: kept (2026-01-01)
    - F-002: dropped (2026-01-01)
    - F-001: swept in 2026-01-02-preview (2026-01-02)

The newest Keep or Drop on a flag stands. A flag with none is still to decide.

The file comes back in one of three states:

  none      no flags.md in the folder; nothing to show
  ok        every flag, with the open ones listed: still to decide, and kept but not yet sourced
  refused   the file cannot be read, or an entry or decision does not fit the shape; the reason says
            which, and nothing from it is shown, because a half-read list would look like a short one

A flag is a question about the draft, never a verdict on it. This script shows
them and changes nothing: it writes no file, and it never blocks a stage.
"""
import argparse
import json
import re
import sys
from pathlib import Path

FILE = "flags.md"
ENTRY = re.compile(r"^## (F-\d{3,})\n((?:- .*\n?)*)", re.M)
DECISION = re.compile(r"^- (F-\d{3,}): (kept|dropped|swept in \S+) \((\d{4}-\d{2}-\d{2})\)$")


def read(piece):
    """The piece's claim flags as a dict with a `state` of none, ok or refused."""
    path = Path(piece) / FILE
    if not path.is_file():
        return {"state": "none", "reason": f"no {FILE} in {Path(piece).name}"}

    def refused(reason):
        return {"state": "refused", "reason": reason}

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return refused(f"{FILE} cannot be read: {type(e).__name__}")

    flags = {}
    for m in ENTRY.finditer(text):
        fields = dict(line[2:].split(": ", 1) for line in m[2].splitlines() if ": " in line)
        claim = fields.get("claim", "").strip().strip('"')
        if not claim:
            return refused(f"{m[1]} has no claim")
        if m[1] in flags:
            return refused(f"{m[1]} appears twice")
        flags[m[1]] = {"id": m[1], "claim": claim, "reason": fields.get("reason", "").strip(),
                       "route": fields.get("route", "").strip(), "status": "to decide", "swept": []}
    headed = len(re.findall(r"^## F-", text, re.M))
    if headed != len(flags):
        return refused(f"{headed - len(flags)} flag heading(s) that are not in the shape `## F-001`")

    decisions = text.split("\n## Decisions\n", 1)[1] if "\n## Decisions\n" in text else ""
    for line in decisions.splitlines():
        if not line.strip():
            continue
        m = DECISION.match(line.strip())
        if not m:
            return refused(f"a decision line does not fit the shape: {line.strip()[:80]}")
        if m[1] not in flags:
            return refused(f"a decision names {m[1]}, which is not in {FILE}")
        if m[2].startswith("swept in "):
            flags[m[1]]["swept"].append(m[2].removeprefix("swept in "))
        else:
            flags[m[1]]["status"] = m[2]

    every = list(flags.values())
    return {"state": "ok", "total": len(every),
            "to_decide": [f for f in every if f["status"] == "to decide"],
            "kept": [f for f in every if f["status"] == "kept"],
            "dropped": sum(f["status"] == "dropped" for f in every)}


def render(result):
    if result["state"] != "ok":
        return f"Claim flags: {result['state']}. {result['reason']}."
    open_ = len(result["to_decide"]) + len(result["kept"])
    lines = [f"Claim flags: ok. {open_} open of {result['total']}"
             + (f"; {result['dropped']} dropped" if result["dropped"] else "") + "."]
    if result["to_decide"]:
        lines.append("\nStill to decide, keep or drop:")
        lines += [f"  {f['id']}  \"{f['claim']}\"" + (f"  ({f['reason']})" if f["reason"] else "")
                  for f in result["to_decide"]]
    if result["kept"]:
        lines.append("\nKept, needs a source in the piece:")
        lines += [f"  {f['id']}  \"{f['claim']}\"" + (f"  (searched in {', '.join(f['swept'])})" if f["swept"] else "")
                  for f in result["kept"]]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Show a piece's open claim flags.")
    parser.add_argument("piece", type=Path, help="the piece folder")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = read(args.piece)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else render(result))
    return 1 if result["state"] == "refused" else 0


if __name__ == "__main__":
    sys.exit(main())
