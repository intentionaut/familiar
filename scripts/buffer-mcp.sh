#!/usr/bin/env bash
# Buffer scheduler adapter. Execs Buffer's hosted MCP server over stdio so a
# client without a Buffer MCP configured can still reach it.
#
# Needs BUFFER_API_KEY in the environment. Get a token from Buffer, then:
#   export BUFFER_API_KEY="..."      (in your shell profile)
#
# Used by prompts/publish.md. Nothing here is specific to one writer: the
# channel ids live in knowledge/social-schedule.md, and the key never does.
set -euo pipefail

if [[ -z "${BUFFER_API_KEY:-}" ]]; then
  cat >&2 <<'MSG'
BUFFER_API_KEY is not set.

Familiar does not need a scheduler. Either export the key:

  export BUFFER_API_KEY="your-token"

or set `scheduler: none` in knowledge/social-schedule.md and publish will
print a paste-ready table instead.
MSG
  exit 1
fi

exec npx --yes mcp-remote https://mcp.buffer.com/mcp \
  --header "Authorization: Bearer ${BUFFER_API_KEY}"
