#!/usr/bin/env bash
set -Eeuo pipefail

TARGET="${1:-http://127.0.0.1:5010/login}"
echo "== Flooding $TARGET =="

# Write a real Lua script to a temp file
LUA_FILE="$(mktemp -t wrk_post.XXXXXX.lua)"
cat > "$LUA_FILE" <<'LUA'
-- Force POST on every request (no chance of GET fallback)
local body = '{"email":"bot@example.com","pw":"x"}'
local headers = {
  ["Content-Type"]    = "application/json",
  ["X-Forwarded-For"] = "119.74.224.147",
  ["X-Real-IP"]       = "119.74.224.147",
}
request = function()
  return wrk.format("POST", nil, headers, body)
end
LUA

echo "Lua script saved to: $LUA_FILE"
wc -c "$LUA_FILE"  # sanity: non-zero size

# Run wrk with the Lua file
wrk -t4 -c200 -d20s -s "$LUA_FILE" "$TARGET"
