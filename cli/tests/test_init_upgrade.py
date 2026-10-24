"""Tests for T-148: `ai-team init` state detection and the upgrade case."""

from __future__ import annotations

import shutil
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from ai_team.cli import app

DOCS_PROMPT = "update the ai-team docs"
SKILLS_PROMPT = "update the agents and skills"


def _run(target: Path, *flags: str, input: str | None = None):
    return CliRunner().invoke(app, ["init", str(target), *flags], input=input)


def _new_project(tmp_path: Path, tools: str = "claude") -> Path:
    """A fresh project whose root guidance exists, so upgrades ask nothing about it."""
    target = tmp_path / "repo"
    result = _run(
        target, "--tools", tools, "--no-interactive", "--create-root-guidance"
    )
    assert result.exit_code == 0, result.output
    return target


def _doc_files(target: Path) -> list[Path]:
    return [
        target / "ai-team" / name for name in ("AGENTS.md", "CLAUDE.md", ".gitignore")
    ]


def _exported_files(target: Path) -> list[Path]:
    return sorted(
        path
        for folder in (".claude", ".codex", ".agents")
        if (target / folder).is_dir()
        for path in (target / folder).rglob("*")
        if path.is_file()
    )


def _mark_custom(paths: list[Path]) -> None:
    for path in paths:
        path.write_text("custom\n", encoding="utf-8")


def _is_custom(paths: list[Path]) -> bool:
    return all(path.read_text(encoding="utf-8") == "custom\n" for path in paths)


def _is_refreshed(paths: list[Path]) -> bool:
    return all(path.read_text(encoding="utf-8") != "custom\n" for path in paths)


def _snapshot(target: Path) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in target.rglob("*") if path.is_file()}


# AC-1


def test_upgrade_asks_for_docs_then_for_agents_and_skills(tmp_path):
    target = _new_project(tmp_path)

    result = _run(target, input="n\nn\n")

    assert result.exit_code == 0, result.output
    output = result.output.lower()
    assert DOCS_PROMPT in output
    assert SKILLS_PROMPT in output
    assert output.index(DOCS_PROMPT) < output.index(SKILLS_PROMPT)


def test_upgrade_writes_only_the_docs_when_only_the_docs_question_is_yes(tmp_path):
    target = _new_project(tmp_path)
    docs, exported = _doc_files(target), _exported_files(target)
    _mark_custom(docs + exported)

    result = _run(target, input="y\nn\n")

    assert result.exit_code == 0, result.output
    assert _is_refreshed(docs)
    assert _is_custom(exported)
    assert f"OVERWROTE: {docs[0]}" in result.output


def test_upgrade_writes_only_agents_and_skills_when_only_that_question_is_yes(
    tmp_path,
):
    target = _new_project(tmp_path)
    docs, exported = _doc_files(target), _exported_files(target)
    _mark_custom(docs + exported)

    result = _run(target, input="n\ny\n")

    assert result.exit_code == 0, result.output
    assert _is_custom(docs)
    assert _is_refreshed(exported)


def test_upgrade_recreates_a_missing_project_directory(tmp_path):
    target = _new_project(tmp_path)
    shutil.rmtree(target / "ai-team")

    result = _run(target, "--no-interactive")

    assert result.exit_code == 0, result.output
    assert (target / "ai-team" / "specs" / ".gitkeep").is_file()
    assert (target / "ai-team" / "CLAUDE.md").is_file()


# AC-2


def test_update_docs_flag_answers_the_docs_question_without_prompting(tmp_path):
    target = _new_project(tmp_path)
    docs, exported = _doc_files(target), _exported_files(target)
    _mark_custom(docs + exported)

    result = _run(target, "--update-docs", input="n\n")

    assert result.exit_code == 0, result.output
    assert DOCS_PROMPT not in result.output.lower()
    assert SKILLS_PROMPT in result.output.lower()
    assert _is_refreshed(docs)
    assert _is_custom(exported)


def test_update_skills_flag_answers_the_skills_question_without_prompting(tmp_path):
    target = _new_project(tmp_path)
    docs, exported = _doc_files(target), _exported_files(target)
    _mark_custom(docs + exported)

    result = _run(target, "--update-skills", input="n\n")

    assert result.exit_code == 0, result.output
    assert SKILLS_PROMPT not in result.output.lower()
    assert DOCS_PROMPT in result.output.lower()
    assert _is_custom(docs)
    assert _is_refreshed(exported)


def test_force_answers_both_upgrade_questions_yes_without_prompting(tmp_path):
    target = _new_project(tmp_path)
    docs, exported = _doc_files(target), _exported_files(target)
    _mark_custom(docs + exported)

    result = _run(target, "--force", input="n\nn\n")

    assert result.exit_code == 0, result.output
    assert DOCS_PROMPT not in result.output.lower()
    assert SKILLS_PROMPT not in result.output.lower()
    assert _is_refreshed(docs + exported)


# AC-3


def test_no_interactive_upgrade_changes_nothing_and_reports_nothing(tmp_path):
    target = _new_project(tmp_path)
    _mark_custom(_doc_files(target) + _exported_files(target))
    before = _snapshot(target)

    result = _run(target, "--no-interactive")

    assert result.exit_code == 0, result.output
    assert _snapshot(target) == before
    assert "OVERWROTE" not in result.output
    assert "WROTE" not in result.output


def test_no_interactive_upgrade_takes_the_tools_from_the_marker(tmp_path):
    target = _new_project(tmp_path, tools="codex")
    removed = _exported_files(target)[0]
    removed.unlink()

    result = _run(target, "--no-interactive", "--update-skills")

    assert result.exit_code == 0, result.output
    assert removed.is_file()
    assert not (target / ".claude").exists()


def test_upgrade_rewrites_the_marker_when_an_explicit_setting_changes(tmp_path):
    target = _new_project(tmp_path)

    result = _run(target, "--no-interactive", "--tools", "all")

    marker = target / ".ai-team.toml"
    assert result.exit_code == 0, result.output
    assert f"OVERWROTE: {marker}" in result.output
    data = tomllib.loads(marker.read_text(encoding="utf-8"))
    assert data["init"]["tools"] == ["claude", "codex"]


def test_upgrade_keeps_the_marker_bytes_when_no_setting_changes(tmp_path):
    target = _new_project(tmp_path)
    marker = target / ".ai-team.toml"
    before = marker.read_bytes()

    result = _run(
        target,
        "--force",
        "--no-interactive",
        "--tools",
        "claude",
        "--integration-branch",
        "dev-agent",
    )

    assert result.exit_code == 0, result.output
    assert marker.read_bytes() == before
    assert f"OVERWROTE: {marker}" not in result.output


# AC-4


def test_dry_run_upgrade_prompts_for_each_file_an_unanswered_question_covers(
    tmp_path,
):
    target = _new_project(tmp_path)
    before = _snapshot(target)

    result = _run(target, "--dry-run")

    assert result.exit_code == 0, result.output
    prompted = {
        line.removeprefix("WOULD PROMPT: ")
        for line in result.output.splitlines()
        if line.startswith("WOULD PROMPT: ")
    }
    assert {str(path) for path in _doc_files(target)} <= prompted
    assert {str(path) for path in _exported_files(target)} <= prompted
    assert _snapshot(target) == before


def test_dry_run_upgrade_treats_unanswered_questions_as_no_when_not_interactive(
    tmp_path,
):
    target = _new_project(tmp_path)

    result = _run(target, "--dry-run", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert "WOULD" not in result.output


def test_dry_run_upgrade_answers_flagged_questions_without_prompting(tmp_path):
    target = _new_project(tmp_path)
    docs = _doc_files(target)

    result = _run(target, "--dry-run", "--update-docs")

    assert result.exit_code == 0, result.output
    for path in docs:
        assert f"WOULD OVERWRITE: {path}" in result.output
        assert f"WOULD PROMPT: {path}" not in result.output
    assert f"WOULD PROMPT: {_exported_files(target)[0]}" in result.output
