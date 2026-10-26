"""
Tests for T-028: cli/docs/usage.md hand-written CLI guide.

Covers:
  AC-1: cli/docs/usage.md exists and covers installation, ai-team init,
        daily command workflows, the project/ folder structure, and a
        maintainer section.
  AC-2: usage.md describes the project/ folder structure including specs/
        (+ archive/), decisions/, docs/, the tracker folders,
        .ai-team.toml, and the locator resolution order.
  AC-3: usage.md includes a maintainer section with module map, how to add
        a command, how to run tests, how to build/release, and how to
        regenerate commands.md.
  AC-4: usage.md links to commands.md.
  AC-5: usage.md documents only commands and flags present in commands.md —
        verified by cross-checking every command in its examples.
"""

from __future__ import annotations

import re
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
    """usage.md must have an installation section with an install command."""
    content = _content()
    assert "\n## Installation\n" in content, (
        "usage.md must have an Installation section"
    )
    assert "pipx install" in content, "usage.md must show how to install the CLI"


def test_usage_md_covers_init_command():
    """usage.md must have an initialisation section that runs ai-team init."""
    content = _content()
    assert "\n## Initialisation\n" in content, (
        "usage.md must have an Initialisation section"
    )
    assert "ai-team init" in content, "usage.md must document the ai-team init command"


def test_usage_md_covers_daily_workflows():
    """usage.md must walk through the daily task and bug workflows."""
    content = _content()
    assert "\n## Daily Workflows\n" in content, (
        "usage.md must have a Daily Workflows section"
    )
    for command in ("ai-team task new", "ai-team task start", "ai-team bug new"):
        assert command in content, f"usage.md daily workflows must show {command!r}"


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


def test_usage_md_describes_tracker_folders():
    """usage.md must describe the tracker folders, where state is the status field."""
    content = _content()
    assert "[tracker] dir" in content, "usage.md must name the [tracker] dir setting"
    for folder in ("tasks/", "bugs/", "change-requests/", "archive/"):
        assert folder in content, f"usage.md must describe the tracker {folder} folder"
    assert "state is the status field" in content, (
        "usage.md must say work-item state is the status field"
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


def _commands_in_usage_examples() -> set[str]:
    """Return ``ai-team <command> [<subcommand>]`` for each example command line."""
    commands = set()
    for block in re.findall(r"```bash\n(.*?)```", _content(), re.S):
        for line in block.splitlines():
            match = re.match(r"ai-team ([a-z][a-z-]*)(?: ([a-z][a-z-]*))?", line)
            if match:
                commands.add(" ".join(part for part in match.groups() if part))
    return commands


def test_usage_md_example_commands_exist_in_commands_md():
    """Every command in a usage.md example must have a commands.md entry."""
    commands_content = COMMANDS_MD.read_text(encoding="utf-8")
    commands = _commands_in_usage_examples()
    assert {"init", "task new", "bug new"} <= commands, (
        "usage.md examples must include the core commands"
    )
    for command in sorted(commands):
        name = command.split()[0]
        assert (
            f"`ai-team {command}`" in commands_content
            or f"`ai-team {name}`" in commands_content
        ), f"'ai-team {command}' is used in usage.md but missing from commands.md"


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
# T-173 AC-1: usage.md describes the Claude-only init
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "retired",
    [
        "codex",
        "--tools",
        "[init] tools",
        "[init].tools",
        ".codex/",
        ".agents/",
        "$name",
    ],
)
def test_usage_md_has_no_codex_or_tools_text(retired):
    """usage.md must not mention Codex, --tools, [init] tools, .codex/ or .agents/."""
    assert retired.lower() not in _lower(), f"usage.md still mentions {retired!r}"


def test_usage_md_says_init_always_writes_the_claude_folders():
    """usage.md must say init always writes .claude/agents/ and .claude/skills/."""
    flat = _flat(_init_section())
    assert "always writes `.claude/agents/` and `.claude/skills/`" in flat


def test_usage_md_names_agents_md_as_the_only_guidance_file():
    """AC-2: AGENTS.md is the only guidance file init generates and check-layout requires."""
    flat = _flat(_init_section())
    assert "`AGENTS.md` is the only guidance file `init` generates" in flat
    assert "CLAUDE.md" not in _content()
    level_three = _content().split("3. **Level 3")[1].split("4. **Level 4")[0]
    assert "root `AGENTS.md`" in _flat(level_three)


def test_usage_md_describes_the_flat_source_and_scaffold_layout():
    """AC-3: sources are skills/<name>/SKILL.md and agents/*.md; scaffolds are project/, agents/, skills/."""
    flat = _flat(_content())
    assert "`sources/skills/<name>/SKILL.md`" in flat
    assert "`sources/agents/*.md`" in flat
    assert "`scaffolds/{project,agents,skills}/`" in flat
    assert "scaffolds/claude" not in flat


def test_usage_md_states_an_upgrade_is_detected_from_framework_version():
    """AC-4: init detects an upgrade from [init] framework_version."""
    flat = _flat(_init_section())
    assert "records `[init] framework_version`" in flat
    assert "detects an upgrade from `[init] framework_version`" in flat


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
    assert "Update the agents and skills?" in section
    assert "never overwritten" in section


def test_init_section_documents_dry_run_case_lines_and_stale_warning():
    """AC-3: dry-run case lines, WOULD PROMPT and the stale-definition warning."""
    section = _init_section()
    for line in ("CASE: upgrade", "CASE: new project", "CASE: adoption"):
        assert f"`{line}`" in section
    assert "WOULD PROMPT" in section
    assert "are not shipped by this version of ai-team" in section


def test_usage_guide_names_update_skills_in_mismatch_and_refresh_passages():
    """AC-3: the three passages point at `ai-team init --update-skills`."""
    content = _content()
    assert (
        "or run `ai-team init --update-skills` to update the project to <running>."
        in content
    )
    assert "ai-team init . --update-skills --update-docs" in content
    assert "ai-team init --force`" not in content.split("### Expected layout")[0]


def test_usage_md_describes_root_guidance_as_an_adoption_trigger():
    content = _content()
    adoption_row = next(
        line for line in content.splitlines() if line.startswith("| Adoption |")
    )
    assert "AGENTS.md" in adoption_row
    assert "CLAUDE.md" not in adoption_row


# ---------------------------------------------------------------------------
# CR-005: init reporting docs (T-159)
# ---------------------------------------------------------------------------

SETUP_GUIDE_MD = REPO_ROOT / "guides" / "setup-guide.md"
CUSTOMIZATION_GUIDE_MD = REPO_ROOT / "guides" / "customization-guide.md"


def _flat(text: str) -> str:
    return " ".join(text.split())


REPORTING_RULE = (
    "Every file `init` creates is reported on stdout as `WROTE: <path>` "
    "(`WOULD WRITE` in a dry run) and every file it replaces as `OVERWROTE: <path>` "
    "(`WOULD OVERWRITE` in a dry run). The tracker folder it creates is reported as "
    "`CREATED: <path>` (`WOULD CREATE` in a dry run) and the root `.gitignore` it "
    "adds the tracker rule to as `UPDATED: <path>` (`WOULD UPDATE` in a dry run). "
    "Only an adoption lists kept files, on stderr: the existing agent, skill and "
    "project-skeleton files its overwrite question kept. Kept root guidance and an "
    "existing `docs/coding_guidelines.md` are not listed, and an upgrade lists no "
    "kept files."
)
RETIRED_KEPT_FILES_RULE = "and every existing file it keeps on stderr"
RETIRED_SETUP_GUIDE_SENTENCE = (
    "Every existing file that `init` replaces is reported as `OVERWROTE: <path>`; "
    "newly created files are not."
)


def test_usage_guide_states_the_init_reporting_rule():
    """T-161 AC-4: kept files are listed only by an adoption; tracker lines are named."""
    flat = _flat(_content())
    assert REPORTING_RULE in flat
    assert RETIRED_KEPT_FILES_RULE not in flat
    assert "Declined or skipped files are not reported" not in flat
    assert (
        "Newly created files and declined or skipped files are not reported" not in flat
    )


def test_setup_guide_states_the_init_reporting_rule():
    """T-161 AC-4: the setup guide states the same rule; only the retired sentence is barred."""
    flat = _flat(SETUP_GUIDE_MD.read_text(encoding="utf-8"))
    assert REPORTING_RULE in flat
    assert RETIRED_KEPT_FILES_RULE not in flat
    assert RETIRED_SETUP_GUIDE_SENTENCE not in flat


def test_usage_guide_upgrade_row_says_missing_skeleton_files_are_written_unasked():
    """AC-2: the Upgrade row covers missing project-skeleton files."""
    row = next(
        line for line in _content().splitlines() if line.startswith("| Upgrade |")
    )
    assert (
        "Missing project-skeleton files that no question covers are written "
        "without a question and never overwritten" in row
    )


def test_customization_guide_states_when_skills_are_overwritten():
    """AC-3: skills are overwritten on an upgrade update, or an adoption yes or --force."""
    flat = _flat(CUSTOMIZATION_GUIDE_MD.read_text(encoding="utf-8"))
    assert (
        "when an upgrade updates the agents and skills (you answer yes to that "
        "question, or pass `--update-skills` or `--force`), or on an adoption "
        "answered yes or run with `--force`" in flat
    )


def test_usage_guide_dry_run_would_overwrite_covers_every_approved_overwrite():
    """AC-4: the --dry-run row says WOULD OVERWRITE covers --update-docs and --update-skills."""
    row = next(
        line for line in _content().splitlines() if line.startswith("| `--dry-run`")
    )
    assert "existing file, with --force" not in row
    assert (
        "`WOULD OVERWRITE` (every approved overwrite, including `--update-docs` "
        "and `--update-skills` on an upgrade)" in row
    )


def test_usage_guide_states_the_pr49_init_rules():
    """PR #49 review: a preset marker is a first run; empty questions are not asked."""
    flat = " ".join(USAGE_MD.read_text(encoding="utf-8").split())
    assert (
        "exists in the repository root and records `[init] framework_version`" in flat
    )
    assert "a question that covers no files is not asked" in flat
    assert "--update-skills --update-docs` to refresh them" in flat


def test_usage_guide_tells_a_preset_marker_to_leave_out_init():
    """PR #49 re-review: a preset marker must not record `[init]`."""
    flat = " ".join(USAGE_MD.read_text(encoding="utf-8").split())
    assert "leave out `[init]`: `init` writes `[init]` itself" in flat
