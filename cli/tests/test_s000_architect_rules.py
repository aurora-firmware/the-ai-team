"""T-094: the Architect reads S-000 at session start and uses it as the consistency-check reference."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.source_paths import agent_source_path

ARCHITECT_SOURCES = [pytest.param(agent_source_path("architect"), id="claude")]

NON_ARCHITECT_ROLES = ["developer", "reviewer", "integrator"]
DEVELOPER_BOOTSTRAP_EXCEPTION = "a task whose source spec is S-000"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    return " ".join(_text(path).split())


@pytest.mark.parametrize("path", ARCHITECT_SOURCES)
def test_architect_reads_approved_s000_at_session_start_before_other_specs(path):
    text = _flat(path)

    assert "reads S-000 at the start of a session" in text
    assert "exists and is approved" in text
    assert "before other specs" in text


@pytest.mark.parametrize("path", ARCHITECT_SOURCES)
def test_architect_uses_s000_as_reference_for_the_consistency_check(path):
    text = _flat(path)

    assert "uses it as the reference" in text
    assert "`architecture-consistency-review` skill" in text
    assert "check itself is owned by" in text


@pytest.mark.parametrize("role", NON_ARCHITECT_ROLES)
def test_non_architect_roles_do_not_mention_s000(role):
    text = _text(agent_source_path(role))
    if role == "developer":
        assert text.count(DEVELOPER_BOOTSTRAP_EXCEPTION) == 1
        text = text.replace(DEVELOPER_BOOTSTRAP_EXCEPTION, "")

    assert "S-000" not in text
