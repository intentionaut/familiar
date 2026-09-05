#!/usr/bin/env bash
# Familiar: the weekly check-in, offered at the start of a session.
#
# Wired as a SessionStart hook automatically when the plugin is enabled
# (hooks/hooks.json), or by `familiar checkin on` for the skills-only
# install, which has no plugin lifecycle to auto-wire it.
#
# Reads the hook JSON on stdin and hands off to scripts/checkin.py, which
# decides whether today's session earns an offer per knowledge/checkin.md
# and, if so, returns additionalContext for the model to phrase the offer
# in — this script never talks to the writer directly.
#
# SessionStart fires in every session, on every project, once the plugin is
# enabled at the user level — most of them have nothing to do with Familiar.
# Anything that goes wrong here must fail silently: exit 0, no output, no
# trace in a session this was never meant to touch.

set -u
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
FAMILIAR_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$SCRIPT")")}"

python3 "$FAMILIAR_ROOT/scripts/checkin.py" hook 2>/dev/null
exit 0
