"""Issue #29: the using-ai-team meta-skill."""

from __future__ import annotations

import re

from tests.source_paths import (
    SKILL_SOURCES,
    skill_export_path,
    skill_frontmatter,
    skill_source_text,
)

BODY = skill_source_text("using-ai-team")


def test_dispatch_table_names_only_existing_skills():
    existing = {path.name for path in SKILL_SOURCES.iterdir() if path.is_dir()}
    table_rows = [line for line in BODY.splitlines() if line.startswith("| ")]
    named = {
        name for row in table_rows[1:] for name in re.findall(r"`([a-z][a-z-]+)`", row)
    }

    assert named
    assert named <= existing, named - existing


def test_every_process_skill_is_reachable_from_the_dispatch_table():
    entry_points = {
        "brainstorm",
        "change-request",
        "architecture-consistency-review",
        "spec-breakdown",
        "spec-breakdown-review",
        "tdd",
        "debug",
        "code-review",
        "integrate",
        "merge-conflicts",
        "escalation-review",
        "new-spec",
        "new-task",
        "new-bug",
        "new-adr",
        "git-conventions",
        "status-report",
    }

    for name in entry_points:
        assert f"`{name}`" in BODY, name


def test_frontmatter_matches_skill_authoring_rules():
    header = skill_frontmatter("using-ai-team")

    assert "name: using-ai-team" in header
    description = re.search(r"^description: (.+)$", header, re.MULTILINE)
    assert description and len(description.group(1)) <= 1024
    assert not re.match(r"(I|You) ", description.group(1))
    assert "disable-model-invocation" not in header


def test_scaffold_is_generated_from_the_skill_body():
    skill = skill_export_path("using-ai-team")
    assert skill.read_text(encoding="utf-8").endswith(BODY)
