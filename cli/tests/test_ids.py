"""
Tests for T-008: ai_team.core.ids — artifact ID allocation helpers.

Cycle 1 scope:
  - next_task_id() behavior for empty and mixed-state task folders.
"""

from pathlib import Path

from ai_team.core.ids import (
    OVERVIEW_ID,
    is_overview_reference,
    next_adr_id,
    next_bug_id,
    next_change_request_id,
    next_spec_id,
    next_task_id,
    overview_exists,
)
from ai_team.core.locator import ProjectRoot


def make_project_root(tmp_path: Path) -> ProjectRoot:
    """Create the minimal artifact tree and return a matching ProjectRoot."""
    project_dir = tmp_path / "ai-team"
    (project_dir / "specs" / "archive").mkdir(parents=True)
    (project_dir / "decisions").mkdir(parents=True)
    (project_dir / "docs").mkdir(parents=True)
    root = ProjectRoot._from_repo_and_project_dir_name(tmp_path, "ai-team")
    root.tasks.mkdir(parents=True)
    root.bugs.mkdir(parents=True)
    return root


def test_next_task_id_returns_t_001_when_no_task_files_exist(tmp_path):
    """AC-1: empty task folders return T-001."""
    root = make_project_root(tmp_path)
    assert next_task_id(root) == "T-001"


def test_next_task_id_uses_highest_number_in_the_tracker(tmp_path):
    """AC-1: allocator scans the tracker's tasks folder."""
    root = make_project_root(tmp_path)
    (root.tasks / "T-007-define-parser.md").write_text("", encoding="utf-8")
    (root.tasks / "T-012-finalize-parser.md").write_text("", encoding="utf-8")

    assert next_task_id(root) == "T-013"


def test_next_task_id_ignores_non_matching_task_files(tmp_path):
    """AC-4: only files matching T-NNN-*.md are considered."""
    root = make_project_root(tmp_path)
    (root.tasks / "TEMPLATE-task.md").write_text("", encoding="utf-8")
    (root.tasks / ".gitkeep").write_text("", encoding="utf-8")
    (root.tasks / "T-01-not-padded.md").write_text("", encoding="utf-8")
    (root.tasks / "T-999-no-extension.txt").write_text("", encoding="utf-8")

    assert next_task_id(root) == "T-001"


def test_next_bug_id_returns_b_001_when_no_bug_files_exist(tmp_path):
    """AC-3: bug IDs are zero-padded and start from B-001."""
    root = make_project_root(tmp_path)
    assert next_bug_id(root) == "B-001"


def test_next_bug_id_scans_the_tracker_and_ignores_non_matching(tmp_path):
    """AC-2: bug allocator scans the tracker, ignoring invalid names."""
    root = make_project_root(tmp_path)
    (root.bugs / "B-004-first.md").write_text("", encoding="utf-8")
    (root.bugs / "B-009-last.md").write_text("", encoding="utf-8")
    (root.bugs / "TEMPLATE-bug.md").write_text("", encoding="utf-8")
    (root.bugs / "B-01-not-padded.md").write_text("", encoding="utf-8")

    assert next_bug_id(root) == "B-010"


def test_next_task_and_bug_ids_ignore_the_tracker_archive_folder(tmp_path):
    """AC-3: files under <tracker>/archive/<bucket>/ are not counted."""
    root = make_project_root(tmp_path)
    bucket = root.tracker / "archive" / "2026-01"
    bucket.mkdir(parents=True)
    (bucket / "T-012-finalize-parser.md").write_text("", encoding="utf-8")
    (bucket / "B-009-last.md").write_text("", encoding="utf-8")

    assert next_task_id(root) == "T-001"
    assert next_bug_id(root) == "B-001"


def test_next_spec_id_uses_project_and_archive_as_one_number_space(tmp_path):
    """AC-3: spec IDs scan specs/ and specs/archive/ together."""
    root = make_project_root(tmp_path)
    (root.specs / "S-002-initial-spec.md").write_text("", encoding="utf-8")
    (root.specs / "archive" / "S-014-legacy-spec.md").write_text("", encoding="utf-8")
    (root.specs / "archive" / "template-spec.md").write_text("", encoding="utf-8")

    assert next_spec_id(root) == "S-015"


def test_next_adr_id_returns_zero_padded_identifier(tmp_path):
    """AC-3: ADR IDs use ADR-NNN formatting."""
    root = make_project_root(tmp_path)
    assert next_adr_id(root) == "ADR-001"


def test_next_adr_id_ignores_non_matching_files(tmp_path):
    """AC-4: only ADR-NNN-*.md contributes to the next ADR ID."""
    root = make_project_root(tmp_path)
    (root.decisions / "ADR-003-use-skill.md").write_text("", encoding="utf-8")
    (root.decisions / "003-use-old-pattern.md").write_text("", encoding="utf-8")
    (root.decisions / "ADR-template.md").write_text("", encoding="utf-8")
    (root.decisions / ".gitkeep").write_text("", encoding="utf-8")

    assert next_adr_id(root) == "ADR-004"


def test_next_change_request_id_returns_cr_001_when_no_matches_exist(tmp_path):
    """CR IDs start at CR-001 when no matching files are found."""
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    assert next_change_request_id((first, second)) == "CR-001"


def test_next_change_request_id_scans_provided_directories(tmp_path):
    """Allocator increments from the max CR-NNN in provided directories."""
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    (first / "CR-003-small-change.md").write_text("", encoding="utf-8")
    (second / "CR-011-bigger-change.md").write_text("", encoding="utf-8")

    assert next_change_request_id((first, second)) == "CR-012"


def test_next_change_request_id_ignores_non_matching_filenames(tmp_path):
    """Only CR-NNN-*.md filenames contribute to the next change-request ID."""
    search_dir = tmp_path / "changes"
    search_dir.mkdir()

    (search_dir / "CR-template.md").write_text("", encoding="utf-8")
    (search_dir / "CR-11-not-padded.md").write_text("", encoding="utf-8")
    (search_dir / "CR-999-no-extension.txt").write_text("", encoding="utf-8")
    (search_dir / "notes.md").write_text("", encoding="utf-8")

    assert next_change_request_id((search_dir,)) == "CR-001"


def test_overview_id_is_s_000():
    assert OVERVIEW_ID == "S-000"


def test_overview_exists_is_false_when_no_s_000_file_exists(tmp_path):
    root = make_project_root(tmp_path)
    (root.specs / "S-001-feature.md").write_text("", encoding="utf-8")

    assert overview_exists(root) is False


def test_overview_exists_detects_s_000_filename_in_specs(tmp_path):
    root = make_project_root(tmp_path)
    (root.specs / "S-000-system-overview.md").write_text("", encoding="utf-8")

    assert overview_exists(root) is True


def test_overview_exists_detects_s_000_filename_in_archive(tmp_path):
    root = make_project_root(tmp_path)
    (root.specs / "archive" / "S-000-old.md").write_text("", encoding="utf-8")

    assert overview_exists(root) is True


def test_overview_exists_detects_s_000_frontmatter_id_with_other_filename(tmp_path):
    root = make_project_root(tmp_path)
    (root.specs / "archive" / "overview.md").write_text(
        "---\nid: S-000\ntitle: x\n---\n", encoding="utf-8"
    )

    assert overview_exists(root) is True


def test_next_spec_id_returns_s_001_when_s_000_is_the_only_spec(tmp_path):
    root = make_project_root(tmp_path)
    (root.specs / "S-000-system-overview.md").write_text(
        "---\nid: S-000\n---\n", encoding="utf-8"
    )

    assert next_spec_id(root) == "S-001"


def test_is_overview_reference_true_for_overview_id_slug_filename_and_path():
    assert is_overview_reference("S-000")
    assert is_overview_reference("S-000-system-overview")
    assert is_overview_reference("S-000-system-overview.md")
    assert is_overview_reference("docs/ai-team/specs/S-000-system-overview.md")


def test_is_overview_reference_false_for_other_references():
    for reference in ("S-001", "S-0001", "S-000x", "", "CR-000", "T-000"):
        assert not is_overview_reference(reference), reference
