"""Tests for package-owned init scaffold source generation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _script_under_test() -> Path:
    return Path(__file__).resolve().parents[1] / "scripts" / "sync_init_scaffolds.py"


def _setup_fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    # Trap files at repository root that should never be read by the generator.
    _write(repo / ".claude", "trap\n")
    _write(repo / "ai-process", "trap\n")

    # Package-owned skill source fixture.
    _write(
        repo
        / "cli"
        / "src"
        / "ai_team"
        / "init"
        / "sources"
        / "skills"
        / "tdd"
        / "SKILL.md",
        (
            "---\n"
            "name: tdd\n"
            "description: claude skill\n"
            "allowed-tools: Read\n"
            "---\n"
            "\n"
            "# Test Skill Body\n"
            "\n"
            "Run the TDD cycle.\n"
        ),
    )
    _write(
        repo / "cli" / "src" / "ai_team" / "init" / "sources" / "agents" / "planner.md",
        "claude planner\n",
    )

    # Package-owned project guidance source fixtures.
    _write(
        repo / "cli" / "src" / "ai_team" / "init" / "sources" / "project" / "AGENTS.md",
        "# Project Guidance for Agents\n\nspecs tasks bugs decisions reports project-local docs\n",
    )
    _write(
        repo
        / "cli"
        / "src"
        / "ai_team"
        / "init"
        / "sources"
        / "project"
        / ".gitignore",
        ".ai-team.lock\n",
    )
    _write(
        repo
        / "cli"
        / "src"
        / "ai_team"
        / "init"
        / "sources"
        / "project"
        / "docs"
        / "coding_guidelines.md",
        "# Coding Guidelines\n\nFilled in by the project bootstrap.\n",
    )

    # Seed stale generated output that should be removed.
    _write(
        repo
        / "cli"
        / "src"
        / "ai_team"
        / "init"
        / "scaffolds"
        / "skills"
        / "old"
        / "SKILL.md",
        "old\n",
    )
    _write(
        repo / "cli" / "src" / "ai_team" / "init" / "scaffolds" / "project" / "old.txt",
        "old\n",
    )
    _write(
        repo / "cli" / "src" / "ai_team" / "init" / "scaffolds" / "agents" / "old.md",
        "old\n",
    )

    script = _script_under_test()
    assert script.exists(), "sync helper script is missing"
    copied_script = repo / "cli" / "scripts" / "sync_init_scaffolds.py"
    copied_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script, copied_script)

    return repo


def test_sync_script_copies_each_skill_md_unchanged(
    tmp_path: Path,
) -> None:
    repo = _setup_fake_repo(tmp_path)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    scaffolds_root = repo / "cli" / "src" / "ai_team" / "init" / "scaffolds"
    source_path = repo / "cli/src/ai_team/init/sources/skills/tdd/SKILL.md"

    exported = scaffolds_root / "skills" / "tdd" / "SKILL.md"

    assert exported.read_bytes() == source_path.read_bytes()

    assert not (scaffolds_root / "skills" / "old").exists()


def test_sync_script_stops_naming_the_skill_when_skill_md_is_missing(
    tmp_path: Path,
) -> None:
    repo = _setup_fake_repo(tmp_path)
    (repo / "cli/src/ai_team/init/sources/skills/tdd/SKILL.md").unlink()

    result = subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "tdd" in result.stderr
    assert "SKILL.md" in result.stderr


def test_sync_script_copies_package_owned_agents(tmp_path: Path) -> None:
    repo = _setup_fake_repo(tmp_path)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    scaffolds_root = repo / "cli" / "src" / "ai_team" / "init" / "scaffolds"

    assert (scaffolds_root / "agents" / "planner.md").read_text(
        encoding="utf-8"
    ) == "claude planner\n"

    assert not (scaffolds_root / "agents" / "old.md").exists()


def test_sync_script_replaces_project_with_empty_lifecycle_skeleton(
    tmp_path: Path,
) -> None:
    repo = _setup_fake_repo(tmp_path)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    project_root = repo / "cli" / "src" / "ai_team" / "init" / "scaffolds" / "project"
    expected_files = {
        Path("specs/.gitkeep"),
        Path("decisions/.gitkeep"),
        Path("docs/.gitkeep"),
        Path("docs/coding_guidelines.md"),
        Path("AGENTS.md"),
        Path(".gitignore"),
    }
    actual_files = {
        (Path(root) / file_name).relative_to(project_root)
        for root, _, file_names in os.walk(project_root)
        for file_name in file_names
    }

    assert actual_files == expected_files
    assert not (project_root / "old.txt").exists()


def test_sync_script_copies_project_guidance_files_from_source(
    tmp_path: Path,
) -> None:
    """AC-1 & AC-2: Generator copies AGENTS.md from sources/project/."""
    repo = _setup_fake_repo(tmp_path)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    sources_root = repo / "cli" / "src" / "ai_team" / "init" / "sources" / "project"
    project_root = repo / "cli" / "src" / "ai_team" / "init" / "scaffolds" / "project"

    source_text = (sources_root / "AGENTS.md").read_text(encoding="utf-8")
    scaffold_text = (project_root / "AGENTS.md").read_text(encoding="utf-8")
    assert scaffold_text == source_text, (
        "scaffolds/project/AGENTS.md does not match sources/project/AGENTS.md"
    )


def test_sync_script_copies_coding_guidelines_placeholder_into_project_docs(
    tmp_path: Path,
) -> None:
    """AC-1: the skeleton's docs/coding_guidelines.md is generated from its source."""
    repo = _setup_fake_repo(tmp_path)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    init_root = repo / "cli" / "src" / "ai_team" / "init"
    source_text = (
        init_root / "sources" / "project" / "docs" / "coding_guidelines.md"
    ).read_text(encoding="utf-8")
    scaffold_text = (
        init_root / "scaffolds" / "project" / "docs" / "coding_guidelines.md"
    ).read_text(encoding="utf-8")

    assert scaffold_text == source_text


def test_sync_script_copies_project_gitignore_ignoring_the_lock_sentinel(
    tmp_path: Path,
) -> None:
    """B-017: generator copies project/.gitignore, and it ignores .ai-team.lock."""
    repo = _setup_fake_repo(tmp_path)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    sources_root = repo / "cli" / "src" / "ai_team" / "init" / "sources" / "project"
    project_root = repo / "cli" / "src" / "ai_team" / "init" / "scaffolds" / "project"

    source_text = (sources_root / ".gitignore").read_text(encoding="utf-8")
    scaffold_text = (project_root / ".gitignore").read_text(encoding="utf-8")

    assert scaffold_text == source_text, (
        "scaffolds/project/.gitignore does not match sources/project/.gitignore"
    )
    assert scaffold_text == ".ai-team.lock\n"


# The generator never writes this tracked, empty placeholder at the scaffolds root.
_UNGENERATED_SCAFFOLD_FILES = frozenset({".gitkeep"})
_IGNORED_SCAFFOLD_PARTS = frozenset({"__pycache__", ".DS_Store"})


def _scaffold_tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not _IGNORED_SCAFFOLD_PARTS.intersection(path.relative_to(root).parts)
        and path.relative_to(root).as_posix() not in _UNGENERATED_SCAFFOLD_FILES
    }


def test_committed_scaffolds_match_fresh_sync_output(tmp_path: Path) -> None:
    """B-025: every committed scaffold equals what the generator produces."""
    cli_root = Path(__file__).resolve().parents[1]
    init_dir = Path("src") / "ai_team" / "init"
    committed_root = cli_root / init_dir / "scaffolds"

    tmp_repo = tmp_path / "repo"
    script_copy = tmp_repo / "cli" / "scripts" / "sync_init_scaffolds.py"
    script_copy.parent.mkdir(parents=True)
    shutil.copy2(_script_under_test(), script_copy)
    shutil.copytree(
        cli_root / init_dir / "sources", tmp_repo / "cli" / init_dir / "sources"
    )

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=tmp_repo,
        check=True,
        capture_output=True,
        text=True,
    )

    generated = _scaffold_tree_bytes(tmp_repo / "cli" / init_dir / "scaffolds")
    committed = _scaffold_tree_bytes(committed_root)

    differences = [
        f"missing from committed scaffolds: {p}"
        for p in generated.keys() - committed.keys()
    ]
    differences += [
        f"not produced by the generator: {p}"
        for p in committed.keys() - generated.keys()
    ]
    differences += [
        f"content differs: {p}"
        for p in generated.keys() & committed.keys()
        if generated[p] != committed[p]
    ]

    assert not differences, (
        "Committed init scaffolds are stale; run "
        "`python scripts/sync_init_scaffolds.py` from cli/ and commit the result.\n"
        + "\n".join(sorted(differences))
    )


def test_package_owned_project_gitignore_source_ignores_the_lock_sentinel() -> None:
    """B-017: the real (non-fixture) sources/project/.gitignore ships the lock entry."""
    repo_root = Path(__file__).resolve().parents[1]
    source_gitignore = (
        repo_root / "src" / "ai_team" / "init" / "sources" / "project" / ".gitignore"
    )
    scaffold_gitignore = (
        repo_root / "src" / "ai_team" / "init" / "scaffolds" / "project" / ".gitignore"
    )

    assert source_gitignore.is_file(), f"Missing source template: {source_gitignore}"
    assert scaffold_gitignore.is_file(), (
        f"Missing scaffold output: {scaffold_gitignore}"
    )

    source_text = source_gitignore.read_text(encoding="utf-8")

    assert ".ai-team.lock" in source_text.splitlines()
    assert "docs/reports/" in source_text.splitlines()


def test_package_owned_skill_sources_hold_only_skill_md_with_frontmatter() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sources_root = repo_root / "src" / "ai_team" / "init" / "sources" / "skills"
    scaffold_root = repo_root / "src" / "ai_team" / "init" / "scaffolds" / "skills"

    expected_skills = sorted(
        path.name for path in scaffold_root.iterdir() if path.is_dir()
    )
    source_skills = sorted(
        path.name for path in sources_root.iterdir() if path.is_dir()
    )

    assert source_skills == expected_skills

    for skill_name in source_skills:
        skill_source_dir = sources_root / skill_name

        assert (skill_source_dir / "SKILL.md").is_file()
        assert not (skill_source_dir / "body.md").exists()
        assert not (skill_source_dir / "metadata.toml").exists()
        assert (
            (skill_source_dir / "SKILL.md")
            .read_text(encoding="utf-8")
            .startswith("---\n")
        )


def test_init_scaffolds_export_change_request_skill_and_project_directory() -> None:
    """Fresh init scaffolds include change-request workflow surfaces."""
    repo_root = Path(__file__).resolve().parents[1]
    source_skill = (
        repo_root / "src" / "ai_team" / "init" / "sources" / "skills" / "change-request"
    )
    scaffold_project = repo_root / "src" / "ai_team" / "init" / "scaffolds" / "project"

    assert (source_skill / "SKILL.md").is_file()
    # Change-requests live in the local tracker (S-006), not the project scaffold.
    assert not (scaffold_project / "change-requests").exists()

    scaffold_skill = (
        repo_root
        / "src"
        / "ai_team"
        / "init"
        / "scaffolds"
        / "skills"
        / "change-request"
        / "SKILL.md"
    )
    assert scaffold_skill.is_file()


def test_sync_script_is_idempotent_for_agent_scaffolds(tmp_path: Path) -> None:
    """AC-4: Running the generator twice leaves no additional diff."""
    repo = _setup_fake_repo(tmp_path)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    scaffolds_root = repo / "cli" / "src" / "ai_team" / "init" / "scaffolds"
    agents_root = scaffolds_root / "agents"

    def collect_file_contents(directory: Path) -> dict[str, str]:
        return {
            str(f.relative_to(directory)): f.read_text(encoding="utf-8")
            for f in sorted(directory.rglob("*"))
            if f.is_file()
        }

    before = collect_file_contents(agents_root)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    after = collect_file_contents(agents_root)

    assert after == before, (
        "Agent scaffold changed on second run — generator is not idempotent"
    )


def test_sync_script_does_not_modify_sources_directory(tmp_path: Path) -> None:
    """AC-5: Running the generator must not modify source files."""
    repo = _setup_fake_repo(tmp_path)

    sources_dir = repo / "cli" / "src" / "ai_team" / "init" / "sources" / "agents"

    def collect_file_contents(directory: Path) -> dict[str, str]:
        return {
            str(f.relative_to(directory)): f.read_text(encoding="utf-8")
            for f in sorted(directory.rglob("*"))
            if f.is_file()
        }

    sources_before = collect_file_contents(sources_dir)

    subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py"],
        cwd=repo,
        check=True,
    )

    sources_after = collect_file_contents(sources_dir)

    assert sources_after == sources_before, (
        "Generator modified source files — sources must remain unchanged"
    )


def _run_sync_script(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "cli/scripts/sync_init_scaffolds.py", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _scaffolds_root(repo: Path) -> Path:
    return repo / "cli" / "src" / "ai_team" / "init" / "scaffolds"


def _snapshot_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_sync_script_long_help_prints_usage_and_leaves_scaffolds_untouched(
    tmp_path: Path,
) -> None:
    repo = _setup_fake_repo(tmp_path)
    scaffolds_before = _snapshot_tree(_scaffolds_root(repo))

    result = _run_sync_script(repo, "--help")

    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
    assert "Synchronized" not in result.stdout
    assert _snapshot_tree(_scaffolds_root(repo)) == scaffolds_before


def test_sync_script_short_help_prints_usage_and_leaves_scaffolds_untouched(
    tmp_path: Path,
) -> None:
    repo = _setup_fake_repo(tmp_path)
    scaffolds_before = _snapshot_tree(_scaffolds_root(repo))

    result = _run_sync_script(repo, "-h")

    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
    assert "Synchronized" not in result.stdout
    assert _snapshot_tree(_scaffolds_root(repo)) == scaffolds_before


def test_sync_script_rejects_unknown_argument_with_usage_and_leaves_scaffolds_untouched(
    tmp_path: Path,
) -> None:
    repo = _setup_fake_repo(tmp_path)
    scaffolds_before = _snapshot_tree(_scaffolds_root(repo))

    result = _run_sync_script(repo, "--bogus")

    assert result.returncode == 2
    assert "usage:" in result.stderr
    assert "--bogus" in result.stderr
    assert _snapshot_tree(_scaffolds_root(repo)) == scaffolds_before


def test_sync_script_without_arguments_generates_scaffolds(tmp_path: Path) -> None:
    repo = _setup_fake_repo(tmp_path)

    result = _run_sync_script(repo)

    assert result.returncode == 0, result.stderr
    assert "Synchronized init scaffolds" in result.stdout
    assert _scaffolds_root(repo).is_dir()


def test_package_owned_agent_sources_cover_each_exported_role() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sources_root = repo_root / "src" / "ai_team" / "init" / "sources" / "agents"
    scaffold_root = repo_root / "src" / "ai_team" / "init" / "scaffolds" / "agents"

    expected_roles = sorted(path.stem for path in scaffold_root.glob("*.md"))
    source_roles = sorted(path.stem for path in sources_root.glob("*.md"))

    assert source_roles == expected_roles

    for role_name in expected_roles:
        source = sources_root / f"{role_name}.md"
        scaffold = scaffold_root / f"{role_name}.md"

        assert source.read_text(encoding="utf-8") == scaffold.read_text(
            encoding="utf-8"
        )
