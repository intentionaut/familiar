#!/usr/bin/env python3
"""What each project digest observed, in the digest's own words.

    python3 scripts/digest-observations.py                  # every digest in <knowledge>/digests/
    python3 scripts/digest-observations.py <dir | file>...  # those instead
    python3 scripts/digest-observations.py --json           # the same, for another tool to read

A digest is one project's git history, written by `scripts/project-digest.py`,
and it runs to the length of that history. `harvest` compares observations
across projects, and for that it needs each digest's `## Observations` and two
counts, not every commit of every project in front of it at once.

So this prints, per digest: the project, the span, each observation exactly as
the digest has it, with its dates and commit ids, and how many commits carried
reasoning and how many were corrections. Nothing is reworded, ranked, merged or
interpreted. Comparing across projects is harvest's job, and the why is the
writer's.

Each digest comes back in one of two states:

  read         its observations and counts, as written
  unreadable   the file could not be read, or is not a project digest; the
               reason says which

A count is null when the digest has no section to count from. Null is not zero:
a digest that lists no corrections says 0, and a digest with no corrections
section says nothing about them.

Exit 0 when every digest was read, including when there are none. Exit 2 when
at least one was unreadable. Say so, and never report that project as having
nothing in it.

Nothing here writes, and nothing here runs another program.
"""
import argparse
import json
import re
import sys
from pathlib import Path

OBSERVATIONS = "Observations"
REASONING = "Commits that carried reasoning"
CORRECTIONS = "Corrections the messages admit to"

TITLE = re.compile(r"^# (.+): what the history says\s*$")
SPAN = re.compile(r"(\d+) commits?, (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})")
# One commit, as project-digest.py lists it in the two counted sections. The
# "None" line each section carries when it is empty does not match, so an empty
# section counts 0 without a second rule.
COMMIT = re.compile(r"^- \d{4}-\d{2}-\d{2} `[0-9a-f]{7,}` ")
NO_OBSERVATIONS = "- None yet."


def _sections(lines):
    """(lines before the first `## ` heading, {heading: its lines})."""
    head, secs, cur = [], {}, None
    for line in lines:
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            cur = m.group(1)
            secs.setdefault(cur, [])
        elif cur is None:
            head.append(line)
        else:
            secs[cur].append(line)
    return head, secs


def _count(secs, name):
    if name not in secs:
        return None
    return sum(1 for line in secs[name] if COMMIT.match(line))


def read_digest(path):
    """One digest's observations and counts, or why it could not be read."""
    path = Path(path)
    out = {"digest": path.name, "project": None, "state": "unreadable", "reason": None,
           "commits": None, "first": None, "last": None, "observations": None,
           "commits_carrying_reasoning": None, "corrections": None}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        out["reason"] = "no such file"
        return out
    except (OSError, UnicodeDecodeError) as e:
        out["reason"] = f"could not be read ({type(e).__name__})"
        return out

    title = TITLE.match(lines[0]) if lines else None
    head, secs = _sections(lines)
    if not title:
        out["reason"] = "not a project digest: no title line"
        return out
    if OBSERVATIONS not in secs:
        out["reason"] = "not a project digest: no `## Observations` section"
        return out

    span = SPAN.search("\n".join(head))
    if span:
        out["commits"], out["first"], out["last"] = int(span.group(1)), span.group(2), span.group(3)
    out["project"] = title.group(1)
    out["observations"] = [line[2:] for line in secs[OBSERVATIONS]
                           if line.startswith("- ") and not line.startswith(NO_OBSERVATIONS)]
    out["commits_carrying_reasoning"] = _count(secs, REASONING)
    out["corrections"] = _count(secs, CORRECTIONS)
    out["state"] = "read"
    return out


def default_dir():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from paths import knowledge_dir
    return Path(knowledge_dir(None)[0]) / "digests"


def gather(targets):
    """Every digest the targets name, in name order. A folder gives its `.md` files."""
    out = []
    for t in targets:
        t = Path(t).expanduser()
        if t.is_dir():
            out += [read_digest(p) for p in sorted(t.glob("*.md"))]
        else:
            out.append(read_digest(t))
    return out


def _n(value, word):
    return f"{word} not stated" if value is None else f"{value} {word}"


def render(digests, where):
    plural = "" if len(digests) == 1 else "s"
    lines = [f"{len(digests)} digest{plural}" + (f" in {where}" if where else ""), ""]
    for d in digests:
        if d["state"] != "read":
            lines += [f"{d['digest']}: UNREADABLE, {d['reason']}. Not the same as nothing observed.", ""]
            continue
        span = (f"{d['commits']} commits, {d['first']} to {d['last']}" if d["commits"] is not None
                else "span not stated")
        lines.append(f"{d['project']} ({d['digest']})")
        lines.append(f"  {span}. {_n(d['commits_carrying_reasoning'], 'carried reasoning')}. "
                     f"{_n(d['corrections'], 'corrections')}.")
        if d["observations"]:
            lines += [f"  - {o}" for o in d["observations"]]
        else:
            lines.append("  No observations: the history is too short or too even for one.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*", help="digest files or folders (default: <knowledge>/digests/)")
    ap.add_argument("--json", action="store_true", help="for another tool to read")
    args = ap.parse_args()

    where = None
    if args.targets:
        digests = gather(args.targets)
    else:
        where = default_dir()
        digests = gather([where]) if where.is_dir() else []

    gaps = [d for d in digests if d["state"] != "read"]
    if args.json:
        print(json.dumps({"dir": str(where) if where else None,
                          "state": "gaps" if gaps else "ok",
                          "digests": digests}, indent=2))
    elif where is not None and not where.is_dir():
        print(f"No digests folder at {where}. `familiar engage --all` writes one digest per project, after a yes.")
    else:
        sys.stdout.write(render(digests, where))
    return 2 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
