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
FAMILIAR_ROOT="$(dirname "$(dirname "$SCRIPT")")"
export FAMILIAR_ROOT
STATE_DIR="${HOME}/.claude/familiar-log"
mkdir -p "$STATE_DIR/state" "$STATE_DIR/logs"

if [ "${FAMILIAR_LOG_SYNC:-0}" != "1" ] && [ "${FAMILIAR_LOG_CHILD:-0}" != "1" ]; then
  # Hand off. SessionEnd hooks get at most 60s; a model call can take longer.
  printf '%s' "$INPUT" | FAMILIAR_LOG_CHILD=1 nohup "$SCRIPT" \
    >>"$STATE_DIR/logs/hook.log" 2>&1 &
  disown 2>/dev/null || true
  exit 0
fi

printf '%s' "$INPUT" | python3 "$FAMILIAR_ROOT/scripts/build_log_entry.py"
