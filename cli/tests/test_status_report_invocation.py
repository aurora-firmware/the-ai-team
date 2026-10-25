"""Regression coverage for model-invocable skill-to-skill targets."""

from __future__ import annotations

import re

from tests.source_paths import (
    SKILL_SOURCES,
    skill_export_path,
    skill_frontmatter,
    skill_source_text,
)

SKILL_INVOCATION = re.compile(r"Skill\(([^)]+)\)")
MODEL_INVOCATION_DISABLED = re.compile(
    r"^disable-model-invocation:\s*true\s*$", re.MULTILINE
)


def test_skill_invocation_targets_allow_model_invocation() -> None:
    """A skill named in Skill(...) must be callable by the invoking model."""
    for skill_dir in sorted(SKILL_SOURCES.iterdir()):
        caller_header = skill_frontmatter(skill_dir.name)
        for target_name in SKILL_INVOCATION.findall(caller_header):
            target_header = skill_frontmatter(target_name)
            assert not MODEL_INVOCATION_DISABLED.search(target_header), (
                f"{skill_dir.name} invokes {target_name}, but "
                "the target disables model invocation"
            )


def test_status_report_is_human_invoked_only_in_generated_scaffolds() -> None:
    """Reporting is on demand: generated status-report skills disable model invocation."""
    content = skill_export_path("status-report").read_text(encoding="utf-8")
    assert MODEL_INVOCATION_DISABLED.search(content), (
        "status-report scaffold must disable model invocation"
    )


def test_loops_end_with_run_summary_instead_of_status_report() -> None:
    """Both loops route an empty queue to Step 8, which returns a chat summary only."""
    for loop_name in ("dev-loop", "bug-loop"):
        body = skill_source_text(loop_name)
        queue_step = body.split("### Step 1: Check the Queue", 1)[1].split(
            "### Step 2:", 1
        )[0]
        loop_complete = body.split("### Step 8: Loop Complete", 1)[1].split("\n## ", 1)[
            0
        ]
        assert "Skill(status-report)" not in skill_frontmatter(loop_name), (
            f"{loop_name} must not be allowed to invoke status-report"
        )
        assert "proceed directly to **Step 8: Loop Complete**" in queue_step, (
            f"{loop_name} does not route an empty full queue to Step 8"
        )
        assert "invoke `Skill(status-report)`" not in body, (
            f"{loop_name} still invokes status-report automatically"
        )
        assert "Do not invoke the `status-report` skill" in loop_complete
        assert "run summary" in loop_complete
        assert "Workspace Hygiene" in loop_complete, (
            f"{loop_name} must check the workspace before it ends"
        )
