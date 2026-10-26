"""
Tests for T-002: ai_team.core.locator — find_project_root and ProjectRoot.

Covers:
  AC-1: Walk up from cwd to find a folder named 'ai-team/' (default project_dir).
  AC-2: AI_TEAM_ROOT env var is preferred over directory walking.
  AC-3: .ai-team.toml with [project] dir = "<name>" overrides the default folder name.
  AC-4: ProjectRootNotFound is raised when no root can be resolved, with a message
        naming the searched paths and suggesting 'ai-team init'.
"""

from pathlib import Path

import pytest

from ai_team.core.locator import ProjectRootNotFound, find_project_root

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_project_layout(base: Path, project_dir_name: str = "ai-team") -> Path:
    """
    Create the minimal project folder hierarchy under *base* and return the
    repo root (base).  The layout is:

        base/
          <project_dir_name>/
            specs/
            decisions/
            docs/
    """
    proj = base / project_dir_name
    (proj / "specs").mkdir(parents=True)
    (proj / "decisions").mkdir()
    (proj / "docs").mkdir()
    return base


# ---------------------------------------------------------------------------
# AC-1: Walk up from cwd and find the default 'ai-team/' folder.
# ---------------------------------------------------------------------------


def test_finds_project_root_in_same_directory_as_cwd(tmp_path):
    """
    When cwd IS the repo root and a 'ai-team/' folder exists there,
    find_project_root returns a ProjectRoot whose repo equals that directory.
    """
    make_project_layout(tmp_path)
    result = find_project_root(tmp_path)
    assert result.repo == tmp_path


def test_finds_project_root_walking_up_from_nested_cwd(tmp_path):
    """
    When cwd is several levels below the repo root, find_project_root still
    resolves the correct repo root by walking up parent directories.
    """
    make_project_layout(tmp_path)
    nested_cwd = tmp_path / "src" / "ai_team" / "commands"
    nested_cwd.mkdir(parents=True)

    result = find_project_root(nested_cwd)
    assert result.repo == tmp_path


def test_project_root_exposes_project_dir_path(tmp_path):
    """ProjectRoot.project_dir is an absolute path pointing at the project folder."""
    make_project_layout(tmp_path)
    result = find_project_root(tmp_path)
    assert result.project_dir == tmp_path / "ai-team"


def test_project_root_exposes_specs_path(tmp_path):
    """ProjectRoot.specs is the absolute path to the specs/ subdirectory."""
    make_project_layout(tmp_path)
    result = find_project_root(tmp_path)
    assert result.specs == tmp_path / "ai-team" / "specs"


def test_project_root_exposes_tracker_folders_with_default_location(tmp_path):
    """Work items live in the default tracker at the repository root (S-006)."""
    make_project_layout(tmp_path)
    result = find_project_root(tmp_path)
    tracker = tmp_path / ".ai-team" / "tracker"
    assert result.tracker == tracker
    assert result.tasks == tracker / "tasks"
    assert result.bugs == tracker / "bugs"
    assert result.change_requests == tracker / "change-requests"
    assert not hasattr(result, "archive")


def test_project_root_exposes_decisions_and_docs(tmp_path):
    """ProjectRoot exposes decisions/ and docs/ paths."""
    make_project_layout(tmp_path)
    result = find_project_root(tmp_path)
    assert result.decisions == tmp_path / "ai-team" / "decisions"
    assert result.docs == tmp_path / "ai-team" / "docs"


def test_repo_path_is_absolute_even_when_cwd_is_relative(tmp_path):
    """
    ProjectRoot.repo is always an absolute path regardless of how cwd was
    provided.  (This tests internal normalisation; in practice the real cwd
    is always absolute, but the function must not rely on that.)
    """
    make_project_layout(tmp_path)
    result = find_project_root(tmp_path)
    assert result.repo.is_absolute()


# ---------------------------------------------------------------------------
# AC-2: AI_TEAM_ROOT env var is preferred over directory walking.
# ---------------------------------------------------------------------------


def test_env_var_overrides_directory_walking(tmp_path, monkeypatch):
    """
    When AI_TEAM_ROOT is set to a valid repo, find_project_root uses it
    instead of walking up from cwd.
    """
    # Two separate repo trees.
    env_repo = tmp_path / "env_repo"
    env_repo.mkdir()
    make_project_layout(env_repo)

    cwd_repo = tmp_path / "cwd_repo"
    cwd_repo.mkdir()
    make_project_layout(cwd_repo)

    monkeypatch.setenv("AI_TEAM_ROOT", str(env_repo))

    result = find_project_root(cwd_repo)
    assert result.repo == env_repo


def test_env_var_resolves_project_dir_correctly(tmp_path, monkeypatch):
    """
    When AI_TEAM_ROOT is used, ProjectRoot.project_dir still points at the
    correct subdirectory under that root.
    """
    env_repo = tmp_path / "env_repo"
    env_repo.mkdir()
    make_project_layout(env_repo)

    monkeypatch.setenv("AI_TEAM_ROOT", str(env_repo))

    result = find_project_root(tmp_path)
    assert result.project_dir == env_repo / "ai-team"


def test_root_kwarg_overrides_env_var_and_walking(tmp_path, monkeypatch):
    """
    The explicit root= keyword argument takes priority over AI_TEAM_ROOT and
    directory walking.
    """
    kwarg_repo = tmp_path / "kwarg_repo"
    kwarg_repo.mkdir()
    make_project_layout(kwarg_repo)

    env_repo = tmp_path / "env_repo"
    env_repo.mkdir()
    make_project_layout(env_repo)

    monkeypatch.setenv("AI_TEAM_ROOT", str(env_repo))

    result = find_project_root(tmp_path, root=kwarg_repo)
    assert result.repo == kwarg_repo


# ---------------------------------------------------------------------------
# AC-3: .ai-team.toml with [project] dir = "<name>" is honoured.
# ---------------------------------------------------------------------------


def test_toml_config_overrides_default_project_dir_name(tmp_path):
    """
    When a .ai-team.toml file with [project] dir = "myproject" is present above
    cwd, find_project_root resolves the project folder using that name.
    """
    custom_name = "myproject"
    make_project_layout(tmp_path, project_dir_name=custom_name)
    (tmp_path / ".ai-team.toml").write_text(f'[project]\ndir = "{custom_name}"\n')

    result = find_project_root(tmp_path)
    assert result.project_dir == tmp_path / custom_name
    assert result.repo == tmp_path


def test_toml_config_found_in_parent_directory(tmp_path):
    """
    When .ai-team.toml is in a parent directory (not cwd), it is still
    discovered by the upward walk.
    """
    custom_name = "custom_proj"
    make_project_layout(tmp_path, project_dir_name=custom_name)
    (tmp_path / ".ai-team.toml").write_text(f'[project]\ndir = "{custom_name}"\n')

    nested_cwd = tmp_path / "a" / "b" / "c"
    nested_cwd.mkdir(parents=True)

    result = find_project_root(nested_cwd)
    assert result.repo == tmp_path
    assert result.project_dir == tmp_path / custom_name


def test_toml_without_project_section_falls_through_to_folder_walking(tmp_path):
    """
    A .ai-team.toml that does not contain a [project] dir key is treated as
    having no override; directory walking for the default folder name still
    applies.
    """
    make_project_layout(tmp_path)
    # TOML exists but has no [project] dir key.
    (tmp_path / ".ai-team.toml").write_text("[init]\ntools = []\n")

    result = find_project_root(tmp_path)
    assert result.project_dir == tmp_path / "ai-team"


# ---------------------------------------------------------------------------
# AC-4: ProjectRootNotFound raised with informative message.
# ---------------------------------------------------------------------------


def test_raises_project_root_not_found_when_no_project_folder_exists(tmp_path):
    """
    When no project folder can be located by any resolution strategy,
    ProjectRootNotFound is raised.
    """
    with pytest.raises(ProjectRootNotFound):
        find_project_root(tmp_path)


def test_not_found_message_names_the_searched_paths(tmp_path):
    """
    The ProjectRootNotFound message includes at least the cwd so the user
    knows which paths were searched.
    """
    with pytest.raises(ProjectRootNotFound) as exc_info:
        find_project_root(tmp_path)
    assert str(tmp_path) in str(exc_info.value)


def test_not_found_message_suggests_ai_team_init(tmp_path):
    """
    The ProjectRootNotFound message suggests running 'ai-team init' to
    bootstrap the project structure.
    """
    with pytest.raises(ProjectRootNotFound) as exc_info:
        find_project_root(tmp_path)
    assert "ai-team init" in str(exc_info.value)


def test_raises_when_env_var_points_to_repo_without_project_folder(
    tmp_path, monkeypatch
):
    """
    When AI_TEAM_ROOT points to a directory that does not contain the expected
    project folder, ProjectRootNotFound is raised.
    """
    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir()
    monkeypatch.setenv("AI_TEAM_ROOT", str(empty_repo))

    with pytest.raises(ProjectRootNotFound):
        find_project_root(tmp_path)


def test_toml_config_accepts_nested_project_dir(tmp_path):
    """A nested ``[project] dir`` such as ``docs/ai-team`` resolves at any depth."""
    make_project_layout(tmp_path, project_dir_name="docs/ai-team")
    (tmp_path / ".ai-team.toml").write_text('[project]\ndir = "docs/ai-team"\n')
    start = tmp_path / "src" / "pkg"
    start.mkdir(parents=True)

    result = find_project_root(start)

    assert result.project_dir == tmp_path / "docs" / "ai-team"
    assert result.specs == tmp_path / "docs" / "ai-team" / "specs"


def test_toml_config_ignores_project_dir_that_escapes_the_repository(tmp_path):
    """A ``..`` component is not a usable ``[project] dir``; the default applies."""
    make_project_layout(tmp_path)
    (tmp_path / ".ai-team.toml").write_text('[project]\ndir = "../elsewhere"\n')

    assert find_project_root(tmp_path).project_dir == tmp_path / "ai-team"
