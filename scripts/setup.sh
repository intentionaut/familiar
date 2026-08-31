#!/bin/sh
# Run after cloning. Installs the /familiar-* commands for Claude Code and
# opencode so they work from any folder. Re-run any time; it overwrites.
set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
CC="$HOME/.claude/commands"
OC="$HOME/.config/opencode/command"
mkdir -p "$CC" "$OC"

for stage in case-study interview outline draft dev-edit line-edit social learn board reflect; do
  # The adapters carry a placeholder for the repo path; render it here so the
  # installed command knows where the prompts live.
  sed "s|{{FAMILIAR_HOME}}|$DIR|g" "$DIR/.claude/commands/$stage.md" > "$CC/familiar-$stage.md"
  sed "s|{{FAMILIAR_HOME}}|$DIR|g" "$DIR/.claude/commands/$stage.md" > "$OC/familiar-$stage.md"
done

# /reflect is muscle memory from Captain's Log, so keep the short alias.
# Remove first: an older install left this as a symlink, and redirecting into a
# symlink writes through to whatever it points at.
rm -f "$CC/reflect.md" "$OC/reflect.md"
sed "s|{{FAMILIAR_HOME}}|$DIR|g" "$DIR/.claude/commands/reflect.md" > "$CC/reflect.md"
sed "s|{{FAMILIAR_HOME}}|$DIR|g" "$DIR/.claude/commands/reflect.md" > "$OC/reflect.md"

echo "Installed /familiar-* commands for Claude Code and opencode."
echo "Familiar lives at: $DIR"
echo
echo "Next: fill in knowledge/positioning.md and knowledge/voice-guide.md,"
echo "then start with /familiar-interview <an idea>."
