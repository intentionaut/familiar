#!/usr/bin/env bash
# Familiar: an automatic build-log entry from the session transcript.
#
# Wired as a Claude Code PreCompact and SessionEnd hook by `familiar log add`.
# Reads the hook JSON on stdin, finds the project's build log, and appends an
# entry generated from the part of the transcript not yet recorded. Runs in the
# background so it never blocks compaction or exit.
#
# The entry format is prompts/log.md. An entry written here is reconstructed
# from a transcript, so it is marked (auto): it gets Shipped and Numbers
# reliably, Decisions when they were said out loud, and reasoning only if it is
# in the transcript. The in-the-moment questions are what capture the why.
#
# Env overrides:
#   FAMILIAR_LOG_FILE   path to the log. Otherwise the filename recorded for
#                       this project in knowledge/build-logs.md, otherwise the
#                       first *-LOG.md, *-PROGRESS.md or LOG.md in the folder.
#   FAMILIAR_LOG_MODEL  model for the summariser (default: sonnet)
#   FAMILIAR_LOG_EFFORT effort level (default: medium)
#   FAMILIAR_LOG_SYNC=1 run in the foreground (for testing)

set -u
INPUT="$(cat)"
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
STATE_DIR="${HOME}/.claude/familiar-log"
mkdir -p "$STATE_DIR/state" "$STATE_DIR/logs"

if [ "${FAMILIAR_LOG_SYNC:-0}" != "1" ] && [ "${FAMILIAR_LOG_CHILD:-0}" != "1" ]; then
  # Hand off. SessionEnd hooks get at most 60s; a model call can take longer.
  printf '%s' "$INPUT" | FAMILIAR_LOG_CHILD=1 nohup "$SCRIPT" \
    >>"$STATE_DIR/logs/hook.log" 2>&1 &
  disown 2>/dev/null || true
  exit 0
fi

python3 - "$INPUT" <<'PY'
import json, os, re, sys, subprocess, glob, datetime, fcntl

hook = json.loads(sys.argv[1])
cwd = hook.get("cwd") or os.getcwd()
transcript = hook.get("transcript_path", "")
session = hook.get("session_id", "unknown")
event = hook.get("hook_event_name", "")
state_dir = os.path.expanduser("~/.claude/familiar-log/state")
now = datetime.datetime.now()

def log(msg):
    print(f"[{now:%Y-%m-%d %H:%M:%S}] {session[:8]} {event}: {msg}", flush=True)

# --- find the log file -------------------------------------------------------
log_file = os.environ.get("FAMILIAR_LOG_FILE")
if not log_file:
    # Prefer the filename recorded for this project, so a log called anything
    # at all is found. Guessing is the fallback, not the rule.
    for base in (os.path.expanduser("~/Projects/familiar/knowledge/build-logs.md"),
                 os.path.expanduser("~/Documents/Dex/06-Resources/Familiar/knowledge/build-logs.md")):
        try:
            with open(base, encoding="utf-8") as fh:
                for line in fh:
                    m = re.match(r"\s*-\s+`([^`]+)`\s*:\s*`([^`]+)`", line)
                    if m and os.path.realpath(os.path.expanduser(m.group(1))) == os.path.realpath(cwd):
                        cand = os.path.join(cwd, m.group(2))
                        if os.path.exists(cand):
                            log_file = cand
                        break
        except OSError:
            pass
        if log_file:
            break
if not log_file:
    for pat in ("*-LOG.md", "*-PROGRESS.md", "LOG.md"):
        hits = sorted(glob.glob(os.path.join(cwd, pat)))
        if hits:
            log_file = hits[0]; break
if not log_file or not os.path.exists(log_file):
    log("no build log in project, skipping"); sys.exit(0)
if not transcript or not os.path.exists(transcript):
    log("no transcript, skipping"); sys.exit(0)

# --- read the unprocessed part of the transcript ----------------------------
offset_file = os.path.join(state_dir, f"{session}.offset")
try:
    start = int(open(offset_file).read().strip())
except Exception:
    start = 0

lines = open(transcript, encoding="utf-8", errors="replace").read().splitlines()
new = lines[start:]
if not new:
    log("nothing new since last entry"); sys.exit(0)

def text_of(content):
    if isinstance(content, str):
        return content
    out = []
    for block in content or []:
        if not isinstance(block, dict):
            continue
        t = block.get("type")
        if t == "text":
            out.append(block.get("text", ""))
        elif t == "tool_use":
            name = block.get("name", "")
            inp = block.get("input", {}) or {}
            hint = inp.get("command") or inp.get("file_path") or inp.get("description") or ""
            out.append(f"[tool: {name} {str(hint)[:160]}]")
        elif t == "tool_result":
            c = block.get("content")
            s = c if isinstance(c, str) else " ".join(b.get("text", "") for b in (c or []) if isinstance(b, dict))
            if block.get("is_error"):
                out.append(f"[tool error: {s[:400]}]")
            elif s:
                out.append(f"[tool result: {s[:200]}]")
    return "\n".join(x for x in out if x)

turns = []
for raw in new:
    try:
        rec = json.loads(raw)
    except Exception:
        continue
    if rec.get("isMeta") or rec.get("type") not in ("user", "assistant"):
        continue
    msg = rec.get("message", {}) or {}
    body = text_of(msg.get("content")).strip()
    if not body or body.startswith("<system-reminder>") or body.startswith("<local-command"):
        continue
    turns.append(f"### {rec['type'].upper()}\n{body}")

convo = "\n\n".join(turns)
if len(convo.strip()) < 400:
    log(f"too little conversation to record ({len(convo)} chars)"); sys.exit(0)
LIMIT = 120_000
if len(convo) > LIMIT:
    convo = "[...earlier part of session truncated...]\n\n" + convo[-LIMIT:]

# --- last entry, for continuity ---------------------------------------------
existing = open(log_file, encoding="utf-8").read()
tail = existing[-4000:]

kind = "compacted, auto" if event == "PreCompact" else "auto"
heading = f"## {now:%Y-%m-%d} ({kind})"

prompt = f"""You are keeping a build log for a software project. Below is the raw transcript
of one Claude Code working session (or the part of it since the last entry),
followed by the end of the existing log. Write the next log entry.

RULES (these matter more than anything else)
- Record, don't dramatise. Facts, numbers, and what things cost in time or rework.
  No adjectives about the project's trajectory, no praise, no narrative headings.
- Prefer numbers to intensifiers. "Took 3 attempts" beats "was tricky".
- Include the agent's own mistakes and dead ends in Went wrong, with the cause
  and the cost. This is the section most worth reading later.
- Never invent a detail. If the transcript doesn't have it, leave it out.
- Plain language. No "leveraged", "streamlined", "robust". No em dashes.
- Do not repeat anything already recorded in the existing log tail.
- This entry is reconstructed from a transcript by a hook, not written during the
  work. It records what happened; the reasoning is only as good as what was said
  out loud. Do not pad reasoning you can't see.

FORMAT: output exactly this, starting with the heading line, no preamble, no
code fences, no closing remarks. Omit any section with nothing real in it.

{heading}

**Shipped**
- One line each. What now exists that didn't before.

**Decisions**
- What was decided, what was rejected, and the reason (only if the reason was given).

**Went wrong**
- Wrong turns, bugs, wasted work. Cause and cost.

**Numbers**
- Anything measurable mentioned in the session.

**Open**
- Unresolved questions, known risks, things waiting on the human.

If genuinely nothing worth recording happened, output only the single word
NOTHING.

=== EXISTING LOG (tail) ===
{tail}

=== TRANSCRIPT ===
{convo}
"""

model = os.environ.get("FAMILIAR_LOG_MODEL", "sonnet")
effort = os.environ.get("FAMILIAR_LOG_EFFORT", "medium")
try:
    res = subprocess.run(
        # --setting-sources "" loads no settings, so no hooks: the summariser
        # can't trigger this hook again. (--bare would do that too but it also
        # skips the stored login.)
        ["claude", "-p", "--no-session-persistence", "--setting-sources", "",
         "--model", model, "--effort", effort, "--tools", ""],
        input=prompt, capture_output=True, text=True, timeout=600,
        cwd=os.path.expanduser("~"),
        env={**os.environ, "CLAUDE_CODE_ENABLE_AWAY_SUMMARY": "0"},
    )
except Exception as e:
    log(f"claude call failed: {e}"); sys.exit(0)
if res.returncode != 0:
    log(f"claude exit {res.returncode}: {res.stderr.strip()[:300]}"); sys.exit(0)

entry = res.stdout.strip()
if not entry or entry.upper().startswith("NOTHING"):
    log("model judged nothing worth recording")
    open(offset_file, "w").write(str(len(lines)))
    sys.exit(0)
if not entry.startswith("## "):
    entry = heading + "\n\n" + entry

# --- append, under a lock so two sessions don't interleave --------------------
with open(log_file, "a+", encoding="utf-8") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    f.seek(0, 2)
    if f.tell() and not existing.endswith("\n"):
        f.write("\n")
    f.write("\n" + entry.rstrip() + "\n")
    fcntl.flock(f, fcntl.LOCK_UN)
open(offset_file, "w").write(str(len(lines)))
log(f"appended {len(entry)} chars to {log_file}")
PY
