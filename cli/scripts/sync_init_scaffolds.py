#!/usr/bin/env python3
"""Generate bundled init scaffolds from package-owned source assets."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PROJECT_LEAF_DIRS = (
    # Tasks, bugs, and change-requests live in the local tracker (spec S-006),
    # outside the project directory, so they are not scaffolded here.
    "specs",
    "decisions",
    "docs",
)

SKILL_SUPPORTING_FOLDERS = ("assets", "references", "scripts")

COPY_IGNORE_PATTERNS = ("__pycache__", ".DS_Store")


def _cli_root_from_script(script_path: Path) -> Path:
    # script lives at <repo>/cli/scripts/sync_init_scaffolds.py
    return script_path.resolve().parents[1]


def _replace_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(f"Expected source directory does not exist: {source}")

    if destination.exists():
        shutil.rmtree(destination)

    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(*COPY_IGNORE_PATTERNS),
    )


def _replace_project_skeleton(destination: Path, source: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)

    destination.mkdir(parents=True, exist_ok=True)

    for leaf in PROJECT_LEAF_DIRS:
        leaf_dir = destination / leaf
        leaf_dir.mkdir(parents=True, exist_ok=True)
        (leaf_dir / ".gitkeep").write_text("", encoding="utf-8")

    for root_file in ("AGENTS.md", ".gitignore"):
        src = source / root_file
        if not src.is_file():
            raise FileNotFoundError(
                f"Expected project skeleton root file does not exist: {src}"
            )
        shutil.copy2(src, destination / root_file)

    coding_guidelines = source / "docs" / "coding_guidelines.md"
    if not coding_guidelines.is_file():
        raise FileNotFoundError(
            f"Expected project skeleton docs file does not exist: {coding_guidelines}"
        )
    shutil.copy2(coding_guidelines, destination / "docs" / "coding_guidelines.md")


def _copy_skill_supporting_folders(skill_dir: Path, skill_output_dir: Path) -> None:
    # Copied verbatim: supporting files are never placeholder-filled.
    for folder_name in SKILL_SUPPORTING_FOLDERS:
        source_folder = skill_dir / folder_name
        if source_folder.is_dir():
            shutil.copytree(
                source_folder,
                skill_output_dir / folder_name,
                ignore=shutil.ignore_patterns(*COPY_IGNORE_PATTERNS),
            )


def _replace_generated_skills(source_root: Path, destination_root: Path) -> None:
    destination_root.mkdir(parents=True, exist_ok=True)
    skill_root = destination_root / "skills"
    if skill_root.exists():
        shutil.rmtree(skill_root)
    skill_root.mkdir(parents=True, exist_ok=True)

    if not source_root.is_dir():
        raise FileNotFoundError(
            f"Expected skill source directory does not exist: {source_root}"
        )

    for skill_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            raise FileNotFoundError(
                f"Skill '{skill_dir.name}' has no SKILL.md: {skill_path}"
            )

        skill_output_dir = skill_root / skill_dir.name
        skill_output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(skill_path, skill_output_dir / "SKILL.md")
        _copy_skill_supporting_folders(skill_dir, skill_output_dir)


def sync_init_scaffolds(cli_root: Path) -> None:
    init_root = cli_root / "src" / "ai_team" / "init"
    scaffolds_root = init_root / "scaffolds"
    sources_root = init_root / "sources"

    scaffolds_root.mkdir(parents=True, exist_ok=True)
    _replace_project_skeleton(scaffolds_root / "project", sources_root / "project")
    _replace_generated_skills(
        sources_root / "skills",
        scaffolds_root,
    )
    _replace_tree(sources_root / "agents", scaffolds_root / "agents")


def main() -> None:
    # Parse first so --help and bad arguments never reach the destructive sync.
    argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="Regenerate bundled init scaffolds from package-owned sources.",
    ).parse_args()
    cli_root = _cli_root_from_script(Path(__file__))
    sync_init_scaffolds(cli_root)
    print(f"Synchronized init scaffolds in {cli_root / 'src/ai_team/init/scaffolds'}")
    print("Run this script before `uv build` to refresh bundled scaffold output.")


if __name__ == "__main__":
    main()
