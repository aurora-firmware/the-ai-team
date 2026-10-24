"""Tests for the init adoption case: no .ai-team.toml, some files already exist."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

OCCUPIED = "occupied\n"


def _occupy(target: Path, *relative_paths: str) -> list[Path]:
    paths = []
    for relative in relative_paths:
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(OCCUPIED, encoding="utf-8")
        paths.append(path)
    return paths


def _init(args: list[str], input_text: str | None = None):
    from ai_team.cli import app

    return CliRunner().invoke(app, ["init", *args], input=input_text)


def _base_args(target: Path) -> list[str]:
    return [str(target), "--tools", "claude"]


def test_asks_once_listing_every_existing_file_and_overwrites_on_yes(tmp_path):
    existing = _occupy(tmp_path, "ai-team/specs/.gitkeep", ".claude/agents/planner.md")

    result = _init(_base_args(tmp_path), input_text="y\nn\nn\n")

    assert result.exit_code == 0
    assert result.output.count("Overwrite") == 1
    for path in existing:
        assert str(path) in result.output
        assert path.read_text(encoding="utf-8") != OCCUPIED
    assert (tmp_path / ".ai-team.toml").is_file()


def test_keeps_existing_files_when_the_question_is_answered_no(tmp_path):
    existing = _occupy(tmp_path, "ai-team/specs/.gitkeep", ".claude/agents/planner.md")

    result = _init(_base_args(tmp_path), input_text="n\nn\nn\n")

    assert result.exit_code == 0
    for path in existing:
        assert path.read_text(encoding="utf-8") == OCCUPIED
    assert (tmp_path / ".claude" / "agents" / "architect.md").is_file()
    assert (tmp_path / ".ai-team.toml").is_file()


def test_does_not_ask_about_coding_guidelines_or_root_guidance(tmp_path):
    guidelines, root_claude = _occupy(
        tmp_path, "ai-team/docs/coding_guidelines.md", "CLAUDE.md"
    )

    result = _init([*_base_args(tmp_path), "--no-interactive"])

    assert result.exit_code == 0
    assert "Overwrite" not in result.output
    assert str(guidelines) not in result.stderr
    assert str(root_claude) not in result.stderr
    assert guidelines.read_text(encoding="utf-8") == OCCUPIED
    assert root_claude.read_text(encoding="utf-8") == OCCUPIED


def test_force_overwrites_existing_files_without_asking(tmp_path):
    existing = _occupy(tmp_path, "ai-team/specs/.gitkeep", ".claude/agents/planner.md")

    result = _init([*_base_args(tmp_path), "--force", "--no-interactive"])

    assert result.exit_code == 0
    assert "Overwrite" not in result.output
    for path in existing:
        assert path.read_text(encoding="utf-8") != OCCUPIED


def test_no_interactive_skips_existing_files_reports_them_and_exits_zero(tmp_path):
    existing = _occupy(tmp_path, "ai-team/specs/.gitkeep", ".claude/agents/planner.md")

    result = _init([*_base_args(tmp_path), "--no-interactive"])

    assert result.exit_code == 0
    for path in existing:
        assert path.read_text(encoding="utf-8") == OCCUPIED
        assert str(path) in result.stderr
    assert (tmp_path / ".claude" / "agents" / "architect.md").is_file()
    assert (tmp_path / "ai-team" / "decisions" / ".gitkeep").is_file()
    assert (tmp_path / ".ai-team.toml").is_file()


def _written(output: str) -> set[str]:
    return {
        line.split(": ", 1)[1]
        for line in output.splitlines()
        if line.startswith(("WOULD WRITE: ", "WOULD OVERWRITE: ", "OVERWROTE: "))
    }


def test_dry_run_prints_would_prompt_for_each_covered_file_when_interactive(tmp_path):
    existing = _occupy(tmp_path, "ai-team/specs/.gitkeep", ".claude/agents/planner.md")

    result = _init([*_base_args(tmp_path), "--dry-run"], input_text="n\nn\n")

    assert result.exit_code == 0
    assert "CASE: adoption" in result.output.splitlines()
    for path in existing:
        assert f"WOULD PROMPT: {path}" in result.output
        assert str(path) not in _written(result.output)
    assert all(path.read_text(encoding="utf-8") == OCCUPIED for path in existing)


def _snapshot(root: Path) -> dict[Path, str]:
    return {
        path: path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*")
        if path.is_file()
    }


def test_dry_run_with_no_interactive_lists_exactly_what_the_real_run_writes(tmp_path):
    _occupy(tmp_path, "ai-team/specs/.gitkeep", ".claude/agents/planner.md")
    args = [*_base_args(tmp_path), "--no-interactive"]

    dry = _init([*args, "--dry-run"])
    before = _snapshot(tmp_path)
    _init(args)
    after = _snapshot(tmp_path)

    really_written = {
        str(path)
        for path, content in after.items()
        if before.get(path) != content and path != tmp_path / ".gitignore"
    }
    assert dry.exit_code == 0
    assert "WOULD PROMPT" not in dry.output
    assert _written(dry.output) == really_written


def test_dry_run_with_force_lists_existing_files_as_overwritten(tmp_path):
    existing = _occupy(tmp_path, "ai-team/specs/.gitkeep", ".claude/agents/planner.md")

    result = _init([*_base_args(tmp_path), "--force", "--dry-run"])

    assert result.exit_code == 0
    assert "WOULD PROMPT: " + str(existing[0]) not in result.output
    for path in existing:
        assert f"WOULD OVERWRITE: {path}" in result.output
