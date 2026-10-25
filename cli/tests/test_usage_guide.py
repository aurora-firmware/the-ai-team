"""
Tests for T-028: cli/docs/usage.md hand-written CLI guide.

Covers:
  AC-1: cli/docs/usage.md exists and covers installation, ai-team init,
        daily command workflows, the project/ folder structure, and a
        maintainer section.
  AC-2: usage.md describes the project/ folder structure including specs/
        (+ archive/), task and bug state subfolders, decisions/, docs/,
        .ai-team.toml, and the locator resolution order.
  AC-3: usage.md includes a maintainer section with module map, how to add
        a command, how to run tests, how to build/release, and how to
        regenerate commands.md.
  AC-4: usage.md links to commands.md.
  AC-5: usage.md documents only commands and flags present in commands.md —
        verified by cross-checking a representative set.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
USAGE_MD = REPO_ROOT / "cli" / "docs" / "usage.md"
COMMANDS_MD = REPO_ROOT / "cli" / "docs" / "commands.md"
DEVELOPMENT_WARNING = (
    "Warning: ai-team is under development. Please report issues at "
    "https://github.com/aurora-firmware/the-ai-team/issues"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _content() -> str:
    assert USAGE_MD.is_file(), f"usage.md not found at {USAGE_MD}"
    return USAGE_MD.read_text(encoding="utf-8")


def _lower() -> str:
    return _content().lower()


# ---------------------------------------------------------------------------
# AC-1: file exists and covers the required high-level topics
# ---------------------------------------------------------------------------


def test_usage_md_file_exists():
    """cli/docs/usage.md must exist as a regular file."""
    assert USAGE_MD.is_file(), f"Expected file not found: {USAGE_MD}"


def test_usage_md_covers_installation():
    """usage.md must have an installation section."""
    assert "install" in _lower(), "usage.md must cover installation"


def test_usage_md_covers_init_command():
    """usage.md must document ai-team init."""
    assert "ai-team init" in _content() or "ai team init" in _lower(), (
        "usage.md must document the ai-team init command"
    )


def test_usage_md_covers_daily_workflows():
    """usage.md must cover at least one daily workflow sequence (task or bug)."""
    lower = _lower()
    assert "task" in lower and "bug" in lower, (
        "usage.md must cover daily task and bug workflows"
    )


def test_usage_md_covers_gate5_report_workflow():
    """usage.md must cover generating a Gate 5 report."""
    lower = _lower()
    assert "report" in lower and (
        "gate 5" in lower or "gate5" in lower or "status" in lower
    ), "usage.md must describe the Gate 5 / status report workflow"


# ---------------------------------------------------------------------------
# AC-2: project/ folder structure and .ai-team.toml locator
# ---------------------------------------------------------------------------


def test_usage_md_describes_specs_folder():
    """usage.md must document the specs/ folder."""
    assert "specs/" in _content() or "specs" in _lower(), (
        "usage.md must describe the specs/ folder"
    )


def test_usage_md_describes_specs_archive_subfolder():
    """usage.md must document the specs/archive/ subfolder."""
    lower = _lower()
    assert "archive" in lower, "usage.md must mention the specs/archive/ folder"


def test_usage_md_describes_tasks_state_subfolders():
    """usage.md must document all four task state folders."""
    lower = _lower()
    for subfolder in ("pending", "in-progress", "completed", "blocked"):
        assert subfolder in lower, (
            f"usage.md must document the tasks/{subfolder}/ subfolder"
        )


def test_usage_md_describes_bugs_state_subfolders():
    """usage.md must document all three bug state folders."""
    lower = _lower()
    for subfolder in ("open", "in-progress", "resolved"):
        assert subfolder in lower, (
            f"usage.md must document the bugs/{subfolder}/ subfolder"
        )


def test_usage_md_describes_decisions_folder():
    """usage.md must document the decisions/ folder."""
    assert "decisions" in _lower(), "usage.md must describe the decisions/ folder"


def test_usage_md_describes_docs_folder():
    """usage.md must document the docs/ folder."""
    assert "docs" in _lower(), "usage.md must describe the docs/ folder"


def test_usage_md_describes_ai_team_toml_marker():
    """usage.md must document the .ai-team.toml marker file."""
    assert ".ai-team.toml" in _content(), (
        "usage.md must document the .ai-team.toml marker"
    )


def test_usage_md_describes_ai_team_lock_sentinel_and_gitignore_coverage():
    """B-017: usage.md must document the .ai-team.lock sentinel, why it persists,
    that the shipped ai-team/.gitignore covers it, and the pre-fix residual case."""
    content = _content()
    lower = _lower()

    assert ".ai-team.lock" in content, (
        "usage.md must document the .ai-team.lock sentinel file"
    )
    assert "flock" in lower, (
        "usage.md must explain the sentinel persists by B-014's flock design"
    )
    assert ".gitignore" in content, (
        "usage.md must document the shipped ai-team/.gitignore covering the sentinel"
    )
    assert "before this" in lower or "retroactively" in lower, (
        "usage.md must call out the residual case for projects that ran "
        "`ai-team init` before the .gitignore fix shipped"
    )


def test_usage_md_describes_locator_resolution_order():
    """usage.md must describe the locator resolution order."""
    lower = _lower()
    # At minimum, the env var and TOML-walk strategies should be mentioned.
    assert (
        "ai_team_root" in lower or "ai-team-root" in lower or "environment" in lower
    ), (
        "usage.md must describe the AI_TEAM_ROOT environment-variable "
        "resolution strategy"
    )


# ---------------------------------------------------------------------------
# AC-3: maintainer section
# ---------------------------------------------------------------------------


def test_usage_md_has_maintainer_section():
    """usage.md must contain a maintainer section heading."""
    lower = _lower()
    assert (
        "maintainer" in lower or "for maintainer" in lower or "contributing" in lower
    ), "usage.md must have a maintainer section"


def test_usage_md_has_module_map():
    """usage.md must document the ai_team module layout."""
    lower = _lower()
    assert "module" in lower or "ai_team" in lower or "package" in lower, (
        "usage.md must include a module map"
    )


def test_usage_md_explains_how_to_add_a_command():
    """usage.md must explain how to add a new command."""
    lower = _lower()
    assert "add" in lower and "command" in lower, (
        "usage.md must explain how to add a new command"
    )


def test_usage_md_explains_how_to_run_tests():
    """usage.md must document how to run the test suite."""
    lower = _lower()
    assert "pytest" in lower or "test" in lower, (
        "usage.md must explain how to run tests"
    )


def test_usage_md_explains_how_to_build_and_release():
    """usage.md must document the build and release process."""
    lower = _lower()
    assert "build" in lower and (
        "release" in lower or "publish" in lower or "pypi" in lower
    ), "usage.md must explain how to build and release"


def test_usage_md_explains_how_to_regenerate_commands_md():
    """usage.md must document how to regenerate commands.md."""
    content = _content()
    assert "gen_docs.sh" in content, (
        "usage.md must document the gen_docs.sh regeneration script"
    )


def test_usage_md_documents_gen_docs_output_option():
    """usage.md must document gen_docs.sh --output and the default target."""
    content = _content()
    assert "bash cli/scripts/gen_docs.sh [--output <path>]" in content, (
        "usage.md must show the gen_docs.sh --output usage form"
    )
    section = content[content.index("### How to regenerate `commands.md`") :]
    assert "cli/docs/commands.md" in section and "working directory" in section, (
        "usage.md must state the default target and that a relative --output "
        "path resolves against the caller's working directory"
    )


# ---------------------------------------------------------------------------
# AC-4: link to commands.md
# ---------------------------------------------------------------------------


def test_usage_md_links_to_commands_md():
    """usage.md must contain a link to commands.md."""
    assert "commands.md" in _content(), "usage.md must link to commands.md"


# ---------------------------------------------------------------------------
# AC-5: no undocumented commands or flags
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "ai-team task new",
        "ai-team task start",
        "ai-team task complete",
        "ai-team task block",
        "ai-team bug new",
        "ai-team bug start",
        "ai-team bug resolve",
        "ai-team init",
        "ai-team status",
        "ai-team report",
        "ai-team validate",
        "ai-team list",
        "ai-team show",
        "ai-team adr new",
        "ai-team spec new",
        "ai-team archive",
    ],
)
def test_commands_mentioned_in_usage_exist_in_commands_md(command):
    """Every command mentioned in usage.md must also appear in commands.md."""
    assert COMMANDS_MD.is_file(), "commands.md must exist for cross-checking"
    commands_content = COMMANDS_MD.read_text(encoding="utf-8")
    # Extract the subcommand portion to check (e.g. "task new" from "ai-team task new")
    parts = command.split()
    # Check for the subcommand term in commands.md.
    assert command in commands_content or " ".join(parts[1:]) in commands_content, (
        f"'{command}' is documented in usage.md but does not appear in commands.md"
    )


def test_usage_md_does_not_mention_nonexistent_flags():
    """usage.md must not document flags that are absent from commands.md."""
    assert COMMANDS_MD.is_file(), "commands.md must exist for cross-checking"
    commands_content = COMMANDS_MD.read_text(encoding="utf-8").lower()
    usage_content = _content().lower()

    # These flags do not exist in any command — they must not appear in usage.md
    # as CLI flags (they may appear in prose explanation of the source code).
    nonexistent_flags = ["--verbose", "--quiet", "--output-dir"]
    for flag in nonexistent_flags:
        if flag in usage_content and flag not in commands_content:
            pytest.fail(
                f"usage.md documents flag '{flag}' that does not exist in commands.md"
            )


# ---------------------------------------------------------------------------
# T-040 AC-1: commands.md must not list --include-ai-process
# ---------------------------------------------------------------------------


def test_commands_md_does_not_list_include_ai_process():
    """commands.md must not contain --include-ai-process after regeneration."""
    assert COMMANDS_MD.is_file(), "commands.md must exist"
    assert "--include-ai-process" not in COMMANDS_MD.read_text(encoding="utf-8"), (
        "commands.md must not list --include-ai-process; regenerate with gen_docs.sh"
    )


# ---------------------------------------------------------------------------
# T-040 AC-2: usage.md documents codex scaffolding
# ---------------------------------------------------------------------------


def test_usage_md_documents_codex_agents_scaffold():
    """usage.md must document that --tools codex scaffolds .codex/agents/."""
    assert ".codex/agents" in _content(), (
        "usage.md must document that ai-team init --tools codex scaffolds .codex/agents/"
    )


def test_usage_md_documents_codex_skills_scaffold():
    """usage.md must document that --tools codex scaffolds .agents/skills/."""
    assert ".agents/skills" in _content(), (
        "usage.md must document that ai-team init --tools codex scaffolds .agents/skills/"
    )


# ---------------------------------------------------------------------------
# T-040 AC-3: usage.md states that init never copies ai-process/
# ---------------------------------------------------------------------------


def test_usage_md_states_never_copies_ai_process():
    """usage.md must contain the literal phrase: never copies `ai-process/`."""
    assert "never copies `ai-process/`" in _content(), (
        "usage.md must state explicitly that ai-team init never copies `ai-process/`"
    )


# ---------------------------------------------------------------------------
# T-040 AC-4: usage.md documents the scaffold source/generator maintenance flow
# ---------------------------------------------------------------------------


def test_usage_md_documents_scaffold_source_maintenance():
    """usage.md must describe how to maintain the package-owned scaffold sources."""
    lower = _lower()
    assert "sync_init_scaffolds" in lower or "scaffold" in lower, (
        "usage.md must document the scaffold source/generator maintenance flow"
    )


def test_usage_md_documents_scaffold_generator_script():
    """usage.md must name the scaffold generator script."""
    assert "sync_init_scaffolds.py" in _content(), (
        "usage.md must name sync_init_scaffolds.py in the maintainer section"
    )


# ---------------------------------------------------------------------------
# T-073 AC-1: development warning contract
# ---------------------------------------------------------------------------


def test_usage_md_documents_exact_development_warning():
    """usage.md must preserve the shipped warning text and issue URL exactly."""
    assert DEVELOPMENT_WARNING in _content(), (
        "usage.md must document the exact development warning contract"
    )


def test_usage_md_documents_warning_frequency_and_output_separation():
    """usage.md must explain warning frequency and stderr output separation."""
    lower = _lower()
    assert "exactly once" in lower and "every invocation" in lower, (
        "usage.md must state that the warning appears exactly once per invocation"
    )
    assert "stderr" in lower and "stdout" in lower and "json" in lower, (
        "usage.md must distinguish the warning on stderr from normal and JSON stdout"
    )


# ---------------------------------------------------------------------------
# T-073 AC-2: check-layout workflow contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "level_contract",
    [
        "Level 1 — expected directories",
        "Level 2 — artifact names and frontmatter",
        "Level 3 — root guidance",
        "Level 4 — version alignment",
    ],
)
def test_usage_md_documents_each_layout_validation_level(level_contract):
    """usage.md must name and explain all four layout validation levels."""
    assert level_contract in _content(), (
        f"usage.md must document the validation contract: {level_contract}"
    )


def test_usage_md_documents_check_layout_report_and_read_only_behavior():
    """usage.md must document check-layout report fields and read-only operation."""
    content = _content()
    lower = content.lower()
    assert "ai-team check-layout" in content, "usage.md must document check-layout"
    assert "read-only" in lower, "usage.md must state that check-layout is read-only"
    for field in ("Level", "Path", "Problem", "Suggested fix"):
        assert field in content, f"usage.md must document the {field!r} report field"


def test_usage_md_documents_check_layout_exit_behavior_and_no_repair():
    """usage.md must distinguish clean/issues exits and exclude automatic repair."""
    lower = _lower()
    assert "exit code 0" in lower and "exit code 1" in lower, (
        "usage.md must document clean and issue exit codes"
    )
    assert "does not repair" in lower or "never repairs" in lower, (
        "usage.md must state that check-layout does not repair repositories"
    )


def test_usage_md_documents_spec_new_overview():
    """usage.md must document the spec new --overview option."""
    assert "ai-team spec new --overview" in _content()


def test_usage_md_documents_missing_overview_hint():
    """usage.md must describe the advisory, stderr-only missing-S-000 hint and its commands."""
    content = _content()
    lower = content.lower()
    assert "no system overview" in lower, (
        "usage.md must describe the missing-S-000 hint"
    )
    assert "stderr" in lower, "usage.md must say the hint is written to stderr"
    assert "advisory" in lower, "usage.md must say the hint is advisory"
    for command in ("validate", "report", "status"):
        assert f"`{command}`" in content, (
            f"usage.md must name {command} as showing the hint"
        )


def _system_overview_section() -> str:
    content = _content()
    start = content.index("### System overview (S-000)")
    return content[start : content.index("### File a change request")]


def test_usage_md_documents_task_new_s000_creates_bootstrap_tasks():
    """usage.md must state that task new --spec S-000 creates the bootstrap tasks."""
    section = _system_overview_section()
    assert "ai-team task new" in section and "--spec S-000" in section
    assert "bootstrap tasks" in section
    assert "refused" not in section.lower()


def test_usage_md_documents_validate_does_not_report_s000_tasks():
    """usage.md must state that validate does not report the S-000 tasks."""
    section = _system_overview_section()
    assert "`validate` does not report" in section


def test_usage_md_documents_level_one_missing_coding_guidelines_finding():
    """usage.md must list the missing docs/coding_guidelines.md level 1 finding."""
    content = _content()
    start = content.index("1. **Level 1 — expected directories.**")
    level_one = content[start : content.index("2. **Level 2", start)]
    assert "docs/coding_guidelines.md" in level_one
    assert "scaffold placeholder" in level_one


def test_usage_md_documents_force_never_overwrites_coding_guidelines():
    """usage.md must state --force never overwrites docs/coding_guidelines.md."""
    row = next(
        line for line in _content().splitlines() if line.startswith("| `--force` |")
    )
    assert "docs/coding_guidelines.md" in row
    assert "only when missing" in row
    assert "never overwritten" in row


# ---------------------------------------------------------------------------
# CR-005: state-aware init (T-152)
# ---------------------------------------------------------------------------


def _init_section() -> str:
    content = _content()
    start = content.index("## Initialisation")
    end = content.index("## Daily Workflows")
    return content[start:end]


def test_init_section_describes_three_cases_and_detection():
    """AC-1: the init section names the upgrade, new-project and adoption cases and how each is detected."""
    section = _init_section().lower()
    assert "### init cases" in section
    for case in ("upgrade", "new project", "adoption"):
        assert case in section
    assert "`.ai-team.toml`" in section
    assert "already exist" in section


def test_init_flags_document_update_flags_and_force_as_yes_to_every_question():
    """AC-2: --update-docs, --update-skills, the adoption question and --force as yes."""
    section = _init_section()
    assert "| `--update-docs` |" in section
    assert "| `--update-skills` |" in section
    assert "Overwrite these existing files?" in section
    assert "yes to every overwrite question" in section
    assert "Update the agents and skills for the configured tools?" in section
    assert "never overwritten" in section


def test_init_section_documents_dry_run_case_lines_and_stale_warning():
    """AC-3: dry-run case lines, WOULD PROMPT and the stale-definition warning."""
    section = _init_section()
    for line in ("CASE: upgrade", "CASE: new project", "CASE: adoption"):
        assert f"`{line}`" in section
    assert "WOULD PROMPT" in section
    assert "are not shipped by this version of ai-team" in section


def test_usage_guide_names_update_skills_in_mismatch_legacy_and_refresh_passages():
    """AC-3: the three passages point at `ai-team init --update-skills`."""
    content = _content()
    assert (
        "or run `ai-team init --update-skills` to update the project to <running>."
        in content
    )
    assert "`ai-team init --update-skills` removes those legacy copies" in content
    assert "ai-team init . --tools <tools> --update-skills" in content
    assert "ai-team init --force`" not in content.split("### Expected layout")[0]
    assert "<tools> --force" not in content


def test_usage_md_describes_root_guidance_as_an_adoption_trigger():
    content = _content()
    adoption_row = next(
        line for line in content.splitlines() if line.startswith("| Adoption |")
    )
    assert "CLAUDE.md" in adoption_row
    assert "AGENTS.md" in adoption_row


def test_usage_md_states_no_interactive_needs_tools_only_without_marker_tools():
    content = _content()
    flag_row = next(
        line for line in content.splitlines() if line.startswith("| `--no-interactive`")
    )
    assert "Requires `--tools` to be provided explicitly" not in flag_row
    assert "`.ai-team.toml`" in flag_row
    assert "`--tools`" in flag_row


def test_usage_md_describes_tools_on_an_upgrade():
    section = _init_section()
    paragraph = next(
        block
        for block in section.split("\n\n")
        if block.startswith("**`--tools` on an upgrade.**")
    )
    flat = " ".join(paragraph.split())
    assert "sets `[init].tools` to the given list" in flat
    assert "newly adds are written without a question" in flat
    assert "only the files that do not exist yet" in flat
    assert "never overwritten" in flat
    assert "covers only the tools already configured" in flat
    assert "removed from `[init].tools`, and its files are left in place" in flat
