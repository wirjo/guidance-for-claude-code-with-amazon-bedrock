#!/bin/bash
# Hook: Block git push to protected branches (PreToolUse)
#
# Prevents accidental or malicious pushes to main, master, production.
# Returns a deny decision if the push target is a protected branch.
#
# Usage in managed-settings.json:
#   "PreToolUse": [{
#     "matcher": "Bash",
#     "hooks": [{
#       "type": "command",
#       "if": "Bash(git push *)",
#       "command": "/etc/claude-code/hooks/block-git-push.sh"
#     }]
#   }]

set -euo pipefail

COMMAND=$(jq -r '.tool_input.command // ""')

PROTECTED_BRANCHES=(
    "main"
    "master"
    "production"
    "release"
)

for branch in "${PROTECTED_BRANCHES[@]}"; do
    if echo "$COMMAND" | grep -qE "git push.*\b${branch}\b"; then
        jq -n \
            --arg reason "Blocked by security policy: git push to protected branch '$branch' requires manual approval outside Claude Code" \
            '{
                hookSpecificOutput: {
                    hookEventName: "PreToolUse",
                    permissionDecision: "deny",
                    permissionDecisionReason: $reason
                }
            }'
        exit 0
    fi
done

# Allow non-protected branch pushes
exit 0
