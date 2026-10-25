"""CR-003 section 4: integrate run context and design-review lookup."""

from __future__ import annotations

from tests.source_paths import skill_export_path, skill_source_text

COPIES = {
    "source": skill_source_text("integrate"),
    "claude": skill_export_path("integrate").read_text(encoding="utf-8"),
}


def section(text: str, start_heading: str, end_heading: str) -> str:
    start = text.index(start_heading)
    return text[start : text.index(end_heading, start)]


def test_step_4_runs_each_line_from_repository_root_in_a_fresh_shell():
    for name, text in COPIES.items():
        step = section(text, "### Step 4:", "### Step 5:")
        assert "from the repository root in a fresh shell" in step, name
        assert "independently of the other lines" in step, name
        assert "changes into it on that line" in step, name
        assert "never run as one script" in step, name


def test_step_6_applies_the_same_run_context_to_destination_commands():
    for name, text in COPIES.items():
        step = section(text, "### Step 6:", "#### All Tests Pass")
        assert "same run context as Step 4" in step, name


def test_step_2_item_7_skips_design_review_line_and_uses_project_guidance():
    for name, text in COPIES.items():
        step = section(
            text, "7. Determine the source-branch", "8. Determine the destination"
        )
        bullets = [line for line in step.splitlines() if "`Design review:`" in line]
        assert len(bullets) == 1, name
        bullet = bullets[0]
        assert "no automated command" in bullet, name
        assert "Gate 3" in bullet, name
        assert "Skip it" in bullet, name
        assert "from project guidance" in bullet, name


def test_step_5_shows_merge_command_with_second_m_argument_for_trailers():
    for name, text in COPIES.items():
        step = section(text, "### Step 5:", "### Step 6:")
        assert (
            'git merge --no-ff <source-branch> -m "chore(<kind>): merge '
            '<work-item-id> <short-description>" -m "<trailer lines>"'
        ) in step, name
        assert "commit conventions require trailers" in step, name


def test_step_5_states_git_merge_does_not_read_message_from_stdin():
    for name, text in COPIES.items():
        step = section(text, "### Step 5:", "### Step 6:")
        assert "does not read a message from stdin" in step, name
        assert "`-F -` fails" in step, name


def test_step_5_keeps_single_m_merge_command_valid_without_required_trailers():
    for name, text in COPIES.items():
        step = section(text, "### Step 5:", "### Step 6:")
        single = (
            'git merge --no-ff <source-branch> -m "chore(<kind>): merge '
            '<work-item-id> <short-description>"\n'
        )
        assert single in step, name
        assert "Without required trailers" in step, name
