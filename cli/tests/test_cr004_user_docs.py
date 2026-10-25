"""Regression tests for CR-004: the project bootstrap in the user-facing docs."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SETUP_GUIDE = (REPO_ROOT / "guides" / "setup-guide.md").read_text(encoding="utf-8")
CUSTOMIZATION_GUIDE = (REPO_ROOT / "guides" / "customization-guide.md").read_text(
    encoding="utf-8"
)
COMPONENT_MAP = (
    REPO_ROOT / "ai-process" / "architecture" / "component-map.md"
).read_text(encoding="utf-8")


def _line_containing(text: str, marker: str) -> str:
    for line in text.splitlines():
        if marker in line:
            return line
    raise AssertionError(f"no line contains {marker!r}")


def test_setup_guide_runs_project_bootstrap_after_s000_approval() -> None:
    assert "project bootstrap" in SETUP_GUIDE
    assert "After S-000 is approved, run the project bootstrap" in SETUP_GUIDE


def test_setup_guide_does_not_tell_reader_to_create_coding_guidelines_by_hand() -> None:
    assert "Create this file and add project-specific rules" not in SETUP_GUIDE
    assert "filled in by the project bootstrap" in SETUP_GUIDE


def test_customization_guide_writes_s000_before_the_bootstrap_fills_guidance() -> None:
    adoption = CUSTOMIZATION_GUIDE.split("## Retrofitting Into an Existing Project")[1]
    s000_at = adoption.index("S-000")
    bootstrap_at = adoption.index("project bootstrap")
    assert s000_at < bootstrap_at
    assert "coding guidelines" in adoption[bootstrap_at:]
    assert "Create `ai-team/docs/coding_guidelines.md`" not in adoption


def test_component_map_limits_new_system_overview_to_bootstrap_tasks() -> None:
    row = _line_containing(COMPONENT_MAP, "| New System Overview |")
    assert "never broken down into tasks" not in row
    assert "only the project bootstrap tasks" in row


def test_component_map_lists_project_bootstrap_procedure_for_planner() -> None:
    row = _line_containing(COMPONENT_MAP, "| Project Bootstrap |")
    assert "Planner" in row
    assert "spec-breakdown" in row
    assert "S-000" in row


def test_setup_guide_upgrade_note_describes_init_and_update_skills() -> None:
    note = _line_containing(SETUP_GUIDE, "To upgrade an installed project")
    assert "`ai-team init`" in note
    assert "`--update-skills`" in note
    assert "refuses to overwrite" not in note


def test_setup_guide_upgrade_note_keeps_coding_guidelines_never_overwritten() -> None:
    note = _line_containing(SETUP_GUIDE, "To upgrade an installed project")
    assert "docs/coding_guidelines.md" in note
    assert "never overwritten, even with `--force`" in note


def test_setup_guide_does_not_say_a_plain_rerun_refuses() -> None:
    assert "a plain re-run refuses" not in SETUP_GUIDE


def test_customization_guide_says_skill_edits_are_overwritten_only_on_upgrade_update() -> (
    None
):
    note = _line_containing(CUSTOMIZATION_GUIDE, "Exported skill files in")
    assert "upgrade updates the agents and skills" in note
    assert "ai-team init --force` overwrites them" not in note


def test_customization_guide_retrofit_step_uses_the_adoption_case() -> None:
    step = _line_containing(CUSTOMIZATION_GUIDE, "Follow the setup guide")
    assert "adoption" in step


def test_customization_guide_describes_rerun_on_initialized_project_as_upgrade_questions() -> (
    None
):
    assert "refuses to overwrite any existing" not in CUSTOMIZATION_GUIDE
    assert "asks the upgrade questions" in CUSTOMIZATION_GUIDE
