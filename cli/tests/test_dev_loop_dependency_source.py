"""Pins the dev-loop Step 3 rule that dependencies come from the task body."""

from __future__ import annotations

from tests.source_paths import skill_source_text


def _step_3_text() -> str:
    body = skill_source_text("dev-loop")
    start = body.index("### Step 3: Pick the Next Task")
    end = body.index("### Step 4:")
    return body[start:end]


def test_step_3_reads_dependencies_from_task_body_at_show_path() -> None:
    step = _step_3_text()
    assert "ai-team show T-NNN --json" in step
    assert "`path`" in step
    assert "## Dependencies" in step
    assert "`completed`" in step


def test_step_3_treats_none_entry_as_no_dependencies() -> None:
    step = _step_3_text()
    assert "- None" in step
    assert "no dependencies" in step


def test_dev_loop_body_does_not_describe_dependencies_as_a_field() -> None:
    body = skill_source_text("dev-loop")
    assert "listed in `dependencies`" not in body
