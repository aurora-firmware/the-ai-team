"""usage.md examples use only commands the CLI provides (cross-checked against commands.md)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
USAGE_MD = REPO_ROOT / "cli" / "docs" / "usage.md"
COMMANDS_MD = REPO_ROOT / "cli" / "docs" / "commands.md"


def _commands_in_usage_examples() -> set[str]:
    """Return ``ai-team <command> [<subcommand>]`` for each example command line."""
    commands = set()
    content = USAGE_MD.read_text(encoding="utf-8")
    for block in re.findall(r"```bash\n(.*?)```", content, re.S):
        for line in block.splitlines():
            match = re.match(r"ai-team ([a-z][a-z-]*)(?: ([a-z][a-z-]*))?", line)
            if match:
                commands.add(" ".join(part for part in match.groups() if part))
    return commands


def test_usage_md_example_commands_exist_in_commands_md():
    """Every command in a usage.md example must have a commands.md entry."""
    commands_content = COMMANDS_MD.read_text(encoding="utf-8")
    commands = _commands_in_usage_examples()
    assert commands, "usage.md examples must name at least one command"
    for command in sorted(commands):
        group = command.split()[0]
        # A group with subcommands needs the exact entry; a bare command's second
        # word is a positional argument, so its group entry is enough.
        has_subcommands = f"`ai-team {group} " in commands_content
        expected = command if has_subcommands else group
        assert f"`ai-team {expected}`" in commands_content, (
            f"'ai-team {command}' is used in usage.md but missing from commands.md"
        )
