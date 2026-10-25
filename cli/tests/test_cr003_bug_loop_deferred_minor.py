"""CR-003 section 3: bug-loop promotes a deferred Minor that proves a real failure."""

from __future__ import annotations

from tests.source_paths import skill_export_path, skill_source_text

COPIES = {
    "source": skill_source_text("bug-loop"),
    "export": skill_export_path("bug-loop").read_text(encoding="utf-8"),
}


def on_pass_section(text: str) -> str:
    start = text.index("#### On PASS")
    end = text.index("#### On FAIL")
    return text[start:end]


def test_on_pass_treats_a_deferred_minor_that_is_a_real_failure_as_fail():
    for name, text in COPIES.items():
        section = on_pass_section(text)
        assert "deferred Minor finding" in section, name
        assert "breaks CI" in section, name
        assert "contradicts the bug's fix contract" in section, name
        assert "treat the verdict as FAIL for that item" in section, name


def test_on_pass_names_promotion_as_the_same_handling_as_cannot_verify():
    for name, text in COPIES.items():
        section = on_pass_section(text)
        assert "same handling as an unconfirmable" in section, name
        assert "`⚠️ Cannot verify from diff`" in section, name


def test_on_pass_appends_resolved_marker_to_the_promoted_deferred_entry():
    for name, text in COPIES.items():
        section = on_pass_section(text)
        assert "`#### Deferred Minor findings`" in section, name
        assert "` — resolved: promoted to FAIL`" in section, name
