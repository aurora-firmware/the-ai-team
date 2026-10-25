"""T-088: using-ai-team and brainstorm suggest the system overview when S-000 is absent."""

from __future__ import annotations

import re

from tests.source_paths import skill_source_text

USING = skill_source_text("using-ai-team")
BRAINSTORM = skill_source_text("brainstorm")


def _step_zero_opening_paragraph(body: str) -> str:
    section = body.split("### Step 0: Triage the Scope\n", 1)[1]
    return section.strip().split("\n\n", 1)[0]


def test_using_ai_team_suggests_system_overview_when_no_s000_exists():
    assert "`ai-team list specs`" in USING
    assert "S-000" in USING
    suggestion = USING.split("`ai-team list specs`", 1)[1]
    assert "`new-system-overview`" in suggestion.split("\n\n", 1)[0]


def test_brainstorm_step_zero_opens_with_the_system_overview_suggestion():
    opening = _step_zero_opening_paragraph(BRAINSTORM)

    assert "`ai-team list specs`" in opening
    assert "S-000" in opening
    assert "`new-system-overview`" in opening


def test_brainstorm_keeps_its_step_headings_unchanged():
    headings = re.findall(r"^### Step \d+: .*$", BRAINSTORM, flags=re.MULTILINE)

    assert headings[0] == "### Step 0: Triage the Scope"
    numbers = [int(re.search(r"\d+", heading).group()) for heading in headings]
    assert numbers == list(range(len(numbers)))


def test_both_skills_say_the_human_may_decline_and_it_is_not_repeated():
    for body in (USING, BRAINSTORM):
        assert "declines" in body
        assert "not repeated in the same session" in body


def test_using_ai_team_dispatch_row_for_system_overview_is_unchanged():
    assert (
        "| The project has no S-000, or is being adopted into the ai-team process "
        "| `new-system-overview` |"
    ) in USING


BOOTSTRAP_ROW = (
    "| S-000 is approved and no task names S-000 as its source spec "
    "| Suggest the project bootstrap (`spec-breakdown` on S-000) to the human |"
)


def _bootstrap_paragraph() -> str:
    after_table = USING.split("\n\n")
    return next(p for p in after_table if p.startswith("When S-000 is approved"))


def test_using_ai_team_routes_approved_s000_without_tasks_to_the_bootstrap_suggestion():
    assert BOOTSTRAP_ROW in USING


def test_using_ai_team_bootstrap_suggestion_leaves_the_decision_to_the_human():
    paragraph = _bootstrap_paragraph()

    assert "`spec-breakdown`" in paragraph
    assert "the human decides" in paragraph


def test_using_ai_team_does_not_repeat_the_declined_bootstrap_suggestion():
    paragraph = _bootstrap_paragraph()

    assert "declines" in paragraph
    assert "not repeated in the same session" in paragraph
