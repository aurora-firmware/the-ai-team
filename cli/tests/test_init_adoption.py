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


KEPT_MESSAGE = "Kept existing files (not overwritten):"


def test_reports_kept_files_on_stderr_without_naming_force_when_answered_no(tmp_path):
    existing = _occupy(tmp_path, "ai-team/specs/.gitkeep")

    result = _init(_base_args(tmp_path), input_text="n\nn\nn\n")

    assert KEPT_MESSAGE in result.stderr
    assert "--force" not in result.stderr
    assert str(existing[0]) in result.stderr


def test_reports_kept_files_with_the_same_message_when_no_interactive(tmp_path):
    existing = _occupy(tmp_path, "ai-team/specs/.gitkeep")

    result = _init([*_base_args(tmp_path), "--no-interactive"])

    assert KEPT_MESSAGE in result.stderr
    assert "--force" not in result.stderr
    assert str(existing[0]) in result.stderr


def test_dry_run_reports_adoption_when_only_root_guidance_exists(tmp_path):
    for filename in ("CLAUDE.md", "AGENTS.md"):
        root_guidance = tmp_path / filename
        root_guidance.write_text(OCCUPIED, encoding="utf-8")

        result = _init([*_base_args(tmp_path), "--dry-run", "--no-interactive"])

        assert result.exit_code == 0
        assert "CASE: adoption" in result.output.splitlines()
        assert "CASE: new project" not in result.output.splitlines()
        root_guidance.unlink()


def test_root_guidance_alone_does_not_trigger_the_overwrite_question(tmp_path):
    (root_claude,) = _occupy(tmp_path, "CLAUDE.md")

    result = _init(_base_args(tmp_path), input_text="n\nn\n")

    assert result.exit_code == 0
    assert "Overwrite these existing files?" not in result.output
    assert root_claude.read_text(encoding="utf-8") == OCCUPIED
    assert (tmp_path / "ai-team" / "specs" / ".gitkeep").exists()


def test_dry_run_handles_existing_root_guidance_through_its_own_table(tmp_path):
    (root_claude,) = _occupy(tmp_path, "CLAUDE.md")

    result = _init([*_base_args(tmp_path), "--dry-run"])
    forced = _init([*_base_args(tmp_path), "--dry-run", "--force"])

    assert "CASE: adoption" in result.output.splitlines()
    assert str(root_claude) not in result.output
    assert "Overwrite these existing files?" not in result.output
    assert f"WOULD PROMPT: {root_claude}" in forced.output


def test_new_project_reports_every_created_file_as_wrote(tmp_path):
    result = _init([*_base_args(tmp_path), "--no-interactive"])

    assert result.exit_code == 0
    wrote = {
        line.removeprefix("WROTE: ")
        for line in result.output.splitlines()
        if line.startswith("WROTE: ")
    }
    assert str(tmp_path / ".ai-team.toml") in wrote
    assert str(tmp_path / ".claude" / "agents" / "architect.md") in wrote
    assert str(tmp_path / "ai-team" / "decisions" / ".gitkeep") in wrote
    assert "OVERWROTE" not in result.output


def test_adoption_reports_created_files_as_wrote_and_replaced_as_overwrote(tmp_path):
    (replaced,) = _occupy(tmp_path, ".claude/agents/planner.md")

    result = _init(_base_args(tmp_path), input_text="y\nn\nn\n")

    assert result.exit_code == 0
    lines = result.output.splitlines()
    assert f"OVERWROTE: {replaced}" in lines
    assert f"WROTE: {replaced}" not in lines
    assert f"WROTE: {tmp_path / '.claude' / 'agents' / 'architect.md'}" in lines


# T-161: the real run reports the tracker writes its dry run lists


def test_new_project_reports_the_tracker_folder_as_created(tmp_path):
    result = _init([*_base_args(tmp_path), "--no-interactive"])

    assert result.exit_code == 0
    tracker = tmp_path / ".ai-team" / "tracker"
    assert tracker.is_dir()
    assert f"CREATED: {tracker}" in result.output.splitlines()


def test_new_project_reports_the_root_gitignore_rule_as_updated(tmp_path):
    result = _init([*_base_args(tmp_path), "--no-interactive"])

    assert result.exit_code == 0
    assert f"UPDATED: {tmp_path / '.gitignore'}" in result.output.splitlines()


def test_new_project_reports_an_existing_root_gitignore_without_the_rule(tmp_path):
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    result = _init([*_base_args(tmp_path), "--no-interactive"])

    assert result.exit_code == 0
    assert f"UPDATED: {tmp_path / '.gitignore'}" in result.output.splitlines()


def _tracker_reports(output: str, root: Path, verbs: dict[str, str]) -> set[str]:
    """Return ``<verb>: <relative path>`` for each line using one of *verbs*.

    *verbs* maps the printed verb to a common name, so dry-run and real-run
    lines from different folders can be compared.
    """
    reports = set()
    for line in output.splitlines():
        verb, _, path = line.partition(": ")
        if verb in verbs:
            reports.add(f"{verbs[verb]}: {Path(path).relative_to(root)}")
    return reports


def test_real_run_reports_the_tracker_lines_its_dry_run_lists(tmp_path):
    dry_target = tmp_path / "dry"
    real_target = tmp_path / "real"

    dry = _init([str(dry_target), "--tools", "claude", "--no-interactive", "--dry-run"])
    real = _init([str(real_target), "--tools", "claude", "--no-interactive"])

    dry_reports = _tracker_reports(
        dry.output, dry_target, {"WOULD CREATE": "CREATED", "WOULD UPDATE": "UPDATED"}
    )
    real_reports = _tracker_reports(
        real.output, real_target, {"CREATED": "CREATED", "UPDATED": "UPDATED"}
    )
    assert dry_reports
    assert real_reports == dry_reports


def test_rerun_reports_no_tracker_lines_once_both_exist(tmp_path):
    _init([*_base_args(tmp_path), "--no-interactive"])

    result = _init([*_base_args(tmp_path), "--no-interactive"])

    assert result.exit_code == 0
    assert "CREATED: " not in result.output
    assert "UPDATED: " not in result.output
