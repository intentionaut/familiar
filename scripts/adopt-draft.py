#!/usr/bin/env python3
"""Adopt a revised draft over a piece's draft.md, only after a verified backup.

    python3 scripts/adopt-draft.py <piece folder> <revised draft>

The writer's yes at dev-edit or line-edit runs this; nothing else replaces draft.md. In order:
1. copy draft.md to .versions/draft-before-r<N>.md, N the next free round; an existing backup is never overwritten;
2. read the backup back and check its sha256 equals draft.md's;
3. only then replace draft.md with the revised file, atomically (temp file, then os.replace).
Any failure exits non-zero and leaves draft.md as it was.
"""
import hashlib
import os
import sys
import tempfile
from pathlib import Path


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write_new(path, data):
    """Create path with data; refuse if it exists (O_EXCL), so a backup is never clobbered."""
    with open(path, "xb") as f:
        f.write(data)


def adopt(piece, revised):
    piece, revised = Path(piece), Path(revised)
    draft = piece / "draft.md"
    if not draft.is_file():
        raise SystemExit(f"adopt-draft: no draft.md in {piece}")
    if not revised.is_file():
        raise SystemExit(f"adopt-draft: no revised draft at {revised}")
    old, new = draft.read_bytes(), revised.read_bytes()
    edits = piece / ".versions"          # the piece's kept-versions store (board_edit.VERSIONS)
    edits.mkdir(parents=True, exist_ok=True)
    n = 1
    while (edits / f"draft-before-r{n}.md").exists():
        n += 1
    backup = edits / f"draft-before-r{n}.md"
    try:
        write_new(backup, old)
    except FileExistsError:
        raise SystemExit(f"adopt-draft: {backup} already exists; nothing changed")
    if sha(backup.read_bytes()) != sha(old):
        raise SystemExit(f"adopt-draft: backup {backup} does not match draft.md; draft.md unchanged")
    fd, tmp = tempfile.mkstemp(dir=piece, prefix=".draft-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(new)
        os.replace(tmp, draft)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return backup


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    try:
        backup = adopt(*argv)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    except OSError as e:
        print(f"adopt-draft: {e}; draft.md unchanged", file=sys.stderr)
        return 1
    print(f"draft.md replaced; previous version kept at {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
