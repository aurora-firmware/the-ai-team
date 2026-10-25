"""Issue #31: process practices adopted from the superpowers comparison report.

Each test pins one adopted practice to the skill, template, or guide that owns it,
so a later edit cannot silently drop it.
"""

from __future__ import annotations

from pathlib import Path

from tests.source_paths import agent_source_path, skill_source_text

CLI = Path(__file__).resolve().parents[1]
REPO = CLI.parent


def skill(name: str) -> str:
    return skill_source_text(name)


def agent(name: str) -> str:
    return agent_source_path(name).read_text(encoding="utf-8")


# -- Phase 1: rationalization tables and review calibration ------------------


def test_enforcement_skills_carry_a_rationalizations_table():
    for name in ("tdd", "debug", "integrate", "code-review", "git-conventions"):
        body = skill(name)
        assert "## Rationalizations" in body, name
        section = body.split("## Rationalizations", 1)[1].split("\n## ", 1)[0]
        rows = [line for line in section.splitlines() if line.startswith('| "')]
        assert len(rows) >= 5, name
        assert body.index("## Rationalizations") < body.index("## Common Pitfalls"), (
            name
        )


def test_code_review_defines_severity_and_ties_the_verdict_to_it():
    body = skill("code-review")

    for term in ("**Critical**", "**Important**", "**Minor**"):
        assert term in body
    assert "cannot be trusted until it is fixed" in body
    assert "Critical or Important finding" in body


def test_code_review_does_not_trust_the_report_or_rerun_developer_tests():
    body = skill("code-review")

    assert "unverified claims" in body
    assert "never lowers a finding's severity" in body
    assert "Do not re-run tests the Work Log already shows passing" in body


def test_code_review_has_a_cannot_verify_category_without_a_new_verdict_word():
    body = skill("code-review")

    assert "⚠️ Cannot verify from diff" in body
    assert "Verdict: `PASS`" in body and "Verdict: `FAIL`" in body
    assert "Verdict: `CANNOT" not in body


def test_loops_keep_reviewer_prompts_neutral_and_resolve_unverifiable_items():
    for name in ("dev-loop", "bug-loop"):
        body = skill(name)
        assert "Keep the Reviewer prompt neutral" in body, name
        for phrase in ("do not flag", "at most Minor", "the plan chose"):
            assert phrase in body, (name, phrase)
        assert "Do not re-run tests the Work Log already shows passing" in body, name
        assert "Cannot verify from diff" in body, name
        assert "Deferred Minor findings" in body, name


def test_status_report_rolls_up_deferred_minor_findings_for_gate_5():
    body = skill("status-report")

    assert "Deferred Minor findings" in body
    assert "### Deferred Minor Findings" in body
    assert "silent discard" in body


# -- Phase 2: evidence before claims, context and cost engineering -----------


def test_evidence_skill_has_gate_function_and_common_failures():
    body = skill("evidence-before-claims")

    for step in ("**Identify**", "**Run**", "**Read**", "**Verify**", "**Only then**"):
        assert step in body
    assert "| Claim | Requires | Not sufficient |" in body
    assert "The agent reporting success" in body
    assert "## Rationalizations" in body


def test_every_role_wires_evidence_into_its_output_envelope():
    for role in ("architect", "developer", "integrator", "planner", "reviewer"):
        text = agent(role)
        assert "evidence-before-claims" in text.split("---")[1], role
        assert "evidence-before-claims" in text, role
        assert "its actual output" in text, role


def test_loops_apply_context_and_cost_engineering():
    for name in ("dev-loop", "bug-loop"):
        body = skill(name)
        assert "## Dispatch Discipline" in body, name
        assert "Never paste prior-work-item history into a dispatch" in body, name
        assert "git diff -U10 BASE..HEAD" in body, name
        assert "git rev-parse HEAD" in body and "Base commit:" in body, name
        assert "review-packages" in body, name
        for tier in ("cheap", "standard", "most capable"):
            assert f"| {tier} |" in body, (name, tier)
        assert "**Spawn the Reviewer subagent** (tier: standard)" in body, name
        assert "**Spawn the Architect subagent** (tier: most capable)" in body, name


def test_code_review_reviews_the_whole_range_from_base():
    body = skill("code-review")

    assert "BASE..HEAD" in body
    assert "Never review `HEAD~1` alone" in body


# -- Phase 3: task template, new-task, and the Gate 2 checklist --------------


def test_task_template_has_an_interfaces_block_with_consumes_and_produces():
    template = (CLI / "src" / "ai_team" / "templates" / "task.md").read_text(
        encoding="utf-8"
    )

    assert "## Interfaces" in template
    assert "**Consumes:**" in template and "**Produces:**" in template
    assert template.index("## Dependencies") < template.index("## Interfaces")
    assert template.index("## Interfaces") < template.index("## Files to Touch")


def test_new_task_requires_interfaces_and_bans_placeholders():
    body = skill("new-task")

    assert "**Interface-explicit**" in body
    assert "**No placeholders**" in body
    for banned in ("TBD", "implement later", "similar to Task N", "handle edge cases"):
        assert banned in body


def test_gate_2_checks_interface_consistency_and_placeholders():
    body = skill("spec-breakdown-review")
    gates = (REPO / "ai-process" / "processes" / "quality-gates.md").read_text(
        encoding="utf-8"
    )

    assert "Check Interface Consistency" in body
    assert "match the producing task's **Produces** entry exactly" in body
    assert "Interfaces are consistent across tasks" in gates
    assert "No task contains placeholder text" in gates


def test_owning_spec_records_the_phase_3_amendment_before_the_change():
    spec = (
        REPO
        / "docs"
        / "ai-team"
        / "specs"
        / "archive"
        / "S-002-coordinated-process-and-cli-workflow-improvements.md"
    ).read_text(encoding="utf-8")

    amendment = spec.split("## Amendment Log", 1)[1]
    assert "Interfaces: Consumes / Produces" in amendment
    assert "#31" in amendment


# -- Phase 4: capability ladder, scope triage, section approval --------------


def test_loops_climb_a_capability_ladder_before_consulting_the_architect():
    for name, kind in (("dev-loop", "task"), ("bug-loop", "bug")):
        body = skill(name)
        on_fail = body.split("#### On FAIL", 1)[1].split("#### On ESCALATE", 1)[0]
        assert "same Developer" in on_fail, name
        assert "fresh Developer subagent on the most capable tier" in on_fail, name
        assert "before any Architect consultation is spent" in on_fail, name
        assert f"Pass only the {kind} file path" in on_fail, name
        assert on_fail.index("cycle = 1") < on_fail.index("cycle = 2"), name
        assert on_fail.index("cycle = 2") < on_fail.index("cycle = 3"), name


def test_parked_findings_must_become_durable_artifacts():
    for name in ("dev-loop", "bug-loop"):
        body = skill(name)
        escalate = body.split("#### On ESCALATE", 1)[1]
        assert "**parked**" in escalate, name
        assert "file it as a new bug" in escalate, name
        assert "### Recorded deviation" in escalate, name
        assert "a ledger line in the chat is not one" in escalate, name


def test_brainstorm_triages_scope_before_asking_questions():
    body = skill("brainstorm")

    assert body.index("### Step 0: Triage the Scope") < body.index("### Step 1")
    assert "independent subsystems" in body
    assert "brainstorm only the first sub-project" in body


def test_brainstorm_approves_the_design_section_by_section():
    body = skill("brainstorm")
    step6 = body.split("### Step 6", 1)[1].split("### Step 7", 1)[0]

    assert "Section by Section" in body
    assert (
        "Stop and wait for the human's answer before presenting the next section"
        in step6
    )
    assert '"no exclusions apply"' in step6
    assert "Lead with your recommended option" in body
    assert "Prefer multiple-choice questions" in body


# -- Phase 5: spec-truth reconciliation at Gate 5 ----------------------------


def test_adr_002_records_the_reconciliation_decision():
    adrs = list((REPO / "docs" / "ai-team" / "decisions").glob("ADR-002-*.md"))

    assert len(adrs) == 1
    text = adrs[0].read_text(encoding="utf-8")
    assert "status: accepted" in text
    assert "ADR-000" not in text and "[Decision Title]" not in text
    for heading in ("## Context", "## Decision", "## Consequences"):
        assert heading in text
    assert "architecture-consistency-review" in text


def test_consistency_review_gains_a_completion_trigger_that_routes_by_authoritative_side():
    body = skill("architecture-consistency-review")

    assert "## Completion Mode" in body
    assert "spec-truth reconciliation" in body
    assert "Work Logs" in body and "deferred-Minor" in body
    assert (
        "Routing** first decides, for each drift, which side is authoritative" in body
    )
    assert "the Planner amends the approved spec" in body
    assert "the Planner creates follow-up tasks with `new-task`" in body
    assert "Never amend a spec to match work that fell short" in body
    assert (
        "**The authoritative side is unclear**, or both sides need to change → escalate to the human"
        in body
    )
    assert "Follow-up tasks are created `pending` and are exempt from Gate 2" in body
    assert "The Planner chooses each follow-up task's verification mode" in body
    assert "escalate to the human instead of routing another round" in body
    assert (
        "A completion-mode amendment of a stale spec is a `FAIL` routed to the Planner"
        in body
    )
    assert (
        "or a follow-up task routed by spec-truth reconciliation, which is exempt"
        in skill("using-ai-team")
    )


def test_gate_5_requires_the_reconciliation_result():
    gates = (REPO / "ai-process" / "processes" / "quality-gates.md").read_text(
        encoding="utf-8"
    )
    gate_5 = gates.split("## Gate 5", 1)[1]

    assert "spec-truth reconciliation" in gate_5
    assert "returned `PASS`, or every correction it routed is done" in gate_5
    assert "each follow-up task completed with a re-run that returns `PASS`" in gate_5
    gate_2 = gates.split("## Gate 2", 1)[1].split("## Gate 3", 1)[0]
    assert "Follow-up tasks routed by spec-truth reconciliation are exempt" in gate_2
    assert "ADR-002" in gates


def test_status_report_and_loops_point_at_the_reconciliation():
    assert "Spec-Truth Reconciliation" in skill("status-report")
    for name in ("dev-loop", "bug-loop"):
        assert "spec-truth reconciliation" in skill(name), name
    assert "completion mode" in agent("architect")


# -- Phase 6: TDD for skills --------------------------------------------------


def test_skill_testing_guide_defines_the_cycle_and_is_linked_from_the_template():
    guide = (REPO / "guides" / "skill-testing-guide.md").read_text(encoding="utf-8")
    template = (REPO / "guides" / "skill_template.md").read_text(encoding="utf-8")

    for phrase in (
        "Write the test first",
        "Watch it fail (RED)",
        "Watch it pass (GREEN)",
        "pressure scenario",
        "rationalizations",
        "never lists the steps",
    ):
        assert phrase in guide, phrase
    assert "guides/skill-testing-guide.md" in template
    assert "never list the steps" in template


def test_evidence_rule_allows_cited_and_artifact_proof():
    body = skill("evidence-before-claims")
    assert "per Work Log session N" in body
    assert (
        "whenever the proof is an artifact read, not a command run"
        in body.split("### Step 3", 1)[1].split("## Output Format", 1)[0]
    )
    for role in ("reviewer", "architect", "planner"):
        assert "evidence-before-claims" in agent(role), role
    assert "per Work Log session N" in agent("reviewer")
