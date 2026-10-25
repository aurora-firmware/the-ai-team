"""Read-only resolution and validation of the AI-team repository layout."""

from __future__ import annotations

import importlib.metadata
import importlib.resources as resources
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Literal

from ai_team.core.config import is_valid_project_dir
from ai_team.core.locator import DEFAULT_PROJECT_DIR, ProjectRoot
from ai_team.core.tool_paths import EXPORT_PATHS
from ai_team.core.tracker import (
    MIGRATION_GUIDE,
    is_inside,
    legacy_work_item_dirs,
    resolve_tracker_dir,
)
from ai_team.core.validate import Finding as ArtifactFinding
from ai_team.core.validate import validate_project

_GUIDANCE_FILENAME = "AGENTS.md"
_GUIDANCE_HEADINGS = (
    "Build and Install",
    "Test",
    "Run",
    "Lint and Format",
    "Key Conventions",
)
_HEADING_PATTERN = re.compile(r"^##[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
_VERSION_PATTERN = re.compile(
    r"[0-9]+(?:\.[0-9]+)*(?:[A-Za-z][A-Za-z0-9.-]*[0-9]?|[.+-][A-Za-z0-9.-]+)*"
)
_Status = Literal["valid", "missing", "invalid"]


@dataclass(frozen=True)
class LayoutFinding:
    """One actionable violation of a numbered layout validation level."""

    level: int
    path: str
    problem: str
    suggested_fix: str


@dataclass(frozen=True)
class LayoutContract:
    """Locally resolved inputs used by every layout validation level."""

    repo: Path
    marker: Path
    project_dir: Path
    configured_version: str | None
    current_version: str | None
    raw_configured_version: object = field(default=None, repr=False)
    marker_status: _Status = field(default="valid", repr=False)
    version_status: _Status = field(default="valid", repr=False)


def _finding(
    level: int,
    path: str,
    problem: str,
    suggested_fix: str,
) -> LayoutFinding:
    return LayoutFinding(level, path, problem, suggested_fix)


def _is_version(value: object) -> bool:
    return isinstance(value, str) and _VERSION_PATTERN.fullmatch(value) is not None


def resolve_layout(
    repo: Path,
    *,
    current_version: str | None = None,
) -> tuple[LayoutContract, list[LayoutFinding]]:
    """Resolve marker configuration and installed contract data without mutation."""

    repo = repo.resolve()
    marker = repo / ".ai-team.toml"
    findings: list[LayoutFinding] = []
    marker_status: _Status = "valid"
    data: object = {}

    if not marker.is_file():
        marker_status = "missing"
        findings.append(
            _finding(
                1,
                ".ai-team.toml",
                "Repository marker .ai-team.toml is missing; project and tool settings cannot be resolved.",
                "Run 'ai-team init' or restore .ai-team.toml; repository conventions will be checked where safe.",
            )
        )
    else:
        try:
            with marker.open("rb") as stream:
                data = tomllib.load(stream)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            marker_status = "invalid"
            findings.append(
                _finding(
                    1,
                    ".ai-team.toml",
                    f"Repository marker .ai-team.toml is invalid: {exc}",
                    "Correct the TOML syntax or regenerate the marker with 'ai-team init'.",
                )
            )

    project_value: object = None
    version_value: object = None
    if marker_status == "valid" and isinstance(data, dict):
        project_table = data.get("project")
        init_table = data.get("init")
        if isinstance(project_table, dict):
            project_value = project_table.get("dir")
        if isinstance(init_table, dict):
            version_value = init_table.get("framework_version")

    project_dir_name = DEFAULT_PROJECT_DIR
    if marker_status == "valid":
        if is_valid_project_dir(project_value):
            project_dir_name = project_value
        else:
            findings.append(
                _finding(
                    1,
                    ".ai-team.toml",
                    f"Marker value [project].dir is missing or invalid; using the default '{DEFAULT_PROJECT_DIR}' directory.",
                    f"Set [project].dir to a relative directory path inside the repository without '..', such as '{DEFAULT_PROJECT_DIR}' or 'docs/{DEFAULT_PROJECT_DIR}'.",
                )
            )

    version_status: _Status = "valid"
    configured_version: str | None = None
    if marker_status != "valid" or version_value is None:
        version_status = "missing"
    elif _is_version(version_value):
        configured_version = version_value
    else:
        version_status = "invalid"

    installed_version = (
        importlib.metadata.version("ai-team")
        if current_version is None
        else current_version
    )
    return (
        LayoutContract(
            repo=repo,
            marker=marker,
            project_dir=repo / project_dir_name,
            configured_version=configured_version,
            current_version=installed_version,
            raw_configured_version=version_value,
            marker_status=marker_status,
            version_status=version_status,
        ),
        sorted(findings, key=_sort_key),
    )


def _resource_directories(root: Traversable) -> list[Path]:
    """Return directory paths below an importlib Traversable resource root."""

    directories: list[Path] = []

    def walk(node: Traversable, relative: Path) -> None:
        for child in node.iterdir():
            if child.is_dir():
                child_relative = relative / child.name
                directories.append(child_relative)
                walk(child, child_relative)

    walk(root, Path())
    return directories


def _expected_directories(contract: LayoutContract) -> list[Path]:
    scaffold_root = resources.files("ai_team.init").joinpath("scaffolds")
    expected = [contract.project_dir]
    expected.extend(
        contract.project_dir / relative
        for relative in _resource_directories(scaffold_root.joinpath("project"))
    )
    for scaffold_subfolder, destination in EXPORT_PATHS:
        destination_root = contract.repo / destination
        expected.append(destination_root)
        expected.extend(
            destination_root / relative
            for relative in _resource_directories(
                scaffold_root.joinpath(scaffold_subfolder)
            )
        )
    return expected


def _missing_directory_fix(contract: LayoutContract, path: Path) -> str:
    """Suggest the init command that recreates a missing scaffold directory."""
    if path.is_relative_to(contract.project_dir):
        return "Create the directory by restoring the current scaffold or rerunning 'ai-team init'."
    return "Create the directory by restoring the current scaffold or running 'ai-team init --update-skills'."


def _tracker_findings(contract: LayoutContract) -> list[LayoutFinding]:
    """Report an unignored in-repository tracker and unmigrated legacy folders."""

    findings: list[LayoutFinding] = []
    tracker = resolve_tracker_dir(contract.repo)
    if is_inside(tracker, contract.repo):
        display_path = tracker.relative_to(contract.repo).as_posix()
        try:
            completed = subprocess.run(
                ["git", "-C", str(contract.repo), "check-ignore", "-q", display_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            completed = None
        if completed is not None and completed.returncode == 1:
            findings.append(
                _finding(
                    1,
                    display_path,
                    f"Tracker folder '{display_path}' is inside the repository but not ignored by git.",
                    f"Add '/{display_path.split('/')[0]}/' to the repository's root .gitignore.",
                )
            )

    for folder in legacy_work_item_dirs(contract.project_dir):
        display_path = folder.relative_to(contract.repo).as_posix()
        findings.append(
            _finding(
                1,
                display_path,
                f"Legacy work-item folder '{display_path}' still holds files; tasks, bugs, and change-requests now live in the local tracker.",
                f"Follow {MIGRATION_GUIDE} to move the files into the tracker and remove the folder.",
            )
        )
    return findings


def _coding_guidelines_findings(contract: LayoutContract) -> list[LayoutFinding]:
    """Report a missing docs/coding_guidelines.md; any existing content is accepted."""

    guidelines = contract.project_dir / "docs" / "coding_guidelines.md"
    if guidelines.is_file():
        return []
    display_path = guidelines.relative_to(contract.repo).as_posix()
    return [
        _finding(
            1,
            display_path,
            f"Required project file '{display_path}' is missing.",
            f"Create '{display_path}' from the scaffold placeholder.",
        )
    ]


def check_level_1(contract: LayoutContract) -> list[LayoutFinding]:
    """Report missing directories, tracker ignore problems, and legacy folders."""

    findings = _tracker_findings(contract)
    findings.extend(_coding_guidelines_findings(contract))
    for path in _expected_directories(contract):
        if not path.is_dir():
            display_path = path.relative_to(contract.repo).as_posix()
            findings.append(
                _finding(
                    1,
                    display_path,
                    f"Required scaffold directory '{display_path}' is missing.",
                    _missing_directory_fix(contract, path),
                )
            )
    return sorted(findings, key=_sort_key)


_LEVEL_2_CODES = {
    "filename-pattern",
    "frontmatter-invalid",
    "id-missing",
    "id-pattern",
    "status-invalid",
}


def _artifact_suggested_fix(finding: ArtifactFinding) -> str:
    if finding.code == "filename-pattern":
        return "Rename the artifact to the filename convention stated in the problem."
    if finding.code == "status-invalid":
        return "Set the frontmatter status to one of the allowed values named in the problem."
    if finding.code == "id-pattern":
        return "Correct the frontmatter id to the required artifact ID pattern."
    if finding.code == "id-missing":
        return "Add the required artifact id to the YAML frontmatter."
    return (
        "Correct the YAML frontmatter and add every required field for this "
        "artifact type."
    )


def check_level_2(contract: LayoutContract) -> list[LayoutFinding]:
    """Report managed artifact naming, frontmatter, and status violations."""

    display_path = contract.project_dir.relative_to(contract.repo).as_posix()
    root = ProjectRoot._from_repo_and_project_dir_name(contract.repo, display_path)
    findings: list[LayoutFinding] = []
    # Tasks, bugs, and change-requests live in the tracker, so they are
    # checked even when the project directory is missing.
    scopes = [{"tasks": True}, {"bugs": True}, {"change_requests": True}]
    if contract.project_dir.is_dir():
        scopes += [{"specs": True}, {"adrs": True}]
    else:
        findings.append(
            _finding(
                2,
                display_path,
                f"Spec and decision checks are blocked because project directory '{display_path}' is missing or is not a directory.",
                "Restore the configured project directory, then rerun the layout check.",
            )
        )
    for scope in scopes:
        try:
            artifact_findings = validate_project(root, **scope)
        except (OSError, UnicodeError) as exc:
            scope_name = next(iter(scope)).replace("_", " ")
            findings.append(
                _finding(
                    2,
                    contract.project_dir.relative_to(contract.repo).as_posix(),
                    f"The {scope_name} artifact check is blocked: {exc}",
                    "Restore readable managed artifact inputs, then rerun the layout check.",
                )
            )
            continue

        findings.extend(
            _finding(
                2,
                finding.path,
                finding.message,
                _artifact_suggested_fix(finding),
            )
            for finding in artifact_findings
            if finding.code in _LEVEL_2_CODES
        )
    return sorted(findings, key=_sort_key)


def _markdown_sections(content: str) -> dict[str, str]:
    matches = list(_HEADING_PATTERN.finditer(content))
    return {
        match.group(1).strip(): content[
            match.end() : matches[index + 1].start()
            if index + 1 < len(matches)
            else len(content)
        ].strip()
        for index, match in enumerate(matches)
    }


def _content_lines(content: str) -> set[str]:
    return {
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("```")
    }


def _starter_guidance_sections(filename: str) -> dict[str, str]:
    starter = resources.files("ai_team.init").joinpath("sources", "root", filename)
    return _markdown_sections(starter.read_text(encoding="utf-8"))


def _is_placeholder_section(content: str, starter_content: str) -> bool:
    content_lines = _content_lines(content)
    return not content_lines or content_lines <= _content_lines(starter_content)


def check_level_3(contract: LayoutContract) -> list[LayoutFinding]:
    """Report missing or placeholder root AGENTS.md guidance."""

    filename = _GUIDANCE_FILENAME
    path = contract.repo / filename
    if not path.is_file():
        return [
            _finding(
                3,
                filename,
                f"Root guidance file '{filename}' is missing.",
                f"Create '{filename}' and fill every required project-guidance section.",
            )
        ]

    try:
        content = path.read_text(encoding="utf-8")
        starter_sections = _starter_guidance_sections(filename)
    except (OSError, UnicodeError) as exc:
        return [
            _finding(
                3,
                filename,
                f"Root guidance checks for '{filename}' are blocked: {exc}",
                "Restore a readable UTF-8 guidance file, then rerun the layout check.",
            )
        ]

    findings: list[LayoutFinding] = []
    sections = _markdown_sections(content)
    for heading in _GUIDANCE_HEADINGS:
        if heading not in sections:
            findings.append(
                _finding(
                    3,
                    filename,
                    f"Root guidance file '{filename}' is missing required section '{heading}'.",
                    f"Add a '## {heading}' section containing project-specific guidance.",
                )
            )
        elif _is_placeholder_section(sections[heading], starter_sections[heading]):
            findings.append(
                _finding(
                    3,
                    filename,
                    f"Required section '{heading}' in '{filename}' contains only starter-template placeholder content.",
                    f"Replace the '{heading}' placeholder with project-specific guidance.",
                )
            )
    return sorted(findings, key=_sort_key)


def check_level_4(contract: LayoutContract) -> list[LayoutFinding]:
    """Report missing, invalid, or non-exact framework version alignment."""

    current = contract.current_version
    if contract.version_status == "missing":
        configured = "unavailable"
        return [
            _finding(
                4,
                ".ai-team.toml",
                f"Configured framework version is missing ({configured}); current CLI version is {current!r}.",
                "Set [init].framework_version to the exact current CLI distribution version.",
            )
        ]
    if contract.version_status == "invalid":
        return [
            _finding(
                4,
                ".ai-team.toml",
                f"Configured framework version {contract.raw_configured_version!r} is invalid; current CLI version is {current!r}.",
                "Set [init].framework_version to a valid version string matching the current CLI exactly.",
            )
        ]
    if contract.configured_version != current:
        return [
            _finding(
                4,
                ".ai-team.toml",
                f"Configured framework version {contract.configured_version!r} does not exactly match current CLI version {current!r}.",
                "Reinitialize or update the scaffold and record the exact current CLI version.",
            )
        ]
    return []


def _sort_key(finding: LayoutFinding) -> tuple[int, str, str, str]:
    return finding.level, finding.path, finding.problem, finding.suggested_fix


def check_layout(
    repo: Path,
    *,
    current_version: str | None = None,
) -> list[LayoutFinding]:
    """Run implemented layout levels and return deterministic findings."""

    contract, findings = resolve_layout(repo, current_version=current_version)
    findings.extend(check_level_1(contract))
    findings.extend(check_level_2(contract))
    findings.extend(check_level_3(contract))
    findings.extend(check_level_4(contract))
    return sorted(findings, key=_sort_key)
