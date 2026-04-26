# ABOUTME: Security baseline command for generating managed-settings.json
# ABOUTME: Generates security profiles (lax/moderate/strict) for Claude Code

"""Security command - Generate managed-settings.json security baseline."""

import json
from pathlib import Path

from cleo.commands.command import Command
from cleo.helpers import option
from rich.console import Console
from rich.panel import Panel

from claude_code_with_bedrock.cli.utils.security_profiles import build_security_profile


class SecurityGenerateCommand(Command):
    """
    Generate Claude Code managed-settings.json security baseline

    security generate
    """

    name = "security generate"
    description = "Generate managed-settings.json with a security baseline for Claude Code"

    options = [
        option(
            "profile",
            "p",
            description="Security profile: lax, moderate, strict (default: moderate)",
            flag=False,
            default="moderate",
        ),
        option(
            "output",
            "o",
            description="Output directory (default: dist/security/)",
            flag=False,
            default=None,
        ),
    ]

    def handle(self) -> int:
        """Execute the security generate command."""
        console = Console()

        profile_name = self.option("profile")
        valid_profiles = ["lax", "moderate", "strict"]
        if profile_name not in valid_profiles:
            console.print(f"[red]Invalid profile '{profile_name}'. Must be one of: {', '.join(valid_profiles)}[/red]")
            return 1

        output_dir_str = self.option("output")
        output_dir = Path(output_dir_str) if output_dir_str else Path("dist") / "security"
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print(
            Panel(
                f"[bold]Claude Code Security Baseline Generator[/bold]\n"
                f"Profile: {profile_name}",
                border_style="cyan",
            )
        )

        # Build the profile
        settings = build_security_profile(profile_name)

        # Write managed-settings.json
        settings_path = output_dir / "managed-settings.json"
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        console.print(f"[green]✓[/green] Generated {settings_path}")

        # Write platform-specific deployment instructions
        deploy_path = output_dir / "DEPLOY.md"
        with open(deploy_path, "w") as f:
            f.write(self._deployment_instructions(profile_name))
        console.print(f"[green]✓[/green] Generated {deploy_path}")

        # Summary
        console.print(f"\n[bold green]Security baseline generated in {output_dir}/[/bold green]")
        console.print(f"\n[bold]What's included ({profile_name} profile):[/bold]")

        checks = {
            "Disable bypassPermissions mode": True,
            "Disable auto mode": profile_name in ("moderate", "strict"),
            "Block third-party marketplaces": True,
            "Managed permission rules only": profile_name in ("moderate", "strict"),
            "Managed hooks only": profile_name == "strict",
            "Deny secrets file reads": profile_name in ("moderate", "strict"),
            "Block destructive commands (hook)": profile_name in ("moderate", "strict"),
            "Block git push to protected branches (hook)": profile_name in ("moderate", "strict"),
            "Audit logging (hook)": profile_name == "strict",
            "Bash sandbox with network restrictions": profile_name == "strict",
        }

        for check, enabled in checks.items():
            icon = "[green]✓[/green]" if enabled else "[dim]·[/dim]"
            console.print(f"  {icon} {check}")

        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Review managed-settings.json")
        console.print("  2. Deploy to system directory or via MDM (see DEPLOY.md)")
        console.print("  3. Verify with /status in Claude Code")
        console.print(
            "\n[dim]Docs: https://code.claude.com/docs/en/settings#settings-files[/dim]"
        )

        return 0

    def _deployment_instructions(self, profile_name: str) -> str:
        """Generate platform-specific deployment instructions."""
        return f"""# Deploying managed-settings.json ({profile_name} profile)

## macOS

```bash
sudo mkdir -p "/Library/Application Support/ClaudeCode"
sudo cp managed-settings.json "/Library/Application Support/ClaudeCode/"
```

Or deploy via Jamf/Kandji using the `com.anthropic.claudecode` preference domain.

## Linux / WSL

```bash
sudo mkdir -p /etc/claude-code
sudo cp managed-settings.json /etc/claude-code/
```

## Windows

```powershell
New-Item -ItemType Directory -Force -Path "C:\\Program Files\\ClaudeCode"
Copy-Item managed-settings.json "C:\\Program Files\\ClaudeCode\\"
```

Or deploy via Intune/Group Policy. See [Anthropic MDM templates](https://github.com/anthropics/claude-code/tree/main/examples/mdm).

## Verification

Run `/status` in Claude Code. You should see:

```
Setting sources:
  Enterprise managed settings (file)
```
"""
