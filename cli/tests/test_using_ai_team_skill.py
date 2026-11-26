"""Issue #29: the using-ai-team meta-skill."""

from __future__ import annotations

import re

from tests.source_paths import (
    skill_export_path,
    skill_frontmatter,
    skill_source_text,
)

BODY = skill_source_text("using-ai-team")


def test_frontmatter_matches_skill_authoring_rules():
    header = skill_frontmatter("using-ai-team")

    assert "name: using-ai-team" in header
    description = re.search(r"^description: (.+)$", header, re.MULTILINE)
    assert description and len(description.group(1)) <= 1024


def test_scaffold_is_generated_from_the_skill_body():
    skill = skill_export_path("using-ai-team")
    assert skill.read_text(encoding="utf-8").endswith(BODY)
