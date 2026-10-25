"""Tests for T-025: `ai-team init` command."""

from __future__ import annotations

import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner


def test_init_defaults_to_cwd_and_scaffolds_project_claude_and_marker(
    monkeypatch, tmp_path
):
    """`ai-team init --no-interactive` scaffolds cwd."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    monkeypatch.chdir(target)

    result = CliRunner().invoke(app, ["init", "--no-interactive"])

    marker = target / ".ai-team.toml"

    assert result.exit_code == 0
    assert (target / "ai-team" / "specs" / ".gitkeep").is_file()
    assert not (target / "ai-team" / "tasks").exists()
    assert (target / ".ai-team" / "tracker").is_dir()
    assert (target / ".claude" / "agents" / "planner.md").is_file()
    assert not (target / "ai-process").exists()
    assert marker.is_file()

    data = tomllib.loads(marker.read_text(encoding="utf-8"))
    assert data["project"]["dir"] == "ai-team"
    assert "tools" not in data["init"]
    assert "include_ai_process" not in data["init"]
    assert isinstance(data["init"]["framework_version"], str)
    assert data["init"]["framework_version"]


def test_init_scaffolds_explicit_target_path_with_claude_and_marker(tmp_path):
    """`ai-team init <path> --no-interactive` scaffolds target path."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app,
        ["init", str(target), "--no-interactive"],
    )

    marker = target / ".ai-team.toml"
    assert result.exit_code == 0
    assert (target / "ai-team" / "decisions" / ".gitkeep").is_file()
    assert not (target / "ai-team" / "bugs").exists()
    assert (target / ".claude" / "skills" / "brainstorm" / "SKILL.md").is_file()
    assert marker.is_file()
    assert not (target / "ai-process").exists()


def test_init_skips_existing_files_when_force_is_not_set(monkeypatch, tmp_path):
    """Adoption keeps an existing file, reports it on stderr, and writes the rest."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()

    existing = target / "ai-team" / "specs" / ".gitkeep"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("occupied\n", encoding="utf-8")

    monkeypatch.chdir(target)
    result = CliRunner().invoke(app, ["init", "--no-interactive"])

    assert result.exit_code == 0
    assert existing.read_text(encoding="utf-8") == "occupied\n"
    assert str(existing) in result.stderr
    assert (target / ".claude" / "agents" / "planner.md").is_file()
    assert (target / ".ai-team.toml").is_file()


def test_init_dry_run_lists_files_and_writes_nothing(tmp_path):
    """Dry-run reports planned writes but does not create files or directories."""
    from ai_team.cli import app

    target = tmp_path / "new-repo"
    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--no-interactive",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "WOULD WRITE:" in result.output
    assert str(target / "ai-team" / "specs" / ".gitkeep") in result.output
    assert f"WOULD CREATE: {target / '.ai-team' / 'tracker'}" in result.output
    assert str(target / ".claude" / "agents" / "planner.md") in result.output
    assert str(target / ".ai-team.toml") in result.output
    assert str(target / "AGENTS.md") not in result.output
    assert not target.exists()


def test_init_include_ai_process_is_unknown_option(tmp_path):
    """`--include-ai-process` is not a recognised option and must be rejected."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--no-interactive",
            "--include-ai-process",
        ],
    )

    assert result.exit_code != 0


def test_init_force_allows_overwriting_existing_files(monkeypatch, tmp_path):
    """`--force` permits init to overwrite scaffold destination files."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    existing = target / "ai-team" / "specs" / ".gitkeep"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("occupied\n", encoding="utf-8")

    monkeypatch.chdir(target)
    result = CliRunner().invoke(
        app,
        ["init", "--no-interactive", "--force"],
    )

    assert result.exit_code == 0
    assert existing.read_text(encoding="utf-8") == ""
    assert (target / ".claude" / "skills" / "tdd" / "SKILL.md").is_file()
    data = tomllib.loads((target / ".ai-team.toml").read_text(encoding="utf-8"))
    assert data["project"]["dir"] == "ai-team"


def test_init_rejects_the_tools_option_and_writes_nothing(tmp_path):
    """`--tools` is an unknown option: Typer rejects it before init writes anything."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app, ["init", str(target), "--tools", "claude", "--no-interactive"]
    )

    assert result.exit_code == 2
    assert "No such option" in result.output
    assert not target.exists()


def test_init_writes_only_claude_agents_and_skills_non_interactively(tmp_path):
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(app, ["init", str(target), "--no-interactive"])

    assert result.exit_code == 0
    assert (target / ".claude" / "agents" / "planner.md").is_file()
    assert (target / ".claude" / "skills" / "tdd" / "SKILL.md").is_file()
    assert not (target / ".codex").exists()
    assert not (target / ".agents").exists()


def test_init_interactive_writes_claude_files_without_asking_for_tools(tmp_path):
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(app, ["init", str(target)], input="y\ny\n")

    assert result.exit_code == 0
    assert "tools" not in result.output.lower()
    assert (target / ".claude" / "agents" / "planner.md").is_file()
    assert (target / ".claude" / "skills" / "tdd" / "SKILL.md").is_file()
    assert not (target / ".codex").exists()


def test_init_never_adds_tools_to_the_marker(tmp_path):
    from ai_team.cli import app

    target = tmp_path / "repo"
    CliRunner().invoke(app, ["init", str(target), "--no-interactive"])

    data = tomllib.loads((target / ".ai-team.toml").read_text(encoding="utf-8"))
    assert "tools" not in data["init"]


def test_init_interactive_does_not_prompt_for_ai_process_snapshot(tmp_path):
    """Interactive mode does not ask whether to include an ai-process snapshot."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    # Provide one root-guidance confirmation (AGENTS.md).
    result = CliRunner().invoke(
        app,
        ["init", str(target)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "Include ai-process" not in result.output


def test_init_creates_project_guidance_files(tmp_path):
    """AC-3: init writes ai-team/AGENTS.md and no ai-team/CLAUDE.md."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app,
        ["init", str(target), "--no-interactive"],
    )

    assert result.exit_code == 0
    assert (target / "ai-team" / "AGENTS.md").is_file()
    assert not (target / "ai-team" / "CLAUDE.md").exists()


def test_init_dry_run_includes_project_guidance_files(tmp_path):
    """AC-3: dry-run output lists ai-team/AGENTS.md and not ai-team/CLAUDE.md."""
    from ai_team.cli import app

    target = tmp_path / "new-repo"
    result = CliRunner().invoke(
        app,
        ["init", str(target), "--no-interactive", "--dry-run"],
    )

    assert result.exit_code == 0
    assert str(target / "ai-team" / "AGENTS.md") in result.output
    assert str(target / "ai-team" / "CLAUDE.md") not in result.output


def test_init_skips_project_guidance_file_when_it_exists_without_force(
    monkeypatch, tmp_path
):
    """AC-4: init keeps an existing ai-team/AGENTS.md without --force and still exits 0."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()

    existing = target / "ai-team" / "AGENTS.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("occupied\n", encoding="utf-8")

    monkeypatch.chdir(target)
    result = CliRunner().invoke(app, ["init", "--no-interactive"])

    assert result.exit_code == 0
    assert existing.read_text(encoding="utf-8") == "occupied\n"
    assert (target / ".claude" / "agents" / "planner.md").is_file()


def test_init_force_overwrites_project_guidance_files(monkeypatch, tmp_path):
    """AC-4: --force allows init to overwrite existing project guidance files."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()

    existing = target / "ai-team" / "AGENTS.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("old content\n", encoding="utf-8")

    monkeypatch.chdir(target)
    result = CliRunner().invoke(app, ["init", "--no-interactive", "--force"])

    assert result.exit_code == 0
    assert existing.read_text(encoding="utf-8") != "old content\n"
    assert (target / "ai-team" / "AGENTS.md").is_file()


def _write_existing_guidelines(target: Path) -> Path:
    existing = target / "ai-team" / "docs" / "coding_guidelines.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("project rules\n", encoding="utf-8")
    return existing


def test_init_writes_coding_guidelines_placeholder_when_missing(tmp_path):
    """AC-1: init writes docs/coding_guidelines.md when it does not exist."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(app, ["init", str(target), "--no-interactive"])

    assert result.exit_code == 0
    written = target / "ai-team" / "docs" / "coding_guidelines.md"
    assert written.is_file()
    assert written.read_text(encoding="utf-8").strip() != ""


def test_init_keeps_existing_coding_guidelines_without_counting_a_collision(tmp_path):
    """AC-2: an existing coding_guidelines.md is not a collision and is kept."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    existing = _write_existing_guidelines(target)

    result = CliRunner().invoke(app, ["init", str(target), "--no-interactive"])

    assert result.exit_code == 0
    assert existing.read_text(encoding="utf-8") == "project rules\n"
    assert (target / "ai-team" / "AGENTS.md").is_file()


def test_init_force_keeps_existing_coding_guidelines(tmp_path):
    """AC-2: --force does not overwrite an existing coding_guidelines.md."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    existing = _write_existing_guidelines(target)

    result = CliRunner().invoke(
        app, ["init", str(target), "--no-interactive", "--force"]
    )

    assert result.exit_code == 0
    assert existing.read_text(encoding="utf-8") == "project rules\n"
    assert str(existing) not in result.output


def test_init_dry_run_does_not_list_existing_coding_guidelines(tmp_path):
    """AC-3: dry-run omits coding_guidelines.md when it exists, lists it when missing."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    existing = _write_existing_guidelines(target)
    args = ["init", str(target), "--no-interactive", "--dry-run"]

    kept = CliRunner().invoke(app, args)
    existing.unlink()
    missing = CliRunner().invoke(app, args)

    assert kept.exit_code == 0
    assert str(existing) not in kept.output
    assert str(existing) in missing.output


def test_init_still_skips_other_skeleton_collisions_when_guidelines_exist(tmp_path):
    """AC-4: other skeleton files are skipped without --force and overwritten by it."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    guidelines = _write_existing_guidelines(target)
    claude_md = target / "ai-team" / "AGENTS.md"
    claude_md.write_text("occupied\n", encoding="utf-8")
    args = ["init", str(target), "--no-interactive"]

    skipped = CliRunner().invoke(app, args)
    assert claude_md.read_text(encoding="utf-8") == "occupied\n"
    forced = CliRunner().invoke(app, [*args, "--force"])

    assert skipped.exit_code == 0
    assert str(claude_md) in skipped.stderr
    assert str(guidelines) not in skipped.output
    assert forced.exit_code == 0
    assert claude_md.read_text(encoding="utf-8") != "occupied\n"
    assert guidelines.read_text(encoding="utf-8") == "project rules\n"


# ── Root guidance file tests (T-050) ─────────────────────────────────────────


def test_interactive_init_prompts_to_create_root_agents_md_when_missing(tmp_path):
    """AC-2: interactive init asks whether to create root AGENTS.md when absent."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    # Provide: create AGENTS.md=yes
    result = CliRunner().invoke(
        app,
        ["init", str(target)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "AGENTS.md" in result.output
    assert (target / "AGENTS.md").is_file()


def test_non_interactive_init_skips_root_guidance_by_default(tmp_path):
    """AC-3: non-interactive init does not create root guidance files by default."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app,
        ["init", str(target), "--no-interactive"],
    )

    assert result.exit_code == 0
    assert not (target / "AGENTS.md").exists()


def test_non_interactive_init_creates_root_guidance_with_flag(tmp_path):
    """AC-3: --create-root-guidance creates root guidance files in non-interactive mode."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--no-interactive",
            "--create-root-guidance",
        ],
    )

    assert result.exit_code == 0
    assert (target / "AGENTS.md").is_file()
    assert not (target / "CLAUDE.md").exists()


def test_declining_root_guidance_prints_followup_message(tmp_path):
    """AC-4: declining root guidance creation prints follow-up about documenting commands."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    # AGENTS.md=no
    result = CliRunner().invoke(
        app,
        ["init", str(target)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert not (target / "AGENTS.md").exists()
    # Should print guidance about documenting project commands
    assert "AGENTS.md" in result.output
    assert "CLAUDE.md" not in result.output
    assert "commands" in result.output.lower()


def test_root_guidance_file_existing_agents_md_is_not_overwritten(tmp_path):
    """AC-5: existing root AGENTS.md is not replaced when interactive init runs."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    existing_agents = target / "AGENTS.md"
    existing_agents.write_text("existing agents content\n", encoding="utf-8")

    # AGENTS.md exists so no prompt for it
    result = CliRunner().invoke(
        app,
        ["init", str(target)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert existing_agents.read_text(encoding="utf-8") == "existing agents content\n"


def test_root_guidance_file_created_from_stable_template(tmp_path):
    """Root AGENTS.md must be created from the stable template with command documentation guidance."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--no-interactive",
            "--create-root-guidance",
        ],
    )

    assert result.exit_code == 0
    content = (target / "AGENTS.md").read_text(encoding="utf-8")
    # Template must invite projects to record test/run commands
    assert "test" in content.lower() or "command" in content.lower()


def test_force_flag_overwrites_existing_root_guidance_files(tmp_path):
    """AC-5 exception: --force allows overwriting existing root guidance files."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    existing_claude = target / "AGENTS.md"
    existing_claude.write_text("old content\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--no-interactive",
            "--create-root-guidance",
            "--force",
        ],
    )

    assert result.exit_code == 0
    assert existing_claude.read_text(encoding="utf-8") != "old content\n"


def test_init_scaffolds_project_gitignore_ignoring_the_lock_sentinel(tmp_path):
    """B-017: init writes ai-team/.gitignore covering the .ai-team.lock sentinel."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app,
        ["init", str(target), "--no-interactive"],
    )

    assert result.exit_code == 0
    gitignore = target / "ai-team" / ".gitignore"
    assert gitignore.is_file()
    ignored = gitignore.read_text(encoding="utf-8").splitlines()
    assert ".ai-team.lock" in ignored
    assert "docs/reports/" in ignored


def test_ai_team_lock_sentinel_is_not_untracked_after_task_creation(
    monkeypatch, tmp_path
):
    """B-017 fix verification: after init + task new, .ai-team.lock is not untracked."""
    from ai_team.cli import app

    target = tmp_path / "repo"
    result = CliRunner().invoke(
        app,
        ["init", str(target), "--no-interactive"],
    )
    assert result.exit_code == 0

    subprocess.run(["git", "init", "-q"], cwd=target, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=target, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=target, check=True)
    subprocess.run(["git", "add", "-A"], cwd=target, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=target, check=True)

    monkeypatch.chdir(target)
    task_result = CliRunner().invoke(app, ["task", "new", "Anything", "--json"])
    assert task_result.exit_code == 0

    lock_file = target / ".ai-team" / "tracker" / ".ai-team.lock"
    assert lock_file.is_file()

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=target,
        check=True,
        capture_output=True,
        text=True,
    )

    assert status.stdout == "", (
        f"task creation left the working tree dirty:\n{status.stdout}"
    )


def test_init_configures_tracker_and_ignores_it_idempotently(tmp_path):
    """S-006: init writes [tracker] dir, creates the folder, and ignores it once."""
    import tomllib

    from ai_team.cli import app

    target = tmp_path / "repo"
    target.mkdir()
    (target / ".gitignore").write_text("node_modules/", encoding="utf-8")

    for extra in ([], ["--force"]):
        result = CliRunner().invoke(
            app,
            ["init", str(target), "--no-interactive", *extra],
        )
        assert result.exit_code == 0, result.output

    marker = tomllib.loads((target / ".ai-team.toml").read_text(encoding="utf-8"))
    assert marker["tracker"]["dir"] == ".ai-team/tracker"
    assert (target / ".ai-team" / "tracker").is_dir()

    lines = (target / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "node_modules/"
    assert lines.count("/.ai-team/") == 1


# ── Root guidance contract and overwrite report (B-018) ─────────────────────


def _repo_with_custom_root_guidance(tmp_path):
    target = tmp_path / "repo"
    target.mkdir()
    for name in ("AGENTS.md",):
        (target / name).write_text("custom\n", encoding="utf-8")
    return target


def _overwrote_lines(output):
    return [line for line in output.splitlines() if line.startswith("OVERWROTE: ")]


def _init(target, *flags, input=None):
    from ai_team.cli import app

    return CliRunner().invoke(app, ["init", str(target), *flags], input=input)


def test_interactive_force_overwrites_and_reports_root_guidance_on_yes(tmp_path):
    target = _repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--force", input="y\n")

    assert result.exit_code == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") != "custom\n"
    assert f"OVERWROTE: {target / 'AGENTS.md'}" in result.output


def test_interactive_force_keeps_and_does_not_report_root_guidance_on_no(tmp_path):
    target = _repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--force", input="n\n")

    assert result.exit_code == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "custom\n"
    assert f"OVERWROTE: {target / 'AGENTS.md'}" not in result.output


def test_interactive_force_with_create_root_guidance_overwrites_without_prompt(
    tmp_path,
):
    target = _repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--force", "--create-root-guidance")

    assert result.exit_code == 0
    assert "Create root" not in result.output
    assert (target / "AGENTS.md").read_text(encoding="utf-8") != "custom\n"
    assert f"OVERWROTE: {target / 'AGENTS.md'}" in result.output


def test_interactive_create_root_guidance_creates_missing_files_without_prompt(
    tmp_path,
):
    target = tmp_path / "repo"

    result = _init(target, "--create-root-guidance")

    assert result.exit_code == 0
    assert "Create root" not in result.output
    assert (target / "AGENTS.md").is_file()
    assert not (target / "CLAUDE.md").exists()


def test_non_interactive_force_with_create_root_guidance_overwrites_and_reports(
    tmp_path,
):
    target = _repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--force", "--no-interactive", "--create-root-guidance")

    assert result.exit_code == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") != "custom\n"
    assert f"OVERWROTE: {target / 'AGENTS.md'}" in result.output


def test_non_interactive_force_without_flag_leaves_root_guidance_untouched(tmp_path):
    target = _repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--force", "--no-interactive")

    assert result.exit_code == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "custom\n"
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "custom\n"
    assert f"OVERWROTE: {target / 'CLAUDE.md'}" not in result.output


def test_create_root_guidance_without_force_leaves_existing_files_untouched(
    tmp_path,
):
    target = _repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--create-root-guidance")

    assert result.exit_code == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "custom\n"
    assert _overwrote_lines(result.output) == []


def test_fresh_init_reports_no_overwrites(tmp_path):
    target = tmp_path / "repo"

    result = _init(target, "--no-interactive", "--create-root-guidance")

    assert result.exit_code == 0
    assert _overwrote_lines(result.output) == []


def test_force_rerun_reports_existing_files_but_not_newly_created_ones(tmp_path):
    target = tmp_path / "repo"
    _init(target, "--no-interactive", "--create-root-guidance")
    (target / "AGENTS.md").unlink()

    result = _init(target, "--force", "--no-interactive", "--create-root-guidance")

    assert result.exit_code == 0
    reported = _overwrote_lines(result.output)
    assert f"OVERWROTE: {target / '.ai-team.toml'}" not in reported
    assert (
        f"OVERWROTE: {target / '.claude' / 'skills' / 'tdd' / 'SKILL.md'}" in reported
    )
    assert f"OVERWROTE: {target / 'AGENTS.md'}" not in reported
    assert result.output.index("OVERWROTE:") < result.output.index(
        "Initialization complete."
    )


# ── Dry run mirrors the real run (B-021) ────────────────────────────────────


def _would_lines(output, verb):
    return {
        line.removeprefix(f"{verb}: ")
        for line in output.splitlines()
        if line.startswith(f"{verb}: ")
    }


def _initialised_repo_with_custom_root_guidance(tmp_path):
    target = tmp_path / "repo"
    _init(target, "--no-interactive", "--create-root-guidance")
    for name in ("AGENTS.md",):
        (target / name).write_text("custom\n", encoding="utf-8")
    return target


def _root_paths(target):
    return {str(target / "AGENTS.md")}


def _all_would_paths(output):
    paths = set()
    for verb in ("WOULD WRITE", "WOULD OVERWRITE", "WOULD PROMPT", "WOULD CREATE"):
        paths |= _would_lines(output, verb)
    return paths


def test_dry_run_non_interactive_force_names_neither_tracker_nor_root_guidance(
    tmp_path,
):
    target = _initialised_repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--force", "--no-interactive", "--dry-run")

    assert result.exit_code == 0
    named = _all_would_paths(result.output)
    assert str(target / ".ai-team" / "tracker") not in named
    assert not named & _root_paths(target)


def test_dry_run_creates_tracker_line_only_when_tracker_is_missing(tmp_path):
    target = tmp_path / "repo"

    result = _init(target, "--no-interactive", "--dry-run")

    assert f"WOULD CREATE: {target / '.ai-team' / 'tracker'}" in result.output


def test_dry_run_reports_gitignore_update_only_when_rule_is_missing(tmp_path):
    target = _initialised_repo_with_custom_root_guidance(tmp_path)
    gitignore = target / ".gitignore"

    present = _init(target, "--force", "--no-interactive", "--dry-run")
    gitignore.write_text("", encoding="utf-8")
    missing = _init(target, "--force", "--no-interactive", "--dry-run")

    assert str(gitignore) not in _would_lines(present.output, "WOULD UPDATE")
    assert str(gitignore) in _would_lines(missing.output, "WOULD UPDATE")


def test_dry_run_interactive_force_prompts_for_existing_and_missing_root_files(
    tmp_path,
):
    target = _initialised_repo_with_custom_root_guidance(tmp_path)
    (target / "AGENTS.md").unlink()

    result = _init(target, "--force", "--dry-run")

    assert result.exit_code == 0
    assert _would_lines(result.output, "WOULD PROMPT") == _root_paths(target)
    assert "Create root" not in result.output


def test_dry_run_interactive_force_create_root_guidance_overwrites_without_prompt(
    tmp_path,
):
    target = _initialised_repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--force", "--create-root-guidance", "--dry-run")

    assert _would_lines(result.output, "WOULD OVERWRITE") >= _root_paths(target)
    assert _would_lines(result.output, "WOULD PROMPT") == set()


def test_dry_run_non_interactive_force_create_root_guidance_distinguishes_new_files(
    tmp_path,
):
    target = _initialised_repo_with_custom_root_guidance(tmp_path)
    (target / "AGENTS.md").unlink()

    result = _init(
        target, "--force", "--no-interactive", "--create-root-guidance", "--dry-run"
    )

    assert str(target / "AGENTS.md") in _would_lines(result.output, "WOULD WRITE")


def test_dry_run_without_force_names_no_existing_root_file_in_either_mode(tmp_path):
    target = tmp_path / "repo"
    target.mkdir()
    for name in ("AGENTS.md",):
        (target / name).write_text("custom\n", encoding="utf-8")

    interactive = _init(target, "--dry-run")
    non_interactive = _init(target, "--no-interactive", "--dry-run")

    assert not _all_would_paths(interactive.output) & _root_paths(target)
    assert not _all_would_paths(non_interactive.output) & _root_paths(target)


def test_dry_run_non_interactive_without_flag_names_no_missing_root_file(tmp_path):
    target = tmp_path / "repo"

    result = _init(target, "--no-interactive", "--dry-run")

    assert not _all_would_paths(result.output) & _root_paths(target)


def test_dry_run_of_a_non_interactive_upgrade_prints_nothing_to_write(tmp_path):
    target = _initialised_repo_with_custom_root_guidance(tmp_path)

    result = _init(target, "--no-interactive", "--dry-run")

    assert result.exit_code == 0
    assert "WOULD" not in result.output


@pytest.mark.parametrize(
    "flags",
    [
        ("--force", "--no-interactive"),
        ("--force", "--no-interactive", "--create-root-guidance"),
        ("--force", "--create-root-guidance"),
    ],
)
def test_dry_run_write_set_equals_paths_the_real_run_writes(tmp_path, flags):
    target = _initialised_repo_with_custom_root_guidance(tmp_path)
    (target / "AGENTS.md").unlink()
    (target / ".gitignore").write_text("", encoding="utf-8")
    copy = tmp_path / "copy"
    shutil.copytree(target, copy)
    files_before = {
        path.relative_to(copy) for path in copy.rglob("*") if path.is_file()
    }

    dry = _init(target, *flags, "--dry-run")
    real = _init(copy, *flags)

    def relative(paths, root):
        return {Path(path).relative_to(root) for path in paths}

    dry_set = relative(
        _would_lines(dry.output, "WOULD WRITE")
        | _would_lines(dry.output, "WOULD OVERWRITE"),
        target,
    )
    files_after = {path.relative_to(copy) for path in copy.rglob("*") if path.is_file()}
    created = {
        path for path in files_after - files_before if path.parts[0] != ".ai-team"
    }
    real_set = relative(_would_lines(real.output, "OVERWROTE"), copy) | created
    real_set.discard(Path(".gitignore"))
    assert dry_set == real_set
