"""Tests for T-148: `ai-team init` state detection and the upgrade case."""

from __future__ import annotations

import importlib.metadata
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


# T-154

OLD_VERSION = "0.0.1"


def _set_framework_version(target: Path, version: str) -> None:
    marker = target / ".ai-team.toml"
    text = marker.read_text(encoding="utf-8")
    current = tomllib.loads(text)["init"]["framework_version"]
    marker.write_text(
        text.replace(
            f'framework_version = "{current}"', f'framework_version = "{version}"'
        ),
        encoding="utf-8",
    )


def _marker_data(target: Path) -> dict:
    return tomllib.loads((target / ".ai-team.toml").read_text(encoding="utf-8"))


def _running_version() -> str:
    return importlib.metadata.version("ai-team")


def _add_legacy_codex_skill(target: Path) -> Path:
    legacy = target / ".codex" / "skills" / "tdd"
    legacy.mkdir(parents=True)
    (legacy / "SKILL.md").write_text("legacy\n", encoding="utf-8")
    return legacy


def test_skills_update_sets_framework_version_and_keeps_other_settings(tmp_path):
    target = _new_project(tmp_path)
    _set_framework_version(target, OLD_VERSION)
    before = _marker_data(target)

    result = _run(target, "--update-skills", input="n\n")

    assert result.exit_code == 0, result.output
    after = _marker_data(target)
    assert after["init"]["framework_version"] == _running_version()
    before["init"]["framework_version"] = _running_version()
    assert after == before


def test_force_upgrade_sets_framework_version(tmp_path):
    target = _new_project(tmp_path)
    _set_framework_version(target, OLD_VERSION)

    result = _run(target, "--force", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert _marker_data(target)["init"]["framework_version"] == _running_version()


def test_interactive_yes_to_skills_sets_framework_version(tmp_path):
    target = _new_project(tmp_path)
    _set_framework_version(target, OLD_VERSION)

    result = _run(target, input="n\ny\n")

    assert result.exit_code == 0, result.output
    assert _marker_data(target)["init"]["framework_version"] == _running_version()


def test_framework_version_is_unchanged_when_skills_are_not_updated(tmp_path):
    target = _new_project(tmp_path)
    _set_framework_version(target, OLD_VERSION)

    result = _run(target, "--update-docs", input="n\n")

    assert result.exit_code == 0, result.output
    assert _marker_data(target)["init"]["framework_version"] == OLD_VERSION


def test_dry_run_reports_the_version_bump_without_writing_it(tmp_path):
    target = _new_project(tmp_path)
    _set_framework_version(target, OLD_VERSION)

    result = _run(target, "--dry-run", "--update-skills")

    assert result.exit_code == 0, result.output
    assert f"WOULD OVERWRITE: {target / '.ai-team.toml'}" in result.output
    assert _marker_data(target)["init"]["framework_version"] == OLD_VERSION


def test_skills_update_for_codex_removes_and_reports_legacy_skills(tmp_path):
    target = _new_project(tmp_path, tools="codex")
    legacy = _add_legacy_codex_skill(target)

    result = _run(target, "--update-skills", input="n\n")

    assert result.exit_code == 0, result.output
    assert not legacy.exists()
    assert f"REMOVED: {legacy}" in result.output


def test_force_upgrade_for_codex_removes_legacy_skills(tmp_path):
    target = _new_project(tmp_path, tools="codex")
    legacy = _add_legacy_codex_skill(target)

    result = _run(target, "--force", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert not legacy.exists()


def test_legacy_codex_skills_stay_when_skills_are_not_updated(tmp_path):
    target = _new_project(tmp_path, tools="codex")
    legacy = _add_legacy_codex_skill(target)

    result = _run(target, "--no-interactive")

    assert result.exit_code == 0, result.output
    assert legacy.is_dir()


def test_legacy_codex_skills_stay_when_tool_is_not_codex(tmp_path):
    target = _new_project(tmp_path, tools="claude")
    legacy = _add_legacy_codex_skill(target)

    result = _run(target, "--update-skills", input="n\n")

    assert result.exit_code == 0, result.output
    assert legacy.is_dir()


def test_dry_run_reports_legacy_removal_without_removing(tmp_path):
    target = _new_project(tmp_path, tools="codex")
    legacy = _add_legacy_codex_skill(target)

    result = _run(target, "--dry-run", "--update-skills")

    assert result.exit_code == 0, result.output
    assert f"WOULD REMOVE: {legacy}" in result.output
    assert legacy.is_dir()


# T-149

STALE_WARNING_MARKER = "neither updated nor removed"


def _add_stale_definitions(target: Path) -> tuple[Path, Path]:
    stale_skill = target / ".claude" / "skills" / "my-own-skill"
    stale_skill.mkdir(parents=True)
    (stale_skill / "SKILL.md").write_text("mine\n", encoding="utf-8")
    stale_agent = target / ".claude" / "agents" / "my-own-agent.md"
    stale_agent.write_text("mine\n", encoding="utf-8")
    return stale_skill, stale_agent


def test_skills_update_warns_on_stderr_about_definitions_the_version_does_not_ship(
    tmp_path,
):
    target = _new_project(tmp_path)
    stale_skill, stale_agent = _add_stale_definitions(target)

    result = _run(target, "--update-skills", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert result.stderr.count(STALE_WARNING_MARKER) == 1
    assert str(stale_skill) in result.stderr
    assert str(stale_agent) in result.stderr
    assert STALE_WARNING_MARKER not in result.stdout


def test_skills_update_never_deletes_definitions_the_version_does_not_ship(tmp_path):
    target = _new_project(tmp_path)
    stale_skill, stale_agent = _add_stale_definitions(target)

    result = _run(target, "--force", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert (stale_skill / "SKILL.md").read_text(encoding="utf-8") == "mine\n"
    assert stale_agent.read_text(encoding="utf-8") == "mine\n"


def test_no_stale_warning_when_every_definition_is_shipped(tmp_path):
    target = _new_project(tmp_path)

    result = _run(target, "--update-skills", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert STALE_WARNING_MARKER not in result.stderr


def test_no_stale_warning_when_skills_are_not_updated(tmp_path):
    target = _new_project(tmp_path)
    _add_stale_definitions(target)

    result = _run(target, "--no-interactive")

    assert result.exit_code == 0, result.output
    assert STALE_WARNING_MARKER not in result.stderr


def test_dry_run_upgrade_starts_with_the_upgrade_case_line(tmp_path):
    target = _new_project(tmp_path)

    result = _run(target, "--dry-run", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[0] == "CASE: upgrade"


def test_dry_run_upgrade_prints_case_then_would_lines_then_the_stale_warning(
    tmp_path,
):
    target = _new_project(tmp_path)
    stale_skill, _ = _add_stale_definitions(target)

    result = _run(target, "--dry-run", "--update-skills", "--no-interactive")

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0] == "CASE: upgrade"
    assert lines[1].startswith("WOULD ")
    assert STALE_WARNING_MARKER in result.stderr
    assert str(stale_skill) in result.stderr
    assert (stale_skill / "SKILL.md").exists()


def test_dry_run_on_an_empty_directory_starts_with_the_new_project_case_line(
    tmp_path,
):
    target = tmp_path / "repo"

    result = _run(target, "--tools", "claude", "--dry-run", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[0] == "CASE: new project"
    assert result.stdout.splitlines()[1].startswith("WOULD WRITE: ")


def test_dry_run_with_existing_scaffold_files_but_no_marker_is_adoption(tmp_path):
    target = tmp_path / "repo"
    existing = target / ".claude" / "agents" / "developer.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("mine\n", encoding="utf-8")

    result = _run(
        target, "--tools", "claude", "--dry-run", "--force", "--no-interactive"
    )

    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[0] == "CASE: adoption"
    assert f"WOULD OVERWRITE: {existing}" in result.stdout


def test_real_run_does_not_print_a_case_line(tmp_path):
    target = tmp_path / "repo"

    result = _run(target, "--tools", "claude", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert "CASE:" not in result.stdout


# T-157: an upgrade recreates the project-skeleton files no question covers


def test_upgrade_recreates_a_missing_coding_guidelines_file_and_reports_it(tmp_path):
    target = _new_project(tmp_path)
    guidelines = target / "ai-team" / "docs" / "coding_guidelines.md"
    guidelines.unlink()

    result = _run(target, "--no-interactive")

    assert result.exit_code == 0, result.output
    assert guidelines.is_file()
    assert f"WROTE: {guidelines}" in result.output.splitlines()


def test_upgrade_recreates_missing_specs_and_decisions_placeholders(tmp_path):
    target = _new_project(tmp_path)
    placeholders = [
        target / "ai-team" / name / ".gitkeep" for name in ("specs", "decisions")
    ]
    for placeholder in placeholders:
        placeholder.unlink()

    result = _run(target, "--no-interactive")

    assert result.exit_code == 0, result.output
    assert all(placeholder.is_file() for placeholder in placeholders)


def test_force_upgrade_recreates_a_missing_skeleton_file(tmp_path):
    target = _new_project(tmp_path)
    guidelines = target / "ai-team" / "docs" / "coding_guidelines.md"
    guidelines.unlink()

    result = _run(target, "--force", input="n\nn\n")

    assert result.exit_code == 0, result.output
    assert guidelines.is_file()


def test_upgrade_recreates_a_missing_skeleton_file_without_asking(tmp_path):
    target = _new_project(tmp_path)
    guidelines = target / "ai-team" / "docs" / "coding_guidelines.md"
    guidelines.unlink()

    result = _run(target, input="n\nn\n")

    assert result.exit_code == 0, result.output
    assert guidelines.is_file()
    assert "coding_guidelines.md" not in "".join(
        line for line in result.output.splitlines() if "?" in line
    )


def test_dry_run_upgrade_reports_a_missing_skeleton_file_as_would_write(tmp_path):
    target = _new_project(tmp_path)
    guidelines = target / "ai-team" / "docs" / "coding_guidelines.md"
    guidelines.unlink()
    before = _snapshot(target)

    result = _run(target, "--dry-run", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert f"WOULD WRITE: {guidelines}" in result.output.splitlines()
    assert _snapshot(target) == before


# T-157 AC-2


def test_force_upgrade_never_overwrites_an_existing_skeleton_file(tmp_path):
    target = _new_project(tmp_path)
    guidelines = target / "ai-team" / "docs" / "coding_guidelines.md"
    guidelines.write_text("custom\n", encoding="utf-8")

    result = _run(target, "--force", input="n\nn\n")

    assert result.exit_code == 0, result.output
    assert _is_custom([guidelines])
    assert f"OVERWROTE: {guidelines}" not in result.output


def test_docs_yes_still_overwrites_the_docs_files_it_covers(tmp_path):
    target = _new_project(tmp_path)
    _mark_custom(_doc_files(target))

    result = _run(target, "--update-docs", input="n\n")

    assert result.exit_code == 0, result.output
    assert _is_refreshed(_doc_files(target))


# T-158: --tools on an upgrade


def _marker_tools(target: Path) -> list[str]:
    data = tomllib.loads((target / ".ai-team.toml").read_text(encoding="utf-8"))
    return data["init"]["tools"]


def test_upgrade_with_a_new_tool_writes_its_files_without_asking_and_records_it(
    tmp_path,
):
    target = _new_project(tmp_path, tools="claude")
    assert not (target / ".codex").exists()

    result = _run(target, "--tools", "claude,codex", input="n\nn\n")

    assert result.exit_code == 0, result.output
    assert any(path.is_file() for path in (target / ".codex").rglob("*"))
    assert _marker_tools(target) == ["claude", "codex"]


def test_upgrade_with_a_new_tool_writes_it_under_no_interactive(tmp_path):
    target = _new_project(tmp_path, tools="claude")

    result = _run(target, "--tools", "claude,codex", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert any(path.is_file() for path in (target / ".codex").rglob("*"))
    assert _marker_tools(target) == ["claude", "codex"]


def test_upgrade_with_a_new_tool_asks_the_skills_question_once_for_configured_tools(
    tmp_path,
):
    target = _new_project(tmp_path, tools="claude")
    claude_files = [p for p in _exported_files(target) if ".claude" in p.parts]
    _mark_custom(claude_files)

    result = _run(target, "--tools", "claude,codex", input="n\nn\n")

    assert result.exit_code == 0, result.output
    assert result.output.lower().count(SKILLS_PROMPT) == 1
    assert _is_custom(claude_files)


def test_upgrade_with_a_new_tool_refreshes_configured_tools_only_on_a_yes(tmp_path):
    target = _new_project(tmp_path, tools="claude")
    claude_files = [p for p in _exported_files(target) if ".claude" in p.parts]
    _mark_custom(claude_files)

    result = _run(target, "--tools", "claude,codex", "--update-skills", input="n\n")

    assert result.exit_code == 0, result.output
    assert _is_refreshed(claude_files)


def test_dry_run_upgrade_with_a_new_tool_reports_would_write_for_its_files(tmp_path):
    target = _new_project(tmp_path, tools="claude")
    before = _snapshot(target)

    result = _run(target, "--tools", "claude,codex", "--dry-run", "--no-interactive")

    assert result.exit_code == 0, result.output
    would_write = [
        line for line in result.output.splitlines() if line.startswith("WOULD WRITE:")
    ]
    assert would_write
    assert all(".codex" in line or ".agents" in line for line in would_write)
    assert _snapshot(target) == before
    assert not (target / ".codex").exists()


def test_upgrade_dropping_a_tool_removes_it_from_the_marker_and_keeps_its_files(
    tmp_path,
):
    target = _new_project(tmp_path, tools="claude,codex")
    codex_files = [p for p in _exported_files(target) if ".claude" not in p.parts]
    assert codex_files

    result = _run(target, "--tools", "claude", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert _marker_tools(target) == ["claude"]
    assert all(path.is_file() for path in codex_files)


def test_readding_a_dropped_tool_keeps_its_existing_files_and_writes_missing_ones(
    tmp_path,
):
    target = _new_project(tmp_path, tools="claude,codex")
    codex_files = [p for p in _exported_files(target) if ".claude" not in p.parts]
    edited, missing = codex_files[0], codex_files[1]
    edited.write_text("custom\n", encoding="utf-8")
    missing.unlink()
    _run(target, "--tools", "claude", "--no-interactive")

    result = _run(target, "--tools", "claude,codex", "--no-interactive")

    assert result.exit_code == 0, result.output
    assert _is_custom([edited])
    assert missing.is_file()
    assert f"OVERWROTE: {edited}" not in result.output
    assert f"WROTE: {missing}" in result.output


def test_dry_run_readding_a_dropped_tool_does_not_report_existing_files_as_overwritten(
    tmp_path,
):
    target = _new_project(tmp_path, tools="claude,codex")
    _run(target, "--tools", "claude", "--no-interactive")

    result = _run(target, "--tools", "claude,codex", "--no-interactive", "--dry-run")

    assert result.exit_code == 0, result.output
    assert "WOULD OVERWRITE: " + str(target / ".codex") not in result.output
    assert "WOULD OVERWRITE: " + str(target / ".agents") not in result.output
