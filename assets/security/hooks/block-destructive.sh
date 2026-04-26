#!/bin/bash
# Hook: Block destructive Bash commands (PreToolUse)
#
# Blocks rm -rf, chmod 777, mkfs, and other dangerous patterns.
# Returns a deny decision with a reason that Claude can see.
#
# Usage in managed-settings.json:
#   "PreToolUse": [{
#     "matcher": "Bash",
#     "hooks": [{
#       "type": "command",
#       "command": "/etc/claude-code/hooks/block-destructive.sh"
#     }]
#   }]

set -euo pipefail

COMMAND=$(jq -r '.tool_input.command // ""')

# Patterns that indicate destructive intent
BLOCKED_PATTERNS=(
    'rm -rf /'
    'rm -rf ~'
    'rm -rf \.'
    'chmod 777'
    'chmod -R 777'
    'mkfs\.'
    ':(){:|:&};:'       # fork bomb
    'dd if=/dev/zero'
    'dd if=/dev/random'
    '> /dev/sda'
    'shutdown'
    'reboot'
    'init 0'
    'init 6'
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$pattern"; then
        jq -n \
            --arg reason "Blocked by security policy: command matches destructive pattern '$pattern'" \
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

# Allow the command
exit 0
