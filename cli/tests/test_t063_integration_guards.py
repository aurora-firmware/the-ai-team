"""Tests for T-063: integrate committed-PASS gate, lifecycle guard, safe delete,
and loop committed-handoff preconditions."""

from __future__ import annotations

from tests.source_paths import skill_export_path, skill_source_text


def _integrate_skill_texts() -> tuple[str, str]:
    return (
        skill_source_text("integrate"),
        skill_export_path("integrate").read_text(encoding="utf-8"),
    )


def _dev_loop_skill_texts() -> tuple[str, str]:
    return (
        skill_source_text("dev-loop"),
        skill_export_path("dev-loop").read_text(encoding="utf-8"),
    )


def _bug_loop_skill_texts() -> tuple[str, str]:
    return (
        skill_source_text("bug-loop"),
        skill_export_path("bug-loop").read_text(encoding="utf-8"),
    )


# AC-1: integrate verifies latest committed canonical PASS verdict on dev-agent before merging


def test_integrate_verifies_recorded_pass_verdict_before_merge() -> None:
    """AC-1 (S-006): integrate must verify the latest Review Verdict recorded in the
    tracker work item file is PASS before proceeding to merge."""
    source, export = _integrate_skill_texts()
    required_phrases = (
        "Verify the Latest Recorded Review Verdict is PASS",
        "ai-team show <work-item-id> --json",
    )
    for phrase in required_phrases:
        assert phrase in source, f"integrate skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"


def test_integrate_stops_when_committed_verdict_is_not_pass() -> None:
    """AC-1: integrate must stop and not proceed when the committed verdict is not PASS."""
    source, export = _integrate_skill_texts()

    # The body must describe stopping when verdict is not PASS
    required_phrases = ("not PASS",)

    for phrase in required_phrases:
        assert phrase in source, f"integrate skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"


# AC-2: lifecycle-file guard is retained in integrate


def test_integrate_retains_lifecycle_file_guard_for_implementation_branches() -> None:
    """AC-2: integrate must still stop when an implementation branch modifies a canonical
    lifecycle file."""
    source, export = _integrate_skill_texts()

    required_phrases = (
        "lifecycle",
        "stop",
    )

    for phrase in required_phrases:
        assert phrase in source, f"integrate skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"


# AC-3: integrate uses stop-and-report instead of git branch -D


def test_integrate_does_not_use_forced_branch_delete() -> None:
    """AC-3: integrate must not contain git branch -D (forced delete fallback removed)."""
    source, export = _integrate_skill_texts()
    forbidden_phrase = "branch -D"

    assert forbidden_phrase not in source, (
        "integrate skill source must not include forced delete 'branch -D'"
    )
    assert forbidden_phrase not in export, (
        "Skill export must not include forced delete 'branch -D'"
    )


def test_integrate_stops_and_reports_when_safe_delete_is_refused() -> None:
    """AC-3: when git branch -d is refused, integrate must stop and report instead of
    using git branch -D."""
    source, export = _integrate_skill_texts()

    required_phrases = (
        "stop",
        "report",
    )

    for phrase in required_phrases:
        assert phrase in source, f"integrate skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"


# AC-3b: integrate task completion uses a deletion-aware move and old-path check


def test_integrate_completes_task_through_the_cli_without_a_lifecycle_commit() -> None:
    """S-006 (supersedes B-012): task completion is a status change in the tracker,
    made with `ai-team task complete`, never a git file move or lifecycle commit."""
    source, export = _integrate_skill_texts()
    required_phrases = ("ai-team task complete <task-id>", "nothing to commit")
    for phrase in required_phrases:
        assert phrase in source, f"integrate skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"
    for forbidden in ("git mv", "chore(tasks): move"):
        assert forbidden not in source, f"integrate must not include: {forbidden!r}"


def test_integrate_confirms_completed_status_before_reporting_success() -> None:
    """S-006 (supersedes B-012): integrate confirms the task status is `completed`
    through the CLI before reporting success."""
    source, export = _integrate_skill_texts()
    required_phrases = (
        "The task status is `completed`",
        "stop and report that the lifecycle update did not land",
    )
    for phrase in required_phrases:
        assert phrase in source, f"integrate skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"


def test_dev_loop_records_work_log_in_tracker_without_commit_or_switch() -> None:
    """AC-4 (S-006): dev-loop appends the Developer Work Log handoff to the task file
    in the tracker before integration, with no lifecycle commit or branch switch."""
    source, export = _dev_loop_skill_texts()
    required_phrases = (
        "append the Developer's entry under `## Work Log` in the task file",
        "no switch and no commit",
    )
    for phrase in required_phrases:
        assert phrase in source, f"dev-loop skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"
    assert "chore(tasks): record T-NNN work log" not in source


def test_dev_loop_keeps_the_review_verdict_out_of_version_control() -> None:
    """AC-4 (S-006): the Reviewer appends the verdict to the task file in the tracker
    and does not commit it; integrate checks the latest verdict is PASS."""
    source, export = _dev_loop_skill_texts()
    required_phrases = (
        "The task file is outside version control: do not commit it.",
        "The `integrate` skill verifies",
    )
    for phrase in required_phrases:
        assert phrase in source, f"dev-loop skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"


def test_bug_loop_records_diagnosis_log_in_tracker_without_commit_or_switch() -> None:
    """AC-4 (S-006): bug-loop appends the Diagnosis Log handoff to the bug file in the
    tracker before implementation, with no lifecycle commit or branch switch."""
    source, export = _bug_loop_skill_texts()
    required_phrases = (
        "append the Developer's entry under `## Diagnosis Log` in the bug file",
        "no switch and no commit",
    )
    for phrase in required_phrases:
        assert phrase in source, f"bug-loop skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"
    assert "chore(bugs): record B-NNN diagnosis" not in source


def test_bug_loop_records_work_log_in_tracker_without_commit() -> None:
    """AC-4 (S-006): bug-loop appends the Work Log handoff to the bug file in the
    tracker before review, with no lifecycle commit."""
    source, export = _bug_loop_skill_texts()
    required_phrases = (
        "append the Developer's entry under `## Work Log` in the bug file. No switch and no commit.",
    )
    for phrase in required_phrases:
        assert phrase in source, f"bug-loop skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"
    assert "chore(bugs): record B-NNN work log" not in source


def test_bug_loop_keeps_the_review_verdict_out_of_version_control() -> None:
    """AC-4 (S-006): the Reviewer appends the verdict to the bug file in the tracker
    and does not commit it; integrate checks the latest verdict is PASS."""
    source, export = _bug_loop_skill_texts()
    required_phrases = (
        "The bug file is outside version control: do not commit it.",
        "The `integrate` skill verifies",
    )
    for phrase in required_phrases:
        assert phrase in source, f"bug-loop skill source must include: {phrase!r}"
        assert phrase in export, f"Skill export must include: {phrase!r}"
