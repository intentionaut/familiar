#!/bin/sh
# Run after cloning. Installs the /familiar-* commands for Claude Code and
# opencode so they work from any folder. Re-run any time; it overwrites.
set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
CC="$HOME/.claude/commands"
OC="$HOME/.config/opencode/command"
mkdir -p "$CC" "$OC"

# Resolve where the writer's knowledge actually lives and bake it into the
# installed commands, so a stage is told rather than left to guess. The
# fallback is this repo's own folder, which is the shipped templates, and the
# adapters say so when that is what they got. See scripts/paths.py.
KDIR="$(python3 "$DIR/scripts/paths.py" --knowledge-only 2>/dev/null || echo "$DIR/knowledge")"

# Every adapter in .claude/commands/ installs. Deliberately a glob and not a
# list: a hardcoded list silently skips any stage added later, which is how
# `repurpose` shipped without a command.
for adapter in "$DIR"/.claude/commands/*.md; do
  stage="$(basename "$adapter" .md)"
  # The adapters carry a placeholder for the repo path; render it here so the
  # installed command knows where the prompts live.
  sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" -e "s|{{FAMILIAR_KNOWLEDGE}}|$KDIR|g" "$adapter" > "$CC/familiar-$stage.md"
  sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" -e "s|{{FAMILIAR_KNOWLEDGE}}|$KDIR|g" "$adapter" > "$OC/familiar-$stage.md"
done

# /reflect is muscle memory from Captain's Log, so keep the short alias.
# Remove first: an older install left this as a symlink, and redirecting into a
# symlink writes through to whatever it points at.
rm -f "$CC/reflect.md" "$OC/reflect.md"
sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" -e "s|{{FAMILIAR_KNOWLEDGE}}|$KDIR|g" "$DIR/.claude/commands/reflect.md" > "$CC/reflect.md"
sed -e "s|{{FAMILIAR_HOME}}|$DIR|g" -e "s|{{FAMILIAR_KNOWLEDGE}}|$KDIR|g" "$DIR/.claude/commands/reflect.md" > "$OC/reflect.md"

echo "Installed /familiar-* commands for Claude Code and opencode."
echo
echo "Familiar stops after every stage and waits for you. It reports rather"
echo "than rewrites: your draft is never edited in place, and anything it"
echo "cannot source is left as a bracket instead of being invented."
echo
# Say what is actually configured and what to do next, rather than assuming.
python3 "$DIR/scripts/doctor.py" || true
