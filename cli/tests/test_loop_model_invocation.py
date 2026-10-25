"""Loops stay model-invocable so a human can delegate them to an agent."""

from __future__ import annotations

import re
from pathlib import Path

from tests.source_paths import skill_export_path, skill_frontmatter, skill_source_text

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_GUIDE = REPO_ROOT / "guides" / "skill_template.md"
LOOP_SENTENCES = {
    "dev-loop": "Use only when the human asks to run the development loop.",
    "bug-loop": "Use only when the human asks to run the bug-fix loop.",
}
FLAG = "disable-model-invocation"


def _source_header(skill: str) -> str:
    return skill_frontmatter(skill)


def _scaffold_header(skill: str) -> str:
    text = skill_export_path(skill).read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[0]


def _description(header: str) -> str:
    match = re.search(r"^description:\s*(.*)$", header, re.MULTILINE)
    assert match, "header has no description"
    return match.group(1).strip()


def test_loop_headers_do_not_disable_model_invocation_in_sources() -> None:
    for skill in LOOP_SENTENCES:
        assert FLAG not in _source_header(skill), f"{skill} source carries {FLAG}"


def test_loop_headers_do_not_disable_model_invocation_in_scaffolds() -> None:
    for skill in LOOP_SENTENCES:
        assert FLAG not in _scaffold_header(skill), f"{skill} scaffold carries {FLAG}"


def test_loop_descriptions_end_with_explicit_human_request_sentence() -> None:
    for skill, sentence in LOOP_SENTENCES.items():
        for header in (_source_header(skill), _scaffold_header(skill)):
            assert _description(header).endswith(sentence), skill


def test_bug_loop_description_no_longer_invites_auto_selection() -> None:
    for header in (_source_header("bug-loop"), _scaffold_header("bug-loop")):
        assert "Use this whenever there are open bugs to fix" not in header


def test_skill_guide_describes_orchestrators_as_model_invocable() -> None:
    guide = SKILL_GUIDE.read_text(encoding="utf-8")
    assert "Usually carry `disable-model-invocation: true`" not in guide
    assert (
        "typically declare `Agent` in `allowed-tools` (to spawn subagents) and"
        not in guide
    )
    assert "stay model-invocable" in guide
    assert "using-ai-team" in guide
    orchestrator_yaml = guide.split("### Frontmatter", 1)[1].split("###", 1)[0]
    assert FLAG not in orchestrator_yaml.split("```yaml", 1)[1]


def test_skill_guide_checklist_does_not_expect_flag_on_orchestrators() -> None:
    guide = SKILL_GUIDE.read_text(encoding="utf-8")
    checklist = [
        ln for ln in guide.splitlines() if ln.startswith("- [ ] `disable-model")
    ]
    assert checklist and "human-only" in checklist[0]


def test_using_ai_team_rule_and_status_report_flag_unchanged() -> None:
    body = skill_source_text("using-ai-team")
    assert (
        "`dev-loop` and `bug-loop` start only when the human invokes them. "
        "Never start either on your own."
    ) in body
    assert f"{FLAG}: true" in _source_header("status-report")
