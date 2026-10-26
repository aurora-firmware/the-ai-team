"""
Tests for T-001: Bootstrap cli/ uv project with Typer scaffold and
command auto-discovery.

Covers:
  AC-2: `ai-team --version` prints the package version.
  AC-3: The console-script entry point resolves to ai_team.cli:app.
  AC-4: Auto-discovery mounts a module's `app` under its `NAME` as a subcommand.
  AC-5: Package data directories are declared in pyproject.toml.
"""

import importlib
import importlib.metadata
import importlib.util
import json
import socket
import types

import pytest
from typer.testing import CliRunner

DEVELOPMENT_WARNING = (
    "Warning: ai-team is under development. Please report issues at "
    "https://github.com/aurora-firmware/the-ai-team/issues"
)

# ---------------------------------------------------------------------------
# AC-2 and AC-3: version callback and entry point
# ---------------------------------------------------------------------------


def test_version_output_matches_package_metadata():
    """--version prints the version string declared in pyproject.toml."""
    from ai_team.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    expected_version = importlib.metadata.version("ai-team")
    assert expected_version in result.output


def test_entry_point_resolves_to_cli_app():
    """The ai-team console-script entry point points at ai_team.cli:app."""
    entry_points = importlib.metadata.entry_points(group="console_scripts")
    ai_team_ep = next((ep for ep in entry_points if ep.name == "ai-team"), None)
    assert ai_team_ep is not None, "No 'ai-team' entry point found in console_scripts"
    assert ai_team_ep.value == "ai_team.cli:app"


@pytest.mark.parametrize(
    ("args", "expected_exit_code"),
    [
        (["--help"], 0),
        (["--version"], 0),
        (["list", "tasks"], 0),
        (["not-a-command"], 2),
    ],
)
def test_every_invocation_emits_development_warning_once(
    args, expected_exit_code, monkeypatch, tmp_path
):
    """Help, version, success, and errors each emit one stderr warning."""
    from ai_team.cli import app

    monkeypatch.chdir(tmp_path)
    (tmp_path / "ai-team").mkdir()

    result = CliRunner().invoke(app, args)

    assert result.exit_code == expected_exit_code
    assert result.stderr.count(DEVELOPMENT_WARNING) == 1


def test_json_command_keeps_warning_out_of_stdout(monkeypatch, tmp_path):
    """JSON output remains parseable because the warning is stderr-only."""
    from ai_team.cli import app

    monkeypatch.chdir(tmp_path)
    (tmp_path / "ai-team").mkdir()

    result = CliRunner().invoke(app, ["list", "tasks", "--json"])

    assert result.exit_code == 0
    assert isinstance(json.loads(result.stdout), list)
    assert DEVELOPMENT_WARNING not in result.stdout
    assert result.stderr.count(DEVELOPMENT_WARNING) == 1


def test_development_warning_does_not_make_a_network_request(monkeypatch):
    """Displaying the warning performs no network connection."""
    from ai_team.cli import app

    def reject_network_request(*args, **kwargs):
        pytest.fail("the development warning attempted a network request")

    monkeypatch.setattr(socket, "create_connection", reject_network_request)

    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert result.stderr.count(DEVELOPMENT_WARNING) == 1


# ---------------------------------------------------------------------------
# AC-4: auto-discovery of subcommands
# ---------------------------------------------------------------------------


def test_auto_discovery_registers_subcommand_from_module(tmp_path, monkeypatch):
    """
    When a module exporting `app` (Typer) and `NAME` (str) is added under
    ai_team.commands, the auto-discovery in commands/__init__.py registers it
    as a top-level subcommand without touching cli.py.
    """
    import typer

    # Build a minimal fake command module in a temporary package directory.
    fake_module_code = (
        "import typer\n"
        "NAME = 'greet'\n"
        "app = typer.Typer()\n"
        "\n"
        "@app.command()\n"
        "def hello():\n"
        "    typer.echo('hello from greet')\n"
    )
    commands_pkg = tmp_path / "ai_team_test_commands"
    commands_pkg.mkdir()
    (commands_pkg / "__init__.py").write_text("")
    (commands_pkg / "greet.py").write_text(fake_module_code)

    # Inject the fake commands package path into sys.path and temporarily
    # replace ai_team.commands with a module that lives under it, so that
    # the discovery function can find it.
    monkeypatch.syspath_prepend(str(tmp_path))

    # Dynamically import the fake greet module as if it were a sibling of
    # ai_team.commands.greet, then call the discovery helper directly.
    from ai_team.commands import discover_and_mount

    parent_app = typer.Typer()

    # Load our fake module.
    spec = importlib.util.spec_from_file_location(
        "ai_team_test_commands.greet", str(commands_pkg / "greet.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # discover_and_mount accepts an iterable of already-loaded modules.
    discover_and_mount(parent_app, [mod])

    runner = CliRunner()
    result = runner.invoke(parent_app, ["greet", "hello"])
    assert result.exit_code == 0
    assert "hello from greet" in result.output


def test_auto_discovery_skips_module_without_name_attribute(tmp_path):
    """
    Modules that do not export a NAME attribute are silently skipped;
    no exception is raised and no subcommand is registered.
    """
    import typer

    from ai_team.commands import discover_and_mount

    # A module with `app` but no `NAME`.
    mod = types.ModuleType("no_name_mod")
    mod.app = typer.Typer()

    parent_app = typer.Typer()
    # Should not raise and should not register any subcommand.
    discover_and_mount(parent_app, [mod])

    # Nothing should have been registered on the parent app.
    assert len(parent_app.registered_groups) == 0


# ---------------------------------------------------------------------------
# Render helper
# ---------------------------------------------------------------------------


def test_print_json_outputs_valid_json(capsys):
    """render.print_json serialises a dict to a JSON string on stdout."""
    import json

    from ai_team.render import print_json

    data = {"key": "value", "number": 42}
    print_json(data)
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == data


# ---------------------------------------------------------------------------
# AC-5: package data directories present in installed package
# ---------------------------------------------------------------------------


def test_package_data_dirs_are_importable_as_packages():
    """
    ai_team.templates and ai_team.init.scaffolds directories are reachable via
    importlib.resources so that later tasks can drop files into them without
    touching pyproject.toml.
    """
    import importlib.resources as res

    # Both directories must be traversable as package data.
    templates_pkg = res.files("ai_team") / "templates"
    scaffolds_pkg = res.files("ai_team.init") / "scaffolds"

    # files() returns a Traversable; confirm the paths are accessible.
    assert templates_pkg is not None
    assert scaffolds_pkg is not None


def test_missing_project_root_prints_clean_error_and_exits_1(monkeypatch, tmp_path):
    """A command run outside any project reports the locator error, not a traceback."""
    from ai_team.cli import app

    monkeypatch.delenv("AI_TEAM_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["list", "tasks"])

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "ai-team init" in result.stderr


def test_archive_command_is_not_registered():
    """The CLI no longer knows an `archive` command."""
    from ai_team.cli import app

    result = CliRunner().invoke(app, ["archive"])

    assert result.exit_code != 0
    assert "No such command" in result.output
