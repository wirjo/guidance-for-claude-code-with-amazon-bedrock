# Security Baseline for Claude Code

This guide provides a security baseline for enterprise Claude Code deployments using `managed-settings.json`. Managed settings sit at the highest precedence level — users cannot override them.

## Overview

Claude Code supports [managed settings](https://code.claude.com/docs/en/settings#settings-files) deployed to system directories:

| Platform | Path |
|----------|------|
| macOS | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| Linux/WSL | `/etc/claude-code/managed-settings.json` |
| Windows | `C:\Program Files\ClaudeCode\managed-settings.json` |

Deploy via MDM (Jamf, Intune, Group Policy) or generate with `ccwb security generate`. See the [Anthropic MDM templates](https://github.com/anthropics/claude-code/tree/main/examples/mdm) for platform-specific examples.

## Risk Framework

| Risk | Severity | Mitigation | Profile |
|------|----------|------------|---------|
| Unrestricted shell access via `bypassPermissions` | Critical | `permissions.disableBypassPermissionsMode` | All |
| Auto mode approves unsafe actions | High | `permissions.disableAutoMode` | Moderate+ |
| Untrusted plugin execution | High | `strictKnownMarketplaces` | All |
| User-defined permission overrides | Medium | `allowManagedPermissionRulesOnly` | Moderate+ |
| Secrets exposure (.env, SSH keys, AWS creds) | High | `permissions.deny` rules | Moderate+ |
| Destructive commands (rm -rf, chmod 777) | High | PreToolUse hook: `block-destructive.sh` | Moderate+ |
| Accidental push to protected branches | Medium | PreToolUse hook: `block-git-push.sh` | Moderate+ |
| User-defined hook injection | Medium | `allowManagedHooksOnly` | Strict |
| No audit trail of Claude actions | Medium | PostToolUse hook: `audit-log.sh` | Strict |
| Unrestricted network/filesystem from Bash | Medium | `sandbox` configuration | Strict |

## Quick Start

```bash
poetry run ccwb security generate                     # moderate (default)
poetry run ccwb security generate --profile strict    # maximum lockdown
poetry run ccwb security generate --profile basic     # minimal restrictions
```

Output: `dist/security/managed-settings.json` + `DEPLOY.md`

## Profile Comparison

| Setting | Basic | Moderate | Strict |
|---------|:-----:|:--------:|:------:|
| Disable `bypassPermissions` | ✅ | ✅ | ✅ |
| Disable `auto` mode | | ✅ | ✅ |
| Block third-party marketplaces | ✅ | ✅ | ✅ |
| Managed permission rules only | | ✅ | ✅ |
| Managed hooks only | | | ✅ |
| Deny secrets file reads | | ✅ | ✅ |
| Destructive command hook | | ✅ | ✅ |
| Git push guard hook | | ✅ | ✅ |
| Audit logging hook | | | ✅ |
| Bash sandbox + network restrictions | | | ✅ |

## Security Hooks

Hook scripts are in [`assets/security/hooks/`](../../assets/security/hooks/) for easy review. Deploy them alongside `managed-settings.json` to the system hooks directory.

### block-destructive.sh

**Event:** PreToolUse (Bash)
**Risk:** Claude executes `rm -rf /`, `chmod 777`, `mkfs`, fork bombs, or other destructive patterns.

Reads the command from stdin JSON, checks against a list of dangerous patterns, and returns a deny decision if matched. See the [script](../../assets/security/hooks/block-destructive.sh) for the full pattern list.

### block-git-push.sh

**Event:** PreToolUse (Bash), filtered by `if: "Bash(git push *)"` 
**Risk:** Claude pushes to main, master, production, or release branches.

Only runs when the command matches `git push *`. Checks whether the target is a protected branch and denies if so. See the [script](../../assets/security/hooks/block-git-push.sh).

### audit-log.sh

**Event:** PostToolUse (Bash)
**Risk:** No visibility into what Claude executes during a session.

Logs every Bash command with timestamp and exit code to `~/.claude/audit.log`. See the [script](../../assets/security/hooks/audit-log.sh).

### Adding custom hooks

Create a script that reads JSON from stdin and optionally outputs a decision. Place it in the hooks directory and reference it in `managed-settings.json`. See the [Anthropic hooks guide](https://code.claude.com/docs/en/hooks-guide) and [bash_command_validator_example.py](https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py) for patterns.

## Sandbox (Strict Profile)

The strict profile enables Claude Code's built-in Bash sandbox with network restrictions:

```json
"sandbox": {
  "enabled": true,
  "autoAllowBashIfSandboxed": false,
  "allowUnsandboxedCommands": false,
  "network": {
    "allowedDomains": ["*.amazonaws.com"],
    "allowAllUnixSockets": false,
    "allowLocalBinding": false
  }
}
```

**Note:** The sandbox only applies to the Bash tool. Other tools (Read, Write, WebFetch, MCPs) and hooks are not sandboxed.

The `allowedDomains` includes `*.amazonaws.com` for Bedrock API access. Add additional domains for internal registries, MCP servers, or other services your developers need.

## Deployment

See `dist/security/DEPLOY.md` (generated by `ccwb security generate`) for platform-specific instructions, or deploy via your MDM tool using [Anthropic's templates](https://github.com/anthropics/claude-code/tree/main/examples/mdm).

After deployment, verify with `/status` in Claude Code — you should see `Enterprise managed settings (file)` in the settings sources.

## References

- [Claude Code Settings](https://code.claude.com/docs/en/settings)
- [Claude Code Permissions](https://code.claude.com/docs/en/permissions)
- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Anthropic MDM Templates](https://github.com/anthropics/claude-code/tree/main/examples/mdm)
- [Anthropic Settings Examples](https://github.com/anthropics/claude-code/tree/main/examples/settings)
