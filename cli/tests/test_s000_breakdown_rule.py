"""spec-breakdown plans only the bootstrap tasks from S-000."""

from __future__ import annotations

import re
from pathlib import Path

from tests.source_paths import skill_source_text

EXPECTED_HEADINGS = [
    "# Write Plan",
    "## Input Requirements",
    "## Procedure",
    "### Step 0: Check Out the Planning Branch",
    "### Step 1: Identify Components",
    "### Step 2: Define Dependencies",
    "### Step 3: Write Task Files",
    "### Step 4: Validate the Plan",
    "### Step 5: Place Tasks",
    "### Step 6: Architect Preflight",
    "### Step 7: Merge the Planning Branch and Activate the Tasks",
    "## Output Format",
    "## Quality Criteria",
    "## Common Pitfalls",
]


def _body() -> str:
    return skill_source_text("spec-breakdown")


def _section(heading: str) -> str:
    """Return the text under `heading` up to the next heading of any level."""
    body = _body()
    start = body.index(heading) + len(heading)
    following = re.search(r"^#{1,3} ", body[start:], flags=re.MULTILINE)
    end = start + following.start() if following else len(body)
    return body[start:end]


def test_input_requirements_accept_s000_for_bootstrap_tasks_only():
    section = _section("## Input Requirements")

    assert "S-000" in section
    assert "bootstrap tasks only" in section
    assert "development-infrastructure components" in section


def test_step_zero_plans_only_bootstrap_tasks_when_the_spec_is_s000():
    section = _section("### Step 0: Check Out the Planning Branch")
    first_paragraph = section.strip().split("\n", 1)[0]

    assert "S-000" in first_paragraph
    assert "only the project bootstrap tasks" in first_paragraph
    assert "development-infrastructure components" in first_paragraph
    assert section.index("S-000") < section.index("check it out")


def test_solution_work_from_s000_is_refused_naming_the_feature_specs():
    section = _section("### Step 0: Check Out the Planning Branch")

    assert "solution work" in section
    assert "refuse" in section
    assert "feature specs" in section
    assert "ai-team list specs" in section


def test_bootstrap_outputs_are_listed():
    section = _section("### Step 0: Check Out the Planning Branch")

    for output in (
        "Decisions needed",
        "docs/development/architecture.md",
        "tech-stack.md",
        "environment configuration",
        "remote access check",
        "coding guidelines",
        "internal documentation placeholders",
        "project guidance",
        "README",
    ):
        assert output in section, output


def test_documentation_location_rule_lets_project_rules_win_and_records_location():
    section = _section("### Step 0: Check Out the Planning Branch")

    assert "repository root" in section
    assert "project's rules" in section
    assert "location" in section
    assert "project guidance" in section


def test_brownfield_bootstrap_plans_only_missing_items():
    section = _section("### Step 0: Check Out the Planning Branch")

    assert "brownfield" in section
    assert "only the missing items" in section


def test_bootstrap_plan_goes_through_gate_two():
    assert "Gate 2" in _section("### Step 0: Check Out the Planning Branch")


def test_skill_no_longer_states_the_cli_refuses_task_new_for_s000():
    body = _body()

    assert "refuses `ai-team task new --spec S-000`" not in body
    assert "CLI also refuses" not in body
    assert "refused by the CLI" not in body


def test_common_pitfalls_list_planning_solution_work_from_s000():
    section = _section("## Common Pitfalls")

    assert "S-000" in section
    assert "solution work" in section


def test_step_headings_are_unchanged_with_exactly_one_step_zero():
    headings = re.findall(r"^#{1,3} .*$", _body(), flags=re.MULTILINE)

    assert headings == EXPECTED_HEADINGS
    assert sum(h.startswith("### Step 0") for h in headings) == 1


def test_gate2_coverage_for_s000_is_the_bootstrap_scope():
    """Gate 2 coverage for S-000 covers the bootstrap scope only, in every rule text."""
    repo = Path(__file__).resolve().parents[2]
    review = skill_source_text("spec-breakdown-review")
    gates = (repo / "ai-process" / "processes" / "quality-gates.md").read_text(
        encoding="utf-8"
    )
    for text in (review, gates):
        assert "For S-000, coverage means the bootstrap scope only" in text
        assert "S-000's solution components never need tasks" in text
    body = _body()
    assert "For S-000, the bootstrap scope only (Step 0)." in body
    assert "(for S-000, its bootstrap scope; see Step 0)" in body
