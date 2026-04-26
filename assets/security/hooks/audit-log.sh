#!/bin/bash
# Hook: Audit log all Bash commands (PostToolUse)
#
# Dual-write: local file + OTEL collector (if configured).
# Local file ensures audit trail even when collector is unavailable.
# OTEL forwarding is best-effort, non-blocking (background curl).
#
# Usage in managed-settings.json:
#   "PostToolUse": [{
#     "matcher": "Bash",
#     "hooks": [{
#       "type": "command",
#       "command": "/etc/claude-code/hooks/audit-log.sh"
#     }]
#   }]

set -euo pipefail

AUDIT_LOG="${HOME}/.claude/audit.log"
mkdir -p "$(dirname "$AUDIT_LOG")"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMAND=$(jq -r '.tool_input.command // "unknown"')
EXIT_CODE=$(jq -r '.tool_output.exit_code // "n/a"')

# 1. Local file (always)
echo "[$TIMESTAMP] command=\"$COMMAND\" exit_code=$EXIT_CODE" >> "$AUDIT_LOG"

# 2. OTEL collector (best-effort, non-blocking)
OTEL_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-}"
if [ -n "$OTEL_ENDPOINT" ]; then
    EPOCH_NS=$(date -u +%s)000000000
    curl -sf --max-time 2 \
        -X POST "${OTEL_ENDPOINT}/v1/logs" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
            --arg ts "$EPOCH_NS" \
            --arg cmd "$COMMAND" \
            --arg ec "$EXIT_CODE" \
            '{
                resourceLogs: [{
                    resource: {},
                    scopeLogs: [{
                        scope: {name: "claude-code-audit"},
                        logRecords: [{
                            timeUnixNano: $ts,
                            body: {stringValue: ("command=" + $cmd + " exit_code=" + $ec)},
                            attributes: [
                                {key: "audit.command", value: {stringValue: $cmd}},
                                {key: "audit.exit_code", value: {stringValue: $ec}},
                                {key: "audit.source", value: {stringValue: "security-hook"}}
                            ]
                        }]
                    }]
                }]
            }')" &>/dev/null &
fi
