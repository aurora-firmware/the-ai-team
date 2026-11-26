"""Issues #33, #34, #35: nested project dir, rendered paths, integration branch."""

from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

from ai_team.cli import app
from ai_team.core.config import (
    integration_branch,
    is_valid_branch_name,
    is_valid_project_dir,
    render_placeholders,
)
from ai_team.core.layout import check_level_2, resolve_layout
from ai_team.core.locator import find_project_root

SCAFFOLDS = Path(__file__).resolve().parents[1] / "src/ai_team/init/scaffolds"
ROOT_GUIDANCE_SOURCE = SCAFFOLDS.parent / "sources/root/AGENTS.md"


def _init(target: Path, *extra: str):
    return CliRunner().invoke(app, ["init", str(target), "--no-interactive", *extra])


def _scaffold_destinations(target: Path, project_dir: str) -> dict[Path, Path]:
    """Map each file of the packaged scaffold subtrees to where init writes it."""
    written_roots = {
        "agents": target / ".claude" / "agents",
        "skills": target / ".claude" / "skills",
        "project": target / project_dir,
    }
    destinations = {}
    for subtree, written_root in written_roots.items():
        root = SCAFFOLDS / subtree
        sources = [path for path in root.rglob("*") if path.is_file()]
        assert sources, f"no scaffold sources under {root}"
        for source in sources:
            destinations[source] = written_root / source.relative_to(root)
    return destinations


def _assert_written_as_rendered(
    destinations: dict[Path, Path], *, project_dir: str, branch: str
) -> None:
    for source, written in destinations.items():
        try:
            template = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # AC-009.2 covers files that are not UTF-8 text.
        text = written.read_text(encoding="utf-8")
        expected = render_placeholders(
            template, project_dir=project_dir, integration_branch=branch
        )
        assert text == expected, written
        assert "{{" not in text, written


def test_project_dir_validation_accepts_any_depth_and_rejects_escapes():
    assert is_valid_project_dir("ai-team")
    assert is_valid_project_dir("docs/ai-team")
    assert is_valid_project_dir("a/b/c")
    for bad in ("", ".", "..", "../x", "a/../b", "/abs", "a/", "a\\b", None, 3):
        assert not is_valid_project_dir(bad)


def test_branch_validation():
    assert is_valid_branch_name("dev-agent")
    assert is_valid_branch_name("release/next")
    for bad in ("", "-x", "a b", "a..b", "a/", "x.lock", "a//b", None):
        assert not is_valid_branch_name(bad)


def test_render_placeholders_replaces_every_occurrence():
    text = "{{project_dir}}/a {{project_dir}}/b -> {{integration_branch}}"
    assert (
        render_placeholders(text, project_dir="docs/x", integration_branch="next")
        == "docs/x/a docs/x/b -> next"
    )


def test_init_scaffolds_into_nested_project_dir_and_records_it(tmp_path):
    target = tmp_path / "repo"
    result = _init(target, "--project-dir", "docs/ai-team")

    assert result.exit_code == 0, result.output
    assert (target / "docs" / "ai-team" / "specs" / ".gitkeep").is_file()
    assert not (target / "ai-team").exists()
    data = tomllib.loads((target / ".ai-team.toml").read_text(encoding="utf-8"))
    assert data["project"]["dir"] == "docs/ai-team"
    assert find_project_root(target).project_dir == target / "docs" / "ai-team"


def test_init_rejects_invalid_project_dir_and_branch(tmp_path):
    bad_dir = _init(tmp_path / "a", "--project-dir", "../outside")
    bad_branch = _init(tmp_path / "b", "--integration-branch", "no good")

    assert bad_dir.exit_code == 1
    assert bad_branch.exit_code == 1
    assert not (tmp_path / "outside").exists()


def test_force_reinit_keeps_configured_settings_and_unrelated_tables(tmp_path):
    target = tmp_path / "repo"
    target.mkdir()
    (target / ".ai-team.toml").write_text(
        '[project]\ndir = "docs/ai-team"\n\n'
        '[tracker]\ndir = ".trk"\n\n'
        '[git]\nintegration_branch = "develop"\n\n'
        '[custom]\nkeep = "me"\n',
        encoding="utf-8",
    )

    result = _init(target, "--force")

    assert result.exit_code == 0, result.output
    data = tomllib.loads((target / ".ai-team.toml").read_text(encoding="utf-8"))
    assert data["project"]["dir"] == "docs/ai-team"
    assert data["tracker"]["dir"] == ".trk"
    assert data["git"]["integration_branch"] == "develop"
    assert data["custom"] == {"keep": "me"}
    assert (target / "docs" / "ai-team" / "specs").is_dir()
    assert not (target / "ai-team").exists()
    assert (target / ".trk").is_dir()
    assert "/.trk/" in (target / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_reinit_without_force_changes_nothing_in_a_non_interactive_upgrade(tmp_path):
    target = tmp_path / "repo"
    assert _init(target).exit_code == 0
    before = {path: path.read_bytes() for path in target.rglob("*") if path.is_file()}

    result = _init(target)

    assert result.exit_code == 0
    assert "OVERWROTE" not in result.output
    assert before == {
        path: path.read_bytes() for path in target.rglob("*") if path.is_file()
    }


def test_generated_output_uses_configured_folder_and_branch(tmp_path):
    target = tmp_path / "repo"
    result = _init(
        target,
        "--project-dir",
        "docs/ai-team",
        "--integration-branch",
        "develop",
        "--create-root-guidance",
    )

    assert result.exit_code == 0, result.output
    destinations = _scaffold_destinations(target, "docs/ai-team")
    destinations[ROOT_GUIDANCE_SOURCE] = target / "AGENTS.md"
    _assert_written_as_rendered(
        destinations, project_dir="docs/ai-team", branch="develop"
    )


def test_default_init_renders_default_folder_and_branch(tmp_path):
    target = tmp_path / "repo"
    assert _init(target).exit_code == 0

    _assert_written_as_rendered(
        _scaffold_destinations(target, "ai-team"),
        project_dir="ai-team",
        branch="dev-agent",
    )
    assert integration_branch(target) == "dev-agent"


def test_integration_branch_reads_marker_and_ignores_invalid_values(tmp_path):
    (tmp_path / ".ai-team.toml").write_text(
        '[git]\nintegration_branch = "next"\n', encoding="utf-8"
    )
    assert integration_branch(tmp_path) == "next"

    (tmp_path / ".ai-team.toml").write_text(
        '[git]\nintegration_branch = "bad name"\n', encoding="utf-8"
    )
    assert integration_branch(tmp_path) == "dev-agent"


def test_check_layout_validates_nested_project_dir_levels_1_and_2(tmp_path):
    target = tmp_path / "repo"
    assert _init(target, "--project-dir", "docs/ai-team").exit_code == 0
    (target / "AGENTS.md").write_text("x", encoding="utf-8")

    contract, findings = resolve_layout(target)

    assert contract.project_dir == target.resolve() / "docs" / "ai-team"
    assert not [f for f in findings if "[project].dir" in f.problem]
    assert check_level_2(contract) == []


def test_check_layout_level_2_checks_artifacts_inside_nested_dir(tmp_path):
    target = tmp_path / "repo"
    assert _init(target, "--project-dir", "docs/ai-team").exit_code == 0
    (target / "docs" / "ai-team" / "specs" / "not-a-spec.md").write_text(
        "no frontmatter", encoding="utf-8"
    )

    contract, _ = resolve_layout(target)
    findings = check_level_2(contract)

    assert findings
    assert all("blocked because project directory" not in f.problem for f in findings)
    assert any("not-a-spec.md" in f.path for f in findings)


def test_check_layout_rejects_parent_escape_in_project_dir(tmp_path):
    (tmp_path / ".ai-team.toml").write_text(
        '[project]\ndir = "../outside"\n[init]\ntools = ["claude"]\n',
        encoding="utf-8",
    )

    contract, findings = resolve_layout(tmp_path)

    assert any("[project].dir" in f.problem for f in findings)
    assert contract.project_dir == tmp_path.resolve() / "ai-team"
