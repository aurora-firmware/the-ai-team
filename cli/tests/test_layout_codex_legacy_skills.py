"""Tests for legacy .codex/skills findings reported by the layout check."""

from __future__ import annotations

from pathlib import Path

from ai_team.core.layout import (
    LayoutFinding,
    check_layout,
    check_level_1,
    resolve_layout,
)
from ai_team.core.tool_paths import framework_skill_names


def _write_marker(repo: Path, tools: tuple[str, ...]) -> None:
    rendered_tools = ", ".join(f'"{tool}"' for tool in tools)
    (repo / ".ai-team.toml").write_text(
        f'[project]\ndir = "ai-team"\n\n[init]\ntools = [{rendered_tools}]\n'
        'framework_version = "1.2.3"\n',
        encoding="utf-8",
    )


def _legacy_findings(repo: Path) -> list[LayoutFinding]:
    contract, _ = resolve_layout(repo, current_version="1.2.3")
    return [
        finding
        for finding in check_level_1(contract)
        if finding.path.startswith(".codex/skills")
    ]


def _snapshot(repo: Path) -> list[tuple[str, bool]]:
    return sorted((p.relative_to(repo).as_posix(), p.is_dir()) for p in repo.rglob("*"))


def test_reports_legacy_folder_for_framework_owned_codex_skill(tmp_path: Path) -> None:
    name = framework_skill_names("codex")[0]
    _write_marker(tmp_path, ("codex",))
    (tmp_path / ".codex" / "skills" / name).mkdir(parents=True)

    assert _legacy_findings(tmp_path) == [
        LayoutFinding(
            1,
            f".codex/skills/{name}",
            f"Legacy Codex skill folder '.codex/skills/{name}' duplicates the framework skill exported to '.agents/skills/{name}'.",
            "Rerun 'ai-team init --update-skills' to remove the legacy copy.",
        )
    ]


def test_reports_no_legacy_finding_for_folders_the_framework_does_not_own(
    tmp_path: Path,
) -> None:
    _write_marker(tmp_path, ("codex",))
    (tmp_path / ".codex" / "skills" / "my-own-skill").mkdir(parents=True)

    assert _legacy_findings(tmp_path) == []


def test_reports_no_legacy_finding_when_codex_is_not_configured(
    tmp_path: Path,
) -> None:
    name = framework_skill_names("codex")[0]
    _write_marker(tmp_path, ("claude",))
    (tmp_path / ".codex" / "skills" / name).mkdir(parents=True)

    assert _legacy_findings(tmp_path) == []


def test_legacy_findings_leave_repository_unchanged(tmp_path: Path) -> None:
    name = framework_skill_names("codex")[0]
    _write_marker(tmp_path, ("codex",))
    (tmp_path / ".codex" / "skills" / name).mkdir(parents=True)
    before = _snapshot(tmp_path)

    assert _legacy_findings(tmp_path)
    assert _snapshot(tmp_path) == before


def _expected_finding(name: str) -> LayoutFinding:
    return LayoutFinding(
        1,
        f".codex/skills/{name}",
        f"Legacy Codex skill folder '.codex/skills/{name}' duplicates the framework skill exported to '.agents/skills/{name}'.",
        "Rerun 'ai-team init --update-skills' to remove the legacy copy.",
    )


def test_reports_one_finding_per_framework_folder_in_path_order_ignoring_user_folder(
    tmp_path: Path,
) -> None:
    first, second = sorted(framework_skill_names("codex"))[:2]
    _write_marker(tmp_path, ("codex",))
    skills = tmp_path / ".codex" / "skills"
    for name in (second, "my-own-skill", first):
        (skills / name).mkdir(parents=True)

    assert _legacy_findings(tmp_path) == [
        _expected_finding(first),
        _expected_finding(second),
    ]


def test_check_layout_includes_legacy_finding_in_sorted_full_result(
    tmp_path: Path,
) -> None:
    name = framework_skill_names("codex")[0]
    _write_marker(tmp_path, ("codex",))
    (tmp_path / ".codex" / "skills" / name).mkdir(parents=True)

    findings = check_layout(tmp_path, current_version="1.2.3")

    assert _expected_finding(name) in findings
    assert len(findings) > 1
    assert findings == sorted(
        findings,
        key=lambda f: (f.level, f.path, f.problem, f.suggested_fix),
    )
