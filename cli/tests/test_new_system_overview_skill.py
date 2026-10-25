"""T-086: the new-system-overview skill and its dispatch-table row."""

from __future__ import annotations

from tests.source_paths import skill_frontmatter, skill_source_text


def _body() -> str:
    return skill_source_text("new-system-overview")


def test_skill_source_has_body_and_frontmatter_naming_the_skill():
    assert _body().strip()
    assert "name: new-system-overview" in skill_frontmatter("new-system-overview")


def test_body_runs_overview_command_and_names_all_seven_sections():
    body = _body()

    assert "ai-team spec new --overview --json" in body
    assert "ai-team list specs" in body
    for section in (
        "Purpose",
        "Users",
        "Pain points",
        "Use cases",
        "Solution overview",
        "Components",
        "Project exclusions",
    ):
        assert section in body, section


def test_body_carries_section_contract_without_framework_repo_paths():
    # Consuming projects receive skills but not guides/ or ai-process/.
    body = _body()

    assert "## Section contract" in body
    assert "Boundary rule" in body
    assert "no technology choices" in body
    assert "boundary (what it is not responsible for)" in body
    assert "guides/" not in body
    assert "ai-process/" not in body


def test_body_has_checklist_and_architect_then_human_gate_handoff():
    body = _body()

    assert "Pre-submission checklist" in body
    assert "[TODO]" in body
    assert "Architect" in body
    assert "Gate 1" in body
    assert body.index("Architect") < body.rindex("Gate 1")


def test_body_has_brownfield_section_reporting_findings_without_amending():
    body = _body()

    assert "## Brownfield adoption" in body
    brownfield = body.split("## Brownfield adoption", 1)[1]
    assert "finding" in brownfield
    assert "never amend" in brownfield.lower()


def test_dispatch_table_names_new_system_overview():
    body = skill_source_text("using-ai-team")
    rows = [line for line in body.splitlines() if line.startswith("| ")]

    assert any("`new-system-overview`" in row for row in rows)


def _section(body: str, heading: str) -> str:
    return body.split(heading, 1)[1].split("\n## ", 1)[0]


def test_section_contract_states_component_definition_groups_and_decisions_needed():
    contract = _section(_body(), "## Section contract")

    assert "A component is a part of the software solution" in contract
    assert "three checks" in contract
    assert "### Solution" in contract
    assert "### Development infrastructure" in contract
    assert "**Decisions needed**" in contract
    assert "never answers them" in contract


def test_interview_and_checklist_cover_component_split_and_decisions_needed():
    body = _body()
    procedure = _section(body, "## Procedure")
    checklist = _section(body, "## Pre-submission checklist")

    assert "solution and development-infrastructure components" in procedure
    assert "decisions needed" in procedure
    assert "Solution and Development infrastructure" in checklist
    assert "Decisions needed" in checklist


def test_brownfield_derives_components_from_use_cases_not_code_layout():
    brownfield = _section(_body(), "## Brownfield adoption")

    assert "derive the components from the use cases" in brownfield
    assert "never from the code or folder layout" in brownfield
    assert "three component checks" in brownfield


def test_steps_after_gate_1_approve_merge_propose_change_request_and_bootstrap():
    body = _body()
    after_gate = _section(body, "## After Gate 1")

    assert "`approved`" in after_gate
    assert "`--no-ff`" in after_gate
    assert "{{integration_branch}}" in after_gate
    assert "`git-conventions`" in after_gate
    assert "change request" in after_gate
    assert "`change-request`" in after_gate
    assert "`spec-breakdown`" in after_gate
    assert "S-000" in after_gate
    assert after_gate.index("`approved`") < after_gate.index("`--no-ff`")
    assert after_gate.index("`--no-ff`") < after_gate.index("`spec-breakdown`")
