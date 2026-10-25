"""Regression tests for CR-003 §1: the Claude Architect has an unrestricted shell."""

from __future__ import annotations

import re
from pathlib import Path

from tests.source_paths import agent_export_path, agent_source_path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_SOURCE_AGENT = agent_source_path("architect")
CLAUDE_SCAFFOLD_AGENT = agent_export_path("architect")
AGENT_TEMPLATE = REPO_ROOT / "guides" / "agent_template.md"

EXPECTED_ARCHITECT_TOOLS_LINE = "tools: Read, Write, Edit, Glob, Grep, Bash"
EXPECTED_CANONICAL_TOOLS = "`Read, Write, Edit, Glob, Grep, Bash`"

# A parenthesised pattern on Bash, for example `Bash(ai-team *)`.
RESTRICTED_BASH_PATTERN = re.compile(r"\bBash\s*\(")


def _tools_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("tools:")]


def test_source_architect_declares_unrestricted_bash_tools_line() -> None:
    """AC-1: the Claude Architect source has exactly one tools line with bare Bash."""
    tools_lines = _tools_lines(CLAUDE_SOURCE_AGENT.read_text(encoding="utf-8"))

    assert tools_lines == [EXPECTED_ARCHITECT_TOOLS_LINE]


def test_scaffold_architect_declares_unrestricted_bash_tools_line() -> None:
    """AC-1: the generated Claude Architect scaffold carries the same tools line."""
    tools_lines = _tools_lines(CLAUDE_SCAFFOLD_AGENT.read_text(encoding="utf-8"))

    assert tools_lines == [EXPECTED_ARCHITECT_TOOLS_LINE]


def test_architect_bash_tool_is_not_restricted_to_a_pattern() -> None:
    """AC-2: a tools line that restricts Bash with a parenthesised pattern is rejected."""
    for path in (CLAUDE_SOURCE_AGENT, CLAUDE_SCAFFOLD_AGENT):
        tools_lines = _tools_lines(path.read_text(encoding="utf-8"))

        assert len(tools_lines) == 1, f"expected one tools line in {path}"
        assert not RESTRICTED_BASH_PATTERN.search(tools_lines[0]), path


def _canonical_agents_rows(text: str) -> dict[str, str]:
    """Map each agent name in the Canonical Agents table to its Tools cell."""
    section = text.split("## Canonical Agents In This Repo", maxsplit=1)[1]
    section = section.split("\n## ", maxsplit=1)[0]
    rows: dict[str, str] = {}
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if (
            len(cells) >= 3
            and cells[0] not in ("Agent", "")
            and not set(cells[0]) <= {"-"}
        ):
            rows[cells[0]] = cells[2]
    return rows


def test_canonical_agents_table_lists_bash_for_planner_and_architect() -> None:
    """AC-3: the Planner and Architect rows of the Canonical Agents table include Bash."""
    rows = _canonical_agents_rows(AGENT_TEMPLATE.read_text(encoding="utf-8"))

    assert rows["Planner"] == EXPECTED_CANONICAL_TOOLS
    assert rows["Architect"] == EXPECTED_CANONICAL_TOOLS
