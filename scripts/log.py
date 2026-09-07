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
    """The registry, wherever this install's knowledge resolves to.

    This used to name one machine's vault path outright, which meant the
    registry was read from that folder whatever a writer had configured, and on
    any other machine the path did not exist and the shipped templates answered
    instead: an empty list, reported as an empty list. `paths.py` is the one
    place that knows where a house is, and every reader of it goes through here.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from paths import knowledge_dir
    kdir, _whose = knowledge_dir()
    return (kdir / "build-logs.md") if kdir else ROOT / "knowledge" / "build-logs.md"


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

# The answer to the one-time ask, and the token inside it.
LOGS_SETTING = "Build logs live in"
PROJECT_TOKEN = "{project}"


def read_log_home(text=None):
    """Where this writer keeps build logs. Asked once, then never again.

    Before this, `log add` put the log at the project root and the writer found
    out it was the wrong place by having a commit refused, or worse by not
    having it refused -- a build log carries defect notes and plan of record,
    and a public repository is the one place it must not be. The remedy was a
    second command, `log move`, which you only knew to run after the mistake.

    So the location is a setting, not a default: asked the first time a log is
    added, written into the Settings block beside the others, and read from
    there forever after. One question, once, instead of a correction every time.

    Returns None when it has never been answered, which is the signal to ask.
    """
    if text is None:
        p = settings_path()
        text = p.read_text(encoding="utf-8") if p.exists() else ""
    m = re.search(rf"^- {LOGS_SETTING}:\s*(.+?)\s*$", text, re.M)
    if not m:
        return None
    value = m.group(1).strip()
    # A template placeholder is not an answer.
    if not value or value.startswith("[") or value.lower() == "none":
        return None
    return value


def log_destination(folder, name, home):
    """The recorded value for a project, given the writer's answer.

    `in the project` keeps the historical behaviour: a bare filename, which
    resolve_log reads as being inside the project. Anything else is a folder,
    optionally with {project} in it, and the recorded value is a full path --
    which resolve_log already understands, because that is what `log move`
    has always written.
    """
    if home is None or home.strip().lower() == "in the project":
        return name
    slot = (home.replace("{Project}", folder.name.replace("-", " ").title().replace(" ", ""))
                .replace(PROJECT_TOKEN, folder.name))
    return str(pathlib.Path(slot) / name)



def wire_instructions(folder, project):
    """Put the log block in the project's own instructions.

    `log add` used to print "paste this into CLAUDE.md" and leave. Skipping it
    is easy and the cost is invisible: the hooks still fire at session end, so a
    log appears and looks fine, while the entries written DURING the work --
    the ones holding the reasoning, which is the whole point -- never happen.

    A command that already edits .claude/settings.json in this project is not
    made more intrusive by also writing the instructions that make the thing it
    just installed useful. Idempotent: it looks for the heading before adding.
    """
    block = (ROOT / "prompts" / "log.md").read_text(encoding="utf-8")
    try:
        body = block.split("```")[1].strip().replace("<PROJECT>", project)
    except IndexError:
        return None
    for candidate in ("CLAUDE.md", "AGENTS.md"):
        f = folder / candidate
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        if "Keep a build log for this project" in text:
            return None
        f.write_text(text.rstrip("\n") + "\n\n## The build log\n\n" + body + "\n",
                     encoding="utf-8")
        return f
    return None


def hide_local_settings(folder):
    """Keep .claude/settings.json out of git, without touching the repo.

    The hook is recorded as an absolute path on this machine, so the file is
    machine-specific by construction and committing it hands a teammate a path
    that does not exist. .git/info/exclude rather than .gitignore: it is local,
    it needs no commit, and it does not modify a tracked file that somebody
    else on the project owns.

    Silent when there is no .git -- not every project is a repository, and that
    is not a problem to report.
    """
    info = folder / ".git" / "info"
    if not (folder / ".git").is_dir():
        return None
    info.mkdir(parents=True, exist_ok=True)
    f = info / "exclude"
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    line = ".claude/settings.json"
    if line in text.split():
        return None
    f.write_text(text.rstrip("\n") + f"\n{line}\n", encoding="utf-8")
    return f


def ask_log_home(stream=None):
    """Ask once where build logs go, write the answer, never ask again.

    ONE QUESTION, and it is asked at the only moment the writer has the context
    to answer it: they have just said they want a log for a project. Asking at
    install time would be asking about a thing they have not met.

    THE COPY LEADS WITH THE PROMISE, not the risk. Familiar's promise is that it
    learns from what you are building and brings you topics; a build log is the
    input to that. harvest reads the watched list to find them and case-study
    turns one log into a brief and a set of interview questions. So the first
    thing this says is what the writer gets, and the location is the clause
    after it.

    The first draft of this said "records what broke and what it cost", three
    lines of risk before any reason to want one. That is the mechanism sold as
    the outcome, and it makes a setup question read like a warning.

    The order of the options is still the recommendation, because a log holds
    candid defect notes and plan of record and a repository other people read
    is the one place those must not be.

    NON-INTERACTIVE RUNS DO NOT HANG AND DO NOT GUESS SILENTLY. With no
    terminal -- a hook, CI, a script -- this takes the recommended option and
    says so, because the alternative is a command that blocks forever in a
    context where nobody can type.
    """
    out = stream or sys.stdout
    default = "~/Documents/{Project}"
    print("\n  Where should build logs live?\n", file=out)
    print("  Familiar reads these to bring you topics: what you built, what you", file=out)
    print("  decided, what broke. They hold candid notes and plan of record, so a", file=out)
    print("  folder of your own keeps them out of a repository others read.\n", file=out)
    print(f"  1. A folder of your own   {default}", file=out)
    print("  2. In the project         <PROJECT>-LOG.md at its root\n", file=out)

    if not sys.stdin.isatty():
        print(f"  No terminal, so: 1, {default}. Change it in the Settings", file=out)
        print("  block of knowledge/build-logs.md.\n", file=out)
        answer = default
    else:
        try:
            reply = input(f"  1, 2, or a path [{default}]: ").strip()
        except EOFError:
            reply = ""
        if reply == "2" or reply.lower() == "in the project":
            answer = "in the project"
        elif reply in ("", "1"):
            answer = default
        else:
            answer = reply

    write_log_home(answer)
    return answer


def write_log_home(answer):
    """Record the answer in the Settings block, beside the others."""
    p = settings_path()
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    line = f"- {LOGS_SETTING}: {answer}"
    if re.search(rf"^- {LOGS_SETTING}:", text, re.M):
        text = re.sub(rf"^- {LOGS_SETTING}:.*$", line, text, count=1, flags=re.M)
    elif re.search(r"^- Projects live in:.*$", text, re.M):
        text = re.sub(r"^(- Projects live in:.*)$", r"\1\n" + line, text,
                      count=1, flags=re.M)
    else:
        text = text.rstrip() + "\n\n## Settings\n\n" + line + "\n"
    p.write_text(text, encoding="utf-8")
    return p


def resolve_log(folder, recorded):
    """Where a project's log actually is.

    A recorded value with no separator in it is a filename inside the project,
    which is the normal case and the whole history of this file. A value with a
    separator, or one starting with ~, is a path used as it stands, so a log can
    live outside the project it describes.

    That matters for a public repository. A build log holds candid defect notes,
    hours budgets and plan-of-record, and keeping it beside the code means
    either committing all of that or gitignoring a file whose only copy is then
    on one disk. Neither is a good answer, so the third one is to let the log
    live in the writer's own folder and record where it went.
    """
    if not recorded:
        return None
    if "/" in recorded or recorded.startswith("~"):
        return pathlib.Path(recorded).expanduser()
    return folder / recorded


def project_folder(target, root):
    """The project a command was pointed at, by name or by path.

    `add`, `move` and `--path` all take the same argument and all have to read
    it the same way. They did not: the first two fell back to the projects root
    when the argument was not a directory, and `--path` resolved it against the
    current directory and stopped. So `log.py --path intentionaut` answered
    nothing from anywhere except the projects root, while `log.py add
    intentionaut` worked from everywhere - and the failure was silent, because
    `--path` is called by a hook that must stay quiet in an unregistered repo.

    Returns None when the target names no project. Saying which of "not a
    project" and "no log" happened is the caller's business, because the hook
    wants silence and a person wants a reason.
    """
    folder = pathlib.Path(target).expanduser()
    if not folder.is_dir():
        folder = root / target
    return folder.resolve() if folder.is_dir() else None


def find_log(folder, watched):
    """The recorded value for this project, or a guess from the folder."""
    named = watched.get(str(folder.resolve()))
    if named and resolve_log(folder, named).exists():
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
    # Only Familiar's own hook counts as coverage. Captain's Log's hook was
    # accepted here during the migration, which meant the one project still
    # running the retired tool was the one reported as covered. `log add` still
    # strips it when rewiring, so an old install upgrades cleanly.
    return "build-log-entry.sh" in blob


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

    folder = project_folder(target, root)
    if folder is None:
        sys.exit(f"No such project: {target}")

    if not name:
        name = find_log(folder, watched)
    fresh = not name
    if not name:
        name = f"{folder.name.upper().replace('-', '_')}-LOG.md"
        print(f"  No build log found. Using {name}.")

    # THE ONE-TIME ASK. Only for a log this command is about to create, and
    # only when it has never been answered. A project that already has a log
    # keeps it where it is: `log add` is being asked to wire hooks, not to move
    # somebody's file out from under them.
    if fresh and "/" not in name and not name.startswith("~"):
        home = read_log_home()
        if home is None:
            home = ask_log_home()
        name = log_destination(folder, name, home)

    dest = resolve_log(folder, name)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            f"# {folder.name} build log\n\nKept per Familiar's prompts/log.md.\n"
            "Append-only, dated, newest at the bottom.\n\n---\n", encoding="utf-8")
        print(f"  Created {dest}")

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

    wired = wire_instructions(folder, folder.name)
    hidden = hide_local_settings(folder)

    print(f"  Wired {folder.name}: {added} hooks, log is {name}")
    print(f"  Recorded in {reg}")
    if wired:
        print(f"  Log block added to {wired.name}, so entries get written "
              f"during the work")
    if hidden:
        print("  .claude/settings.json excluded locally: it holds this "
              "machine's hook path")


def cmd_move(args):
    """Move a project's log out of the project, and record where it went."""
    if len(args) < 2:
        sys.exit("usage: log.py move <project> <destination folder or file>")
    root, watched, reg = read_settings()
    target, dest = args[0], pathlib.Path(args[1]).expanduser()

    folder = project_folder(target, root)
    if folder is None:
        sys.exit(f"No such project: {target}")

    name = watched.get(str(folder)) or find_log(folder, watched)
    if not name:
        sys.exit(f"No log recorded or found for {folder.name}.")
    src = resolve_log(folder, name)
    if not src.exists():
        sys.exit(f"{src} does not exist.")

    if dest.is_dir() or not dest.suffix:
        dest = dest / src.name
    if dest.resolve() == src.resolve():
        sys.exit("That is where it already lives.")
    if dest.exists():
        sys.exit(f"{dest} already exists. Move it out of the way first.")

    dest.parent.mkdir(parents=True, exist_ok=True)
    src.replace(dest)

    home = str(pathlib.Path.home())
    recorded = str(dest)
    if recorded.startswith(home + "/"):
        recorded = "~" + recorded[len(home):]
    text = reg.read_text(encoding="utf-8")
    old_line = f"- `{folder}`: `{name}`"
    new_line = f"- `{folder}`: `{recorded}`"
    if old_line in text:
        reg.write_text(text.replace(old_line, new_line, 1), encoding="utf-8")
    else:
        marker = "<!-- familiar log add appends below this line -->"
        text = (text.replace(marker, marker + "\n\n" + new_line) if marker in text
                else text.rstrip() + "\n\n" + new_line + "\n")
        reg.write_text(text, encoding="utf-8")

    print(f"  Moved to {dest}")
    print(f"  Recorded in {reg}")
    print("  The hooks are unchanged: they read the registry, so they follow it.")
    if (folder / ".gitignore").exists():
        print(f"  Worth checking {folder.name}/.gitignore: the entry that hid the")
        print("  log is now hiding nothing.")


def cmd_path(args):
    """Print where a project's log is. One resolver, for the hook to call."""
    root, watched, _reg = read_settings()
    folder = project_folder(args[0] if args else ".", root)
    if folder is None:
        return 1
    name = watched.get(str(folder)) or find_log(folder, watched)
    if not name:
        return 1
    path = resolve_log(folder, name)
    if not path.exists():
        return 1
    print(path)
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == "add":
        return cmd_add(args[1:])
    if args and args[0] == "move":
        return cmd_move(args[1:])
    if args and args[0] == "--path":
        return cmd_path(args[1:])
    if args and args[0] not in ("list", ""):
        sys.exit(__doc__)
    cmd_list()


if __name__ == "__main__":
    # The return value is the exit code. Dropping it made every run exit 0,
    # including a `--path` that found nothing - so the session-end hook's
    # `returncode == 0` guard was always true and only its stdout check did any
    # work. The guard says what it means now.
    sys.exit(main())
