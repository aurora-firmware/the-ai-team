"""CR-003: the skill template guide documents supporting-folder export and placeholders."""

from __future__ import annotations

import re
from pathlib import Path

GUIDE = Path(__file__).resolve().parents[2] / "guides" / "skill_template.md"


def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def export_rules_text() -> str:
    text = guide_text()
    heading = "### Export Rules for Skills in This Repository"
    start = text.index(heading) + len(heading)
    following = re.search(r"^#{1,3} ", text[start:], flags=re.MULTILINE)
    end = start + following.start() if following else len(text)
    return " ".join(text[start:end].split())


def test_guide_does_not_point_to_missing_new_task_template() -> None:
    assert "new-task/assets/TEMPLATE-task.md" not in guide_text()


def test_guide_states_a_source_skill_is_one_skill_md_with_supporting_folders() -> None:
    text = export_rules_text()
    assert "one `SKILL.md`" in text
    assert "`assets/`, `references/` and `scripts/` folders" in text
    assert "cli/src/ai_team/init/sources/skills/<name>/" in text


def test_guide_states_supporting_folders_reach_the_export_next_to_skill_md() -> None:
    text = export_rules_text()
    assert "reach the export" in text
    assert "next to `SKILL.md`" in text


def test_guide_has_no_codex_or_two_file_skill_text() -> None:
    text = guide_text().lower()
    for removed in ("codex", "metadata.toml", "body.md"):
        assert removed not in text


def test_guide_keeps_the_disable_model_invocation_rules() -> None:
    text = guide_text()
    assert "`disable-model-invocation`:" in text
    assert "human-only actions" in text


def test_guide_states_placeholder_filling_and_byte_copy_rules() -> None:
    text = export_rules_text()
    assert "`{{project_dir}}`" in text
    assert "`{{integration_branch}}`" in text
    assert "not UTF-8 text" in text
    assert "byte for byte" in text
