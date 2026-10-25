"""Tests for read-only project layout contract validation."""

from __future__ import annotations

import importlib.resources as resources
import shutil
from pathlib import Path

import pytest

from ai_team.core.layout import (
    LayoutContract,
    LayoutFinding,
    check_layout,
    check_level_1,
    check_level_2,
    check_level_3,
    check_level_4,
    resolve_layout,
)
from ai_team.core.tool_paths import TOOL_EXPORT_PATHS


def _write_marker(
    repo: Path,
    *,
    project_dir: str = "ai-team",
    tools: tuple[str, ...] = ("claude", "codex"),
    version: str = "1.2.3",
) -> None:
    rendered_tools = ", ".join(f'"{tool}"' for tool in tools)
    (repo / ".ai-team.toml").write_text(
        f'[project]\ndir = "{project_dir}"\n\n'
        f"[init]\ntools = [{rendered_tools}]\n"
        f'framework_version = "{version}"\n',
        encoding="utf-8",
    )


def _create_current_scaffold(repo: Path, tools: tuple[str, ...]) -> None:
    scaffold_root = resources.files("ai_team.init").joinpath("scaffolds")
    exports = [("project", "ai-team")]
    for tool in tools:
        exports.extend(
            (f"{tool}/{subfolder}", destination)
            for subfolder, destination in TOOL_EXPORT_PATHS[tool]
        )
    for source_name, destination_name in exports:
        source = scaffold_root.joinpath(source_name)
        for entry in source.rglob("*"):
            if entry.is_dir():
                (repo / destination_name / entry.relative_to(source)).mkdir(
                    parents=True, exist_ok=True
                )
        (repo / destination_name).mkdir(parents=True, exist_ok=True)
    guidelines = repo / "ai-team" / "docs" / "coding_guidelines.md"
    guidelines.parent.mkdir(parents=True, exist_ok=True)
    guidelines.write_text("# Coding guidelines\n", encoding="utf-8")


def _snapshot(repo: Path) -> list[tuple[str, bool, bytes | None]]:
    return [
        (
            path.relative_to(repo).as_posix(),
            path.is_dir(),
            None if path.is_dir() else path.read_bytes(),
        )
        for path in sorted(repo.rglob("*"))
    ]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    # Work items live in the tracker; artifact checks still need the project dir.
    for parent in path.parents:
        if parent.name == ".ai-team":
            (parent.parent / "ai-team").mkdir(exist_ok=True)
            break


def _frontmatter(**values: str) -> str:
    fields = "\n".join(f"{key}: {value}" for key, value in values.items())
    return f"---\n{fields}\n---\n\nBody.\n"


_VALID_GUIDANCE = """\
# Project Guidance

## Build and Install

Run `uv build` from `cli/`.

## Test

Run `uv run pytest` from `cli/`.

## Run

This package is a CLI; run `uv run ai-team --help`.

## Lint and Format

Run `uv run ruff check .` and `uv run ruff format --check .`.

## Key Conventions

Keep framework sources separate from generated scaffolds.
"""


def test_resolve_layout_reads_valid_local_marker_and_distribution_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_marker(
        tmp_path,
        project_dir="team-state",
        tools=("codex", "claude"),
        version="2.4.0",
    )
    monkeypatch.setattr("importlib.metadata.version", lambda name: "2.4.0")

    contract, findings = resolve_layout(tmp_path)

    assert contract == LayoutContract(
        repo=tmp_path,
        marker=tmp_path / ".ai-team.toml",
        project_dir=tmp_path / "team-state",
        tools=("codex", "claude"),
        configured_version="2.4.0",
        current_version="2.4.0",
        raw_configured_version="2.4.0",
    )
    assert findings == []


@pytest.mark.parametrize(
    ("marker", "expected_problem"),
    [
        (None, "missing"),
        ("not valid = [toml", "invalid"),
        ('[project]\ndir = "../outside"\n[init]\ntools = "codex"\n', "invalid"),
    ],
)
def test_resolve_layout_reports_marker_faults_and_uses_safe_conventions(
    tmp_path: Path, marker: str | None, expected_problem: str
) -> None:
    if marker is not None:
        (tmp_path / ".ai-team.toml").write_text(marker, encoding="utf-8")

    contract, findings = resolve_layout(tmp_path, current_version="1.2.3")

    assert contract.project_dir == tmp_path / "ai-team"
    assert contract.tools == ()
    assert findings
    assert all(finding.suggested_fix for finding in findings)
    assert any(expected_problem in finding.problem.lower() for finding in findings)


def test_level_1_reports_every_missing_current_scaffold_directory_and_allows_extra(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("codex",))
    _create_current_scaffold(tmp_path, ("codex",))
    shutil.rmtree(tmp_path / "ai-team" / "specs")
    shutil.rmtree(tmp_path / ".codex" / "agents")
    (tmp_path / "ai-team" / "extra").mkdir()
    contract, resolution_findings = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_1(contract)

    assert resolution_findings == []
    assert {finding.path for finding in findings} == {
        "ai-team/specs",
        ".codex/agents",
    }
    assert all(finding.level == 1 for finding in findings)
    assert all(finding.problem and finding.suggested_fix for finding in findings)


def test_level_1_reports_missing_agents_skills_for_codex(tmp_path: Path) -> None:
    _write_marker(tmp_path, tools=("codex",))
    _create_current_scaffold(tmp_path, ("codex",))
    shutil.rmtree(tmp_path / ".agents" / "skills")
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_1(contract)

    assert ".agents/skills" in {finding.path for finding in findings}


def test_level_1_reports_missing_coding_guidelines_with_scaffold_fix(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("claude",))
    _create_current_scaffold(tmp_path, ("claude",))
    (tmp_path / "ai-team" / "docs" / "coding_guidelines.md").unlink()
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_1(contract)

    assert [(f.level, f.path) for f in findings] == [
        (1, "ai-team/docs/coding_guidelines.md")
    ]
    assert "scaffold placeholder" in findings[0].suggested_fix


def test_level_1_reports_no_finding_for_existing_coding_guidelines_of_any_content(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("claude",))
    _create_current_scaffold(tmp_path, ("claude",))
    (tmp_path / "ai-team" / "docs" / "coding_guidelines.md").write_text(
        "", encoding="utf-8"
    )
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    assert check_level_1(contract) == []


def test_level_1_does_not_require_bare_tool_roots(tmp_path: Path) -> None:
    _write_marker(tmp_path, tools=("claude", "codex"))
    _create_current_scaffold(tmp_path, ("claude", "codex"))
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    assert check_level_1(contract) == []
    assert not (tmp_path / ".codex" / "skills").exists()


@pytest.mark.parametrize(
    ("relative_path", "content", "expected_problem"),
    [
        (
            "ai-team/specs/Bad Spec.md",
            _frontmatter(
                id="S-001",
                title="Spec",
                version="'0.1'",
                status="approved",
                created="2026-06-24",
                author="planner",
            ),
            "filename",
        ),
        (
            ".ai-team/tracker/tasks/T-001-task.md",
            _frontmatter(
                id="T-001",
                title="Task",
                status="pending",
                priority="medium",
                created="2026-06-24",
            ),
            "frontmatter",
        ),
        (
            ".ai-team/tracker/bugs/not-a-bug.md",
            _frontmatter(
                id="B-001",
                title="Bug",
                severity="medium",
                status="open",
                created="2026-06-24",
            ),
            "filename",
        ),
        (
            ".ai-team/tracker/change-requests/request.md",
            _frontmatter(
                id="CR-001",
                title="Request",
                status="pending",
                created="2026-06-24",
            ),
            "filename",
        ),
        (
            "ai-team/decisions/decision.md",
            _frontmatter(
                id="ADR-001",
                title="Decision",
                status="accepted",
                created="2026-06-24",
            ),
            "filename",
        ),
    ],
)
def test_level_2_reuses_artifact_filename_and_frontmatter_rules(
    tmp_path: Path,
    relative_path: str,
    content: str,
    expected_problem: str,
) -> None:
    _write_marker(tmp_path, tools=())
    _write(tmp_path / relative_path, content)
    contract, resolution_findings = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_2(contract)

    assert resolution_findings == []
    assert findings
    assert all(finding.level == 2 for finding in findings)
    assert any(expected_problem in finding.problem.lower() for finding in findings)
    assert all(finding.suggested_fix for finding in findings)


@pytest.mark.parametrize(
    ("relative_path", "status"),
    [
        (".ai-team/tracker/tasks/T-001-task.md", "done"),
        (".ai-team/tracker/bugs/B-001-bug.md", "closed"),
    ],
)
def test_level_2_reports_invalid_status_values_with_actionable_fix(
    tmp_path: Path, relative_path: str, status: str
) -> None:
    _write_marker(tmp_path, tools=())
    if "/tasks/" in relative_path:
        content = _frontmatter(
            id="T-001",
            title="Task",
            status=status,
            priority="medium",
            **{"assigned-role": "developer"},
            created="2026-06-24",
        )
    else:
        content = _frontmatter(
            id="B-001",
            title="Bug",
            severity="medium",
            status=status,
            created="2026-06-24",
        )
    _write(tmp_path / relative_path, content)
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_2(contract)

    invalid = next(
        finding for finding in findings if "is not one of" in finding.problem
    )
    assert status in invalid.problem
    assert "allowed values" in invalid.suggested_fix.lower()


def test_level_1_reports_unmigrated_legacy_work_item_folders(tmp_path: Path) -> None:
    _write_marker(tmp_path, tools=())
    _create_current_scaffold(tmp_path, ())
    _write(tmp_path / "ai-team" / "tasks" / "pending" / "T-001-old.md", "legacy")
    (tmp_path / "ai-team" / "bugs" / "open").mkdir(parents=True)
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_1(contract)

    assert [finding.path for finding in findings] == ["ai-team/tasks"]
    assert "legacy" in findings[0].problem.lower()
    assert "migrating to the local tracker" in findings[0].suggested_fix.lower()


def test_level_1_reports_tracker_inside_repository_that_git_does_not_ignore(
    tmp_path: Path,
) -> None:
    import subprocess

    _write_marker(tmp_path, tools=())
    _create_current_scaffold(tmp_path, ())
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    assert [finding.path for finding in check_level_1(contract)] == [".ai-team/tracker"]

    (tmp_path / ".gitignore").write_text("/.ai-team/\n", encoding="utf-8")
    assert check_level_1(contract) == []


def test_level_2_ignores_placeholders_and_non_artifact_documentation(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=())
    _write(tmp_path / ".ai-team/tracker/tasks/.gitkeep", "")
    _write(tmp_path / ".ai-team/tracker/tasks/TEMPLATE-task.md", "not frontmatter")
    _write(tmp_path / "ai-team/docs/Bad Documentation.md", "not frontmatter")
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    assert check_level_2(contract) == []


def test_level_2_reports_malformed_artifact_and_continues_independent_checks(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=())
    _write(
        tmp_path / ".ai-team/tracker/tasks/T-001-malformed.md",
        "---\ninvalid: [yaml\n---\n",
    )
    _write(
        tmp_path / "ai-team/decisions/bad-name.md",
        _frontmatter(
            id="ADR-001",
            title="Decision",
            status="accepted",
            created="2026-06-24",
        ),
    )
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_2(contract)

    assert {finding.path for finding in findings} == {
        ".ai-team/tracker/tasks/T-001-malformed.md",
        "ai-team/decisions/bad-name.md",
    }
    assert any("frontmatter" in finding.problem.lower() for finding in findings)
    assert any("filename" in finding.problem.lower() for finding in findings)


def test_invalid_artifact_encoding_is_blocked_and_guidance_check_continues(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("codex",))
    artifact = tmp_path / ".ai-team/tracker/tasks/T-001-invalid-encoding.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"\xff")

    findings = check_layout(tmp_path, current_version="1.2.3")

    assert any(
        finding.level == 2 and "blocked" in finding.problem.lower()
        for finding in findings
    )
    assert any(
        finding.level == 3
        and finding.path == "AGENTS.md"
        and "missing" in finding.problem.lower()
        for finding in findings
    )


def test_missing_project_directory_still_checks_tracker_artifacts(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path)
    task = tmp_path / ".ai-team/tracker/tasks/T-001-invalid-status.md"
    task.parent.mkdir(parents=True)
    task.write_text(
        "---\nid: T-001\ntitle: Invalid status\nstatus: bogus\npriority: low\n"
        "assigned-role: unassigned\ncreated: '2026-10-21'\n---\n\n# Invalid status\n",
        encoding="utf-8",
    )

    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")
    findings = check_level_2(contract)

    assert any(
        finding.path == "ai-team" and "blocked" in finding.problem.lower()
        for finding in findings
    )
    assert any(
        finding.path.endswith("T-001-invalid-status.md")
        and "status 'bogus'" in finding.problem
        for finding in findings
    )


@pytest.mark.parametrize(
    ("tools", "required", "not_required"),
    [
        (("codex",), "AGENTS.md", "CLAUDE.md"),
        (("claude",), "CLAUDE.md", "AGENTS.md"),
    ],
)
def test_level_3_selects_root_guidance_from_configured_tools(
    tmp_path: Path,
    tools: tuple[str, ...],
    required: str,
    not_required: str,
) -> None:
    _write_marker(tmp_path, tools=tools)
    _write(tmp_path / required, _VALID_GUIDANCE)
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    assert check_level_3(contract) == []
    assert not (tmp_path / not_required).exists()


def test_level_3_requires_both_guidance_files_when_both_tools_are_configured(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("claude", "codex"))
    _write(tmp_path / "CLAUDE.md", _VALID_GUIDANCE)
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_3(contract)

    assert [finding.path for finding in findings] == ["AGENTS.md"]
    assert "missing" in findings[0].problem.lower()
    assert findings[0].suggested_fix


def test_level_3_reports_each_missing_or_placeholder_contract_section(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("codex",))
    starter = resources.files("ai_team.init").joinpath("sources", "root", "AGENTS.md")
    _write(tmp_path / "AGENTS.md", starter.read_text(encoding="utf-8"))
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_3(contract)

    assert len(findings) == 5
    combined = " ".join(finding.problem for finding in findings)
    for heading in (
        "Build and Install",
        "Test",
        "Run",
        "Lint and Format",
        "Key Conventions",
    ):
        assert heading in combined
    assert all(finding.level == 3 for finding in findings)
    assert all("placeholder" in finding.problem.lower() for finding in findings)


def test_level_3_reports_missing_section_without_executing_guidance_commands(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("codex",))
    sentinel = tmp_path / "command-ran"
    guidance = _VALID_GUIDANCE.replace(
        "## Test\n\nRun `uv run pytest` from `cli/`.\n\n", ""
    ).replace(
        "Run `uv build` from `cli/`.",
        f"Run `touch {sentinel}` to build.",
    )
    _write(tmp_path / "AGENTS.md", guidance)
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_3(contract)

    assert len(findings) == 1
    assert "Test" in findings[0].problem
    assert "missing" in findings[0].problem.lower()
    assert not sentinel.exists()


def test_level_3_reports_unreadable_guidance_and_continues_other_file(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("claude", "codex"))
    (tmp_path / "CLAUDE.md").write_bytes(b"\xff")
    _write(tmp_path / "AGENTS.md", _VALID_GUIDANCE.replace("## Run", "## Start"))
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_3(contract)

    assert {finding.path for finding in findings} == {"CLAUDE.md", "AGENTS.md"}
    assert any("blocked" in finding.problem.lower() for finding in findings)
    assert any("Run" in finding.problem for finding in findings)


@pytest.mark.parametrize(
    ("configured", "problem_parts"),
    [
        (None, ("missing", "1.2.3")),
        (42, ("invalid", "42", "1.2.3")),
        ("1.2.2", ("1.2.2", "1.2.3")),
    ],
)
def test_level_4_reports_missing_invalid_and_non_exact_versions(
    tmp_path: Path, configured: str | int | None, problem_parts: tuple[str, ...]
) -> None:
    marker_version = (
        ""
        if configured is None
        else f'framework_version = "{configured}"\n'
        if isinstance(configured, str)
        else f"framework_version = {configured}\n"
    )
    (tmp_path / ".ai-team.toml").write_text(
        '[project]\ndir = "project"\n[init]\ntools = []\n' + marker_version,
        encoding="utf-8",
    )
    contract, resolution_findings = resolve_layout(tmp_path, current_version="1.2.3")

    findings = [*resolution_findings, *check_level_4(contract)]

    assert contract.raw_configured_version == configured
    if configured == 42:
        assert contract.configured_version is None
    assert any(finding.level == 4 for finding in findings)
    combined_problem = " ".join(finding.problem.lower() for finding in findings)
    assert all(part.lower() in combined_problem for part in problem_parts)


def test_level_4_accepts_only_an_exact_version_match(tmp_path: Path) -> None:
    _write_marker(tmp_path, tools=(), version="1.2.3+local.1")
    contract, resolution_findings = resolve_layout(
        tmp_path, current_version="1.2.3+local.1"
    )

    assert resolution_findings == []
    assert check_level_4(contract) == []


def test_check_layout_runs_artifact_and_guidance_levels(tmp_path: Path) -> None:
    _write_marker(tmp_path, tools=("codex",))
    _write(tmp_path / ".ai-team/tracker/tasks/T-001-task.md", "not frontmatter")

    findings = check_layout(tmp_path, current_version="1.2.3")

    assert {finding.level for finding in findings} >= {2, 3}
    assert any(finding.path.endswith("T-001-task.md") for finding in findings)
    assert any(finding.path == "AGENTS.md" for finding in findings)


def test_check_layout_returns_ordered_findings_without_modifying_repository(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("claude",), version="1.0.0")
    (tmp_path / "ai-team" / "unexpected").mkdir(parents=True)
    before = _snapshot(tmp_path)

    findings = check_layout(tmp_path, current_version="2.0.0")

    assert findings == sorted(
        findings, key=lambda finding: (finding.level, finding.path)
    )
    assert all(isinstance(finding, LayoutFinding) for finding in findings)
    assert all(
        finding.level and finding.path and finding.problem and finding.suggested_fix
        for finding in findings
    )
    assert _snapshot(tmp_path) == before


def test_level_1_reports_nothing_for_a_freshly_initialised_all_tools_project(
    tmp_path: Path,
) -> None:
    from typer.testing import CliRunner

    from ai_team.cli import app

    result = CliRunner().invoke(
        app, ["init", str(tmp_path), "--tools", "all", "--no-interactive"]
    )
    contract, _ = resolve_layout(tmp_path, current_version=None)

    assert result.exit_code == 0
    assert check_level_1(contract) == []


def test_level_1_suggests_update_skills_for_a_missing_tool_directory(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("codex",))
    _create_current_scaffold(tmp_path, ("codex",))
    shutil.rmtree(tmp_path / ".codex" / "agents")
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_1(contract)

    fixes = {finding.path: finding.suggested_fix for finding in findings}
    assert "ai-team init --update-skills" in fixes[".codex/agents"]


def test_level_1_suggests_plain_init_for_a_missing_project_directory(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, tools=("codex",))
    _create_current_scaffold(tmp_path, ("codex",))
    shutil.rmtree(tmp_path / "ai-team" / "specs")
    contract, _ = resolve_layout(tmp_path, current_version="1.2.3")

    findings = check_level_1(contract)

    fixes = {finding.path: finding.suggested_fix for finding in findings}
    assert "--update-skills" not in fixes["ai-team/specs"]
    assert "ai-team init" in fixes["ai-team/specs"]
