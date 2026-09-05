#!/bin/sh
# Run after cloning. Installs the /familiar-* commands for supported agents
# so they work from any folder. Re-run any time; it overwrites.
#
# Supported agents:
#   Claude Code      ~/.claude/commands/
#   opencode         ~/.config/opencode/command/
#   Codex (OpenAI)   ~/.codex/commands/
#   Gemini CLI       ~/.gemini/commands/
#
# Only agents you already have are installed for. An agent is taken to be
# present when its own config folder exists; a folder Familiar has never seen
# belongs to a tool you do not run, and creating one there would be putting
# files in a place you did not ask for.
#
# Pass --only <agent> to install for just one, or --all to install everywhere
# whether or not the folder is there yet:
#   scripts/setup.sh --only claude
#   scripts/setup.sh --all
set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
ONLY=""
ALL=""
for arg in "$@"; do
  case "$arg" in
    --only) shift ;;
    --all) ALL="yes" ;;
    claude|opencode|codex|gemini) ONLY="$arg" ;;
  esac
done

# The folder that says the agent is installed. Not the command folder itself:
# that one is missing for people who do run the agent and have never added a
# command, so testing it would skip exactly the writers this is meant to serve.
home_for() {
  case "$1" in
    claude)   echo "$HOME/.claude" ;;
    opencode) echo "$HOME/.config/opencode" ;;
    codex)    echo "$HOME/.codex" ;;
    gemini)   echo "$HOME/.gemini" ;;
  esac
}

skipped=""

# Install unless this agent is absent from the machine. Naming it explicitly
# (--only codex) is taken as "install it anyway": the writer knows something
# the filesystem does not.
wanted() {
  agent="$1"
  [ "$ONLY" = "$agent" ] && return 0
  [ -n "$ONLY" ] && return 1
  [ -n "$ALL" ] && return 0
  if [ -d "$(home_for "$agent")" ]; then
    return 0
  fi
  skipped="$skipped $agent"
  return 1
}

# The adapters resolve the knowledge folder at runtime rather than having it
# baked in here. Baking it meant an install done from one folder kept pointing
# at that folder forever: move a vault, or run the installer from a temporary
# directory once, and every command afterwards read a house that was not there.
# Nothing is silent about it either way, because paths.py says whose files it
# found. See scripts/paths.py.

# The three ways into a piece.
COMMANDS="board new-piece harvest"
# reflect is not a way into a piece; it is a standing practice with its own
# scheduled nudge, and it installs unprefixed as /reflect. A nudge that names a
# command the writer does not have is worse than no nudge at all.
ALIAS="reflect"

install_for() {
  local label="$1" dir="$2"
  mkdir -p "$dir"
  for cmd in $COMMANDS; do
    adapter="$DIR/.claude/commands/$cmd.md"
    if [ -f "$adapter" ]; then
      sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" "$adapter" > "$dir/familiar-$cmd.md"
    fi
  done

  # The standing practice, installed unprefixed.
  alias_adapter="$DIR/.claude/commands/$ALIAS.md"
  if [ -f "$alias_adapter" ]; then
    sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" "$alias_adapter" > "$dir/$ALIAS.md"
  fi

  # Take out commands an earlier version installed that are no longer part of
  # Familiar. A left-behind command is worse than a missing one: it still
  # appears in the agent's list and calls a prompt that is not there any more.
  # Only files this installer wrote are touched.
  removed=""
  for f in "$dir"/familiar-*.md; do
    [ -f "$f" ] || continue
    stem="$(basename "$f" .md)"
    stem="${stem#familiar-}"
    keep=0
    for cmd in $COMMANDS; do
      if [ "$stem" = "$cmd" ]; then keep=1; fi
    done
    if [ "$keep" = "0" ]; then
      rm -f "$f"
      removed="$removed $stem"
    fi
  done

  if [ -n "$removed" ]; then
    echo "  $label: $dir"
    echo "    took out:$removed"
  else
    echo "  $label: $dir"
  fi
}

installed=""

if wanted claude; then
  install_for "Claude Code" "$HOME/.claude/commands"
  installed="$installed claude"
fi

if wanted opencode; then
  install_for "opencode" "$HOME/.config/opencode/command"
  installed="$installed opencode"
fi

if wanted codex; then
  install_for "Codex" "$HOME/.codex/commands"
  installed="$installed codex"
fi

if wanted gemini; then
  install_for "Gemini CLI" "$HOME/.gemini/commands"
  installed="$installed gemini"
fi

echo
if [ -z "$installed" ]; then
  echo "No agent found to install for."
  echo "Looked for Claude Code, opencode, Codex and Gemini CLI and found none of"
  echo "their folders. If you have one anyway, name it:"
  echo "  scripts/setup.sh --only claude"
else
  echo "Installed /familiar-board, /familiar-new-piece, /familiar-harvest and /reflect for:$installed"
fi
if [ -n "$skipped" ]; then
  echo "Left alone, not installed on this machine:$skipped"
  echo "  Add one later with:  scripts/setup.sh --only <agent>"
fi
echo
echo "Three ways in: start a piece, pick one back up, or find something to"
echo "write about. Everything after that is a conversation. Tell the agent"
echo "what you have and it picks the right stage."
echo
echo "Two loops feed it. 'familiar log add <project>' writes what shipped as a"
echo "Claude Code session ends (other agents: 'familiar log entry' by hand)."
echo "'familiar reflect' asks two questions and keeps your words; it is off"
echo "until knowledge/reflection.md turns it on."
echo
# Say what is actually configured and what to do next, rather than assuming.
python3 "$DIR/scripts/doctor.py" || true
