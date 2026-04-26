# ABOUTME: Security baseline profiles for managed-settings.json generation
# ABOUTME: Defines basic, moderate, and strict security profiles for Claude Code

"""Security baseline profiles for Claude Code managed-settings.json.

Hook scripts are stored as standalone files in assets/security/hooks/
for easy review and customization. The profiles reference them by path.
"""

# Deny rules for secrets and sensitive files
SECRETS_DENY_RULES = [
    "Read(.env)",
    "Read(.env.*)",
    "Read(~/.ssh/*)",
    "Read(~/.aws/credentials)",
    "Read(*.pem)",
    "Read(*.key)",
]

# Hook script paths (relative to deployment — admins set the absolute path)
# Default paths match the system managed-settings directory convention:
#   macOS:  /Library/Application Support/ClaudeCode/hooks/
#   Linux:  /etc/claude-code/hooks/
#   Windows: C:\Program Files\ClaudeCode\hooks\
HOOKS_DIR = "/etc/claude-code/hooks"


def _hook_path(script: str) -> str:
    """Return the default hook script path."""
    return f"{HOOKS_DIR}/{script}"


def build_security_profile(profile_name: str = "moderate", hooks_dir: str = None) -> dict:
    """Build a managed-settings.json security profile.

    Args:
        profile_name: One of "basic", "moderate", "strict".
        hooks_dir: Override the default hooks directory path.

    Returns:
        Dictionary suitable for writing as managed-settings.json.
    """
    global HOOKS_DIR
    if hooks_dir:
        HOOKS_DIR = hooks_dir

    if profile_name == "basic":
        return _build_basic()
    elif profile_name == "strict":
        return _build_strict()
    else:
        return _build_moderate()


def _build_basic() -> dict:
    """Minimal restrictions — disables bypass mode and blocks untrusted marketplaces."""
    return {
        "permissions": {
            "disableBypassPermissionsMode": "disable",
        },
        "strictKnownMarketplaces": [],
    }


def _build_moderate() -> dict:
    """Recommended baseline — adds auto mode restriction, secrets protection, and security hooks."""
    return {
        "permissions": {
            "disableBypassPermissionsMode": "disable",
            "disableAutoMode": "disable",
            "deny": list(SECRETS_DENY_RULES),
        },
        "allowManagedPermissionRulesOnly": True,
        "strictKnownMarketplaces": [],
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": _hook_path("block-destructive.sh"),
                        },
                        {
                            "type": "command",
                            "if": "Bash(git push *)",
                            "command": _hook_path("block-git-push.sh"),
                        },
                    ],
                }
            ],
        },
    }


def _build_strict() -> dict:
    """Maximum lockdown — adds managed-only hooks, sandbox, and audit logging."""
    return {
        "permissions": {
            "disableBypassPermissionsMode": "disable",
            "disableAutoMode": "disable",
            "deny": list(SECRETS_DENY_RULES),
        },
        "allowManagedPermissionRulesOnly": True,
        "allowManagedHooksOnly": True,
        "strictKnownMarketplaces": [],
        "sandbox": {
            "enabled": True,
            "autoAllowBashIfSandboxed": False,
            "allowUnsandboxedCommands": False,
            "network": {
                "allowedDomains": ["*.amazonaws.com"],
                "allowAllUnixSockets": False,
                "allowLocalBinding": False,
            },
        },
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": _hook_path("block-destructive.sh"),
                        },
                        {
                            "type": "command",
                            "if": "Bash(git push *)",
                            "command": _hook_path("block-git-push.sh"),
                        },
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": _hook_path("audit-log.sh"),
                        }
                    ],
                }
            ],
        },
    }
