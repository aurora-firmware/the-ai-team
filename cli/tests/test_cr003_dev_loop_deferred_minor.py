"""CR-003 section 3: dev-loop promotes a deferred Minor that proves a real failure."""

from __future__ import annotations

import re

from tests.source_paths import skill_export_path, skill_source_text

COPIES = {
    "source": skill_source_text("dev-loop"),
    "export": skill_export_path("dev-loop").read_text(encoding="utf-8"),
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
        assert "contradicts the task" in section, name
        assert "treat the verdict as FAIL for that item" in section, name


def test_on_pass_names_promotion_as_the_same_handling_as_cannot_verify():
    for name, text in COPIES.items():
        section = on_pass_section(text)
        assert "same handling as an unconfirmable" in section, name
        assert "`⚠️ Cannot verify from diff`" in section, name


def test_on_pass_appends_resolved_marker_to_the_promoted_deferred_entry():
    for name, text in COPIES.items():
        section = on_pass_section(text)
        marker = "` — resolved: promoted to FAIL`"
        sentences = re.split(r"(?<=\.)\s+", section)
        marker_sentences = [s for s in sentences if marker in s]
        assert len(marker_sentences) == 1, name
        assert "append" in marker_sentences[0], name
        assert "`#### Deferred Minor findings`" in marker_sentences[0], name
