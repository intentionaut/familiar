#!/usr/bin/env python3
"""Where Familiar's knowledge and pieces actually live.

The tool ships a `knowledge/` folder of templates. A writer's filled-in copies
are usually somewhere else: a vault, a private repo, a synced folder. Nothing
used to connect the two, so every stage read the templates, found blanks, and
either stopped or fell back to defaults. That is not a missing file, it is a
missing address, and it looks like a bad edit rather than a broken setup.

Resolution order, highest first. The first one that exists wins:

  knowledge   FAMILIAR_KNOWLEDGE, then FAMILIAR_CONFIG (the older name, still
              honoured), then `knowledge = ` in a `.familiar` file, then
              ./knowledge, then ~/.familiar/knowledge, then the shipped
              templates.
  pieces      FAMILIAR_PIECES, then `pieces = ` in `.familiar`, then
              <home>/pieces. Accepts several, separated by a path separator.

`.familiar` sits next to this repo or in the current folder. It is per-install,
so it is not committed. Format is deliberately dull:

    knowledge = ~/Documents/vault/Familiar/knowledge
    pieces = ~/Documents/vault/Writing
    pieces = ~/Projects/familiar/pieces

Run it to see what resolves:  python3 scripts/paths.py
"""
import os
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
SHIPPED = (HOME / "knowledge").resolve()


def _config_file():
    for base in (Path.cwd(), HOME):
        f = base / ".familiar"
        if f.is_file():
            return f
    return None


def read_config():
    """Parse `.familiar` into {key: [values]}. Blank lines and # are ignored."""
    out = {}
    f = _config_file()
    if not f:
        return out
    for line in f.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = (p.strip() for p in line.split("=", 1))
        if v:
            out.setdefault(k.lower(), []).append(os.path.expanduser(v))
    return out


def knowledge_dir(explicit=None):
    """Return (path, whose). `whose` is "yours" or "the shipped templates"."""
    cfg = read_config().get("knowledge", [])
    candidates = [explicit,
                  os.environ.get("FAMILIAR_KNOWLEDGE"),
                  os.environ.get("FAMILIAR_CONFIG")]
    candidates += cfg
    candidates += ["./knowledge", os.path.expanduser("~/.familiar/knowledge")]
    for c in candidates:
        if c and (Path(c).expanduser() / "positioning.md").is_file():
            found = Path(c).expanduser().resolve()
            return found, ("the shipped templates" if found == SHIPPED else "yours")
    return SHIPPED, "the shipped templates"


def pieces_dirs(explicit=None):
    """Every folder holding piece folders, in order. Always at least one."""
    if explicit:
        return [Path(p).expanduser().resolve() for p in explicit]
    env = os.environ.get("FAMILIAR_PIECES")
    raw = []
    if env:
        raw += [p for p in env.split(os.pathsep) if p]
    raw += read_config().get("pieces", [])
    if not raw:
        raw = [str(HOME / "pieces")]
    seen, out = set(), []
    for p in raw:
        r = Path(p).expanduser().resolve()
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


if __name__ == "__main__":
    import sys as _sys
    k, whose = knowledge_dir()
    if "--knowledge-only" in _sys.argv:
        print(k)
        raise SystemExit(0)
    f = _config_file()
    print(f"config file : {f if f else 'none, using defaults'}")
    print(f"knowledge   : {k}  ({whose})")
    for i, p in enumerate(pieces_dirs()):
        print(f"pieces      : {p}" if i == 0 else f"            : {p}")
