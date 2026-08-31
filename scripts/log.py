#!/usr/bin/env python3
"""See which projects are keeping a build log, and wire up the ones that are not.

A tool that only sees what you registered will keep seeing the two projects you
remembered to wire up. So this scans instead: every project, whether it has a
build log, whether the hooks are installed, and when it last shipped. The most
useful line it prints is the gap.

Usage:
  scripts/log.py                     every project, and which are covered
  scripts/log.py add <project>       install the hooks and record the project
  scripts/log.py add <project> --file NAME   when the log is not the default name

Reads `knowledge/build-logs.md` for the projects root and the watched list.
Nothing is written to a project except its `.claude/settings.json`, and that is
merged rather than replaced.
"""
import json, os, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "build-log-entry.sh"
LOG_PATTERNS = ("*-LOG.md", "*-PROGRESS.md", "LOG.md")


def settings_path():
    """The registry, in the vault if Familiar is installed into one."""
    vault = pathlib.Path.home() / "Documents/Dex/06-Resources/Familiar/knowledge/build-logs.md"
    return vault if vault.exists() else ROOT / "knowledge" / "build-logs.md"


def read_settings():
    p = settings_path()
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    m = re.search(r"^- Projects live in:\s*(.+?)\s*$", text, re.M)
    root = (m.group(1) if m else "~/Projects").strip()
    if root.startswith("["):
        root = "~/Projects"
    watched = {}
    for line in text.splitlines():
        m = re.match(r"\s*-\s+`([^`]+)`\s*:\s*`([^`]+)`", line)
        if m:
            watched[str(pathlib.Path(m.group(1)).expanduser().resolve())] = m.group(2)
    return pathlib.Path(root).expanduser(), watched, p


def find_log(folder, watched):
    named = watched.get(str(folder.resolve()))
    if named and (folder / named).exists():
        return named
    for pat in LOG_PATTERNS:
        hits = sorted(folder.glob(pat))
        if hits:
            return hits[0].name
    return None


def hooks_wired(folder):
    s = folder / ".claude" / "settings.json"
    try:
        data = json.loads(s.read_text(encoding="utf-8"))
    except Exception:
        return False
    blob = json.dumps(data.get("hooks", {}))
    return "build-log-entry.sh" in blob or "captains-log-entry.sh" in blob


def last_commit(folder):
    try:
        out = subprocess.run(["git", "-C", str(folder), "log", "-1", "--format=%ct"],
                             capture_output=True, text=True, timeout=10)
        return int(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None
    except Exception:
        return None


def ago(ts):
    if ts is None:
        return "no commits"
    d = time.time() - ts
    if d < 86400:
        return "today"
    if d < 86400 * 14:
        return f"{int(d // 86400)}d ago"
    if d < 86400 * 70:
        return f"{int(d // 604800)}w ago"
    return f"{int(d // 2592000)}mo ago"


def reflections_folder():
    """Where reflections live, so the scan does not offer to log them."""
    for p in (ROOT / "knowledge" / "reflection.md",
              pathlib.Path.home() / "Documents/Dex/06-Resources/Familiar/knowledge/reflection.md"):
        try:
            m = re.search(r"^- Reflections live in:\s*(.+?)\s*$", p.read_text(encoding="utf-8"), re.M)
        except OSError:
            continue
        if m and not m.group(1).startswith("["):
            return pathlib.Path(m.group(1)).expanduser().resolve()
    return None


def scan(root, watched):
    out = []
    if not root.is_dir():
        sys.exit(f"No such folder: {root}. Set it in {settings_path()}")
    skip = {ROOT.resolve()}
    refl = reflections_folder()
    if refl:
        skip.add(refl)
    for folder in sorted(root.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if folder.resolve() in skip:
            continue
        out.append({
            "name": folder.name, "folder": folder,
            "log": find_log(folder, watched),
            "wired": hooks_wired(folder),
            "commit": last_commit(folder),
        })
    return out


def cmd_list():
    root, watched, reg = read_settings()
    projects = scan(root, watched)
    if not projects:
        sys.exit(f"No projects under {root}")

    print(f"\n  {'PROJECT':<26} {'BUILD LOG':<24} {'HOOKS':<8} LAST SHIPPED")
    for p in projects:
        log = p["log"] or "none"
        hooks = "on" if p["wired"] else ("" if p["log"] else "")
        print(f"  {p['name']:<26} {log:<24} {hooks:<8} {ago(p['commit'])}")

    week = time.time() - 86400 * 7
    gap = [p for p in projects if not p["log"] and p["commit"] and p["commit"] > week]
    covered = sum(1 for p in projects if p["log"])
    print(f"\n  {covered} of {len(projects)} projects keep a build log.")
    if gap:
        names = ", ".join(p["name"] for p in gap)
        print(f"  {len(gap)} shipped this week without one: {names}")
        print(f"\n  Start one:  familiar log add {gap[0]['name']}")
    print()


def cmd_add(args):
    root, watched, reg = read_settings()
    if not args:
        sys.exit("usage: log.py add <project> [--file NAME]")
    target = args[0]
    name = None
    if "--file" in args:
        name = args[args.index("--file") + 1]

    folder = pathlib.Path(target).expanduser()
    if not folder.is_dir():
        folder = root / target
    if not folder.is_dir():
        sys.exit(f"No such project: {target}")
    folder = folder.resolve()

    if not name:
        name = find_log(folder, watched)
    if not name:
        name = f"{folder.name.upper().replace('-', '_')}-LOG.md"
        print(f"  No build log found. Using {name}.")
        print(f"  Paste the block from {ROOT / 'prompts' / 'log.md'} into that")
        print(f"  project's CLAUDE.md so entries get written during the work too.")
    if not (folder / name).exists():
        (folder / name).write_text(
            f"# {folder.name} build log\n\nKept per Familiar's prompts/log.md.\n"
            "Append-only, dated, newest at the bottom.\n\n---\n", encoding="utf-8")
        print(f"  Created {folder / name}")

    # Merge into the project's settings, never replace.
    sp = folder / ".claude" / "settings.json"
    sp.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
    except Exception:
        sys.exit(f"{sp} is not valid JSON. Fix it, then run this again.")
    hooks = data.setdefault("hooks", {})
    entry = {"type": "command", "command": str(HOOK), "timeout": 60}
    added = 0
    for event in ("PreCompact", "SessionEnd"):
        groups = hooks.setdefault(event, [])
        for g in groups:
            g["hooks"] = [h for h in g.get("hooks", [])
                          if "build-log-entry.sh" not in h.get("command", "")
                          and "captains-log-entry.sh" not in h.get("command", "")]
        groups[:] = [g for g in groups if g.get("hooks")]
        groups.append({"hooks": [entry]})
        added += 1
    sp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # Record it, so the hook can find a log called anything.
    text = reg.read_text(encoding="utf-8")
    line = f"- `{folder}`: `{name}`"
    if line not in text:
        marker = "<!-- familiar log add appends below this line -->"
        text = (text.replace(marker, marker + "\n\n" + line) if marker in text
                else text.rstrip() + "\n\n" + line + "\n")
        reg.write_text(text, encoding="utf-8")

    print(f"  Wired {folder.name}: {added} hooks, log is {name}")
    print(f"  Recorded in {reg}")


def main():
    args = sys.argv[1:]
    if args and args[0] == "add":
        return cmd_add(args[1:])
    if args and args[0] not in ("list", ""):
        sys.exit(__doc__)
    cmd_list()


if __name__ == "__main__":
    main()
