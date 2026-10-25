"""Tests for T-061: Bug evidence chain across debug, tdd, code-review, new-bug skills.

AC-1: debug skill is diagnosis-only and requires a fix contract in the Diagnosis Log.
AC-2: tdd skill consumes the fix contract as implementation target for bug fixes.
AC-3: code-review returns FAIL when diagnosis->fix evidence chain is missing.
AC-4: code-review body contains the canonical two-stage checklist.
AC-5: new-bug skill requires evidence, source_branch, expected/actual behaviour,
      and fix-verification for integration-filed regression bugs.
"""

from __future__ import annotations

from tests.source_paths import skill_export_path, skill_source_text


def _skill_source(skill_name: str) -> str:
    return skill_source_text(skill_name)


def _skill_export(skill_name: str) -> str:
    return skill_export_path(skill_name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC-1: debug skill is diagnosis-only and requires a fix contract
# ---------------------------------------------------------------------------


def test_debug_skill_is_diagnosis_only() -> None:
    """AC-1: debug body must declare it is diagnosis-only."""
    body = _skill_source("debug")
    assert any(
        phrase in body
        for phrase in (
            "diagnosis-only",
            "diagnosis only",
            "Diagnosis-Only",
            "Diagnosis Only",
        )
    ), "debug source must state it is diagnosis-only"


def test_debug_skill_requires_fix_contract_in_diagnosis_log() -> None:
    """AC-1: debug body must require a fix contract in the Diagnosis Log."""
    body = _skill_source("debug")
    assert "fix contract" in body.lower(), (
        "debug source must require a fix contract in the Diagnosis Log"
    )


def test_debug_skill_fix_contract_includes_isolated_fault() -> None:
    """AC-1: fix contract must include isolated fault."""
    body = _skill_source("debug")
    assert "isolated fault" in body.lower(), (
        "debug source fix contract must include isolated fault"
    )


def test_debug_skill_fix_contract_includes_root_cause() -> None:
    """AC-1: fix contract must include root cause or fault hypothesis."""
    body = _skill_source("debug")
    assert "root cause or fault hypothesis" in body.lower(), (
        "debug source fix contract must include root cause or fault hypothesis"
    )


def test_debug_skill_fix_contract_includes_planned_verification() -> None:
    """AC-1: fix contract must include planned verification."""
    body = _skill_source("debug")
    assert "planned verification" in body.lower(), (
        "debug source fix contract must include planned verification"
    )


def test_debug_skill_stops_before_production_code_change() -> None:
    """AC-1: debug must stop before production code change until fix contract is in the log."""
    body = _skill_source("debug")
    # Must stop after diagnosis — no Step 6 Fix or Step 7 Verify
    assert (
        "do not change production code" in body.lower() or "stop here" in body.lower()
    ), "debug source must instruct the agent to stop before changing production code"


def test_debug_scaffold_includes_fix_contract_phrases() -> None:
    """AC-1: scaffold must reflect the fix contract requirement."""
    scaffold = _skill_export("debug")
    assert "fix contract" in scaffold.lower(), (
        "debug scaffold must include 'fix contract'"
    )


# ---------------------------------------------------------------------------
# AC-2: tdd skill consumes the fix contract as implementation target for bug fixes
# ---------------------------------------------------------------------------


def test_tdd_skill_references_fix_contract_for_bug_fixes() -> None:
    """AC-2: tdd body must mention consuming the fix contract from the Diagnosis Log."""
    body = _skill_source("tdd")
    assert "fix contract" in body.lower(), (
        "tdd source must reference consuming the fix contract as implementation target"
    )


def test_tdd_skill_requires_diagnosis_log_before_implementation() -> None:
    """AC-2: tdd body must require a Diagnosis Log (with fix contract) before coding."""
    body = _skill_source("tdd")
    assert "diagnosis log" in body.lower(), (
        "tdd source must require a Diagnosis Log before writing implementation"
    )


def test_tdd_scaffold_references_fix_contract() -> None:
    """AC-2: tdd scaffold must reflect the fix contract consumption."""
    scaffold = _skill_export("tdd")
    assert "fix contract" in scaffold.lower(), (
        "tdd scaffold must include 'fix contract'"
    )


# ---------------------------------------------------------------------------
# AC-3: code-review returns FAIL when diagnosis->fix evidence chain is missing
# ---------------------------------------------------------------------------


def test_code_review_fails_when_evidence_chain_is_missing() -> None:
    """AC-3: code-review body must return FAIL when diagnosis->fix evidence chain is absent."""
    body = _skill_source("code-review")
    assert "evidence chain" in body.lower(), (
        "code-review source must reference the diagnosis->fix evidence chain"
    )


def test_code_review_does_not_infer_intent_from_diff() -> None:
    """AC-3: code-review must not infer intent from the diff when evidence chain is missing."""
    body = _skill_source("code-review")
    assert "infer" in body.lower() or "evidence chain" in body.lower(), (
        "code-review source must address the case where the reviewer cannot infer intent"
    )


def test_code_review_requires_diagnosis_log_for_bug_fixes() -> None:
    """AC-3: code-review must explicitly require diagnosis log for bug fixes."""
    body = _skill_source("code-review")
    assert "diagnosis" in body.lower(), (
        "code-review source must require checking the Diagnosis Log for bug fixes"
    )


def test_code_review_scaffold_includes_evidence_chain_gate() -> None:
    """AC-3: code-review scaffolds must include evidence chain gate."""
    scaffold = _skill_export("code-review")
    assert "evidence chain" in scaffold.lower(), (
        "code-review scaffold must include evidence chain gate"
    )


# ---------------------------------------------------------------------------
# AC-4: code-review body contains the canonical two-stage checklist
# ---------------------------------------------------------------------------


def test_code_review_contains_stage_1_heading() -> None:
    """AC-4: code-review body must contain a Stage 1 heading."""
    body = _skill_source("code-review")
    assert "stage 1" in body.lower(), (
        "code-review source must contain the Stage 1 checklist"
    )


def test_code_review_contains_stage_2_heading() -> None:
    """AC-4: code-review body must contain a Stage 2 heading."""
    body = _skill_source("code-review")
    assert "stage 2" in body.lower(), (
        "code-review source must contain the Stage 2 checklist"
    )


def test_code_review_contains_bug_fix_addendum() -> None:
    """AC-4: code-review body must contain the Bug Fix Addendum."""
    body = _skill_source("code-review")
    assert "bug fix addendum" in body.lower(), (
        "code-review source must contain the Bug Fix Addendum"
    )


def test_code_review_two_stage_checklist_in_scaffolds() -> None:
    """AC-4: code-review scaffolds must contain the two-stage checklist."""
    scaffold = _skill_export("code-review")
    assert "stage 1" in scaffold.lower(), "code-review scaffold must include Stage 1"
    assert "stage 2" in scaffold.lower(), "code-review scaffold must include Stage 2"
    assert "bug fix addendum" in scaffold.lower(), (
        "code-review scaffold must include Bug Fix Addendum"
    )


# ---------------------------------------------------------------------------
# AC-5: new-bug requires regression evidence fields
# ---------------------------------------------------------------------------


def test_new_bug_requires_source_branch_for_regression_bugs() -> None:
    """AC-5: new-bug body must require source_branch for regression bugs."""
    body = _skill_source("new-bug")
    assert (
        "source_branch" in body
        or "source-branch" in body.lower()
        or "source branch" in body.lower()
    ), "new-bug source must require source_branch for integration-filed regression bugs"


def test_new_bug_requires_expected_and_actual_behaviour() -> None:
    """AC-5: new-bug body must require expected and actual behaviour for regression bugs."""
    body = _skill_source("new-bug")
    assert "expected" in body.lower(), (
        "new-bug source must require expected behaviour for regression bugs"
    )
    assert "actual" in body.lower(), (
        "new-bug source must require actual behaviour for regression bugs"
    )


def test_new_bug_requires_fix_verification_for_regression_bugs() -> None:
    """AC-5: new-bug body must require fix-verification for regression bugs."""
    body = _skill_source("new-bug")
    assert "fix" in body.lower() and "veri" in body.lower(), (
        "new-bug source must require fix-verification for regression bugs"
    )


def test_new_bug_requires_evidence_for_regression_bugs() -> None:
    """AC-5: new-bug body must require evidence for regression bugs."""
    body = _skill_source("new-bug")
    assert "evidence" in body.lower(), (
        "new-bug source must require evidence for integration-filed regression bugs"
    )


def test_new_bug_scaffold_includes_regression_fields() -> None:
    """AC-5: new-bug scaffolds must include regression evidence fields."""
    scaffold = _skill_export("new-bug")
    assert "source_branch" in scaffold or "source branch" in scaffold.lower(), (
        "new-bug scaffold must include source_branch for regression bugs"
    )
    assert "evidence" in scaffold.lower(), (
        "new-bug scaffold must include evidence requirement"
    )
