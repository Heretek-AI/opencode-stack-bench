#!/usr/bin/env bash
# Print what opencode actually loads from an arm's config dir: config documents, agents,
# skills, plugins and MCP servers. Unknown config keys are dropped silently by opencode,
# so compare this output against what you meant to declare.
set -uo pipefail
arm_dir="$(cd "$1" && pwd)"
scratch="$(mktemp -d)"
export HOME="$scratch/home" XDG_CONFIG_HOME="$scratch/home/.config" XDG_DATA_HOME="$scratch/home/.local/share" \
  XDG_STATE_HOME="$scratch/home/.local/state" XDG_CACHE_HOME="$scratch/home/.cache" \
  OPENCODE_CONFIG_DIR="$arm_dir" OPENCODE_DISABLE_AUTOUPDATE=1 OPENCODE_DISABLE_CLAUDE_CODE=1
mkdir -p "$scratch/ws" && cd "$scratch/ws" && git init -q
export PWD="$scratch/ws"

opencode service start >/dev/null 2>&1 || true
# Agents and skills load asynchronously after the server starts; wait until they show up.
for _ in $(seq 1 30); do
  n=$(opencode api GET /api/agent 2>/dev/null | python3 -c "import json,sys; print(len(json.load(sys.stdin)['data']))" 2>/dev/null || echo 0)
  [ "${n:-0}" -gt 0 ] && break
  sleep 2
done

section() { echo; echo "::group::$1"; shift; "$@" 2>&1 | head -c 20000; echo; echo "::endgroup::"; }
section "Config sources (opencode debug config)" opencode debug config
section "Agents" sh -c 'opencode api GET /api/agent | python3 -c "import json,sys; [print(a[\"id\"], a.get(\"mode\"), \"-\", (a.get(\"description\") or \"\")[:80]) for a in json.load(sys.stdin)[\"data\"]]"'
section "Skills" sh -c 'opencode api GET /api/skill | python3 -c "import json,sys; [print(s[\"id\"], \"-\", (s.get(\"description\") or \"\")[:80]) for s in json.load(sys.stdin)[\"data\"]]"'
section "Plugins" opencode plugin list
section "MCP servers" opencode mcp list
opencode service stop >/dev/null 2>&1 || true
