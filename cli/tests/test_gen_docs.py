"""
Tests for T-027: Add typer-cli dependency, gen_docs script, and generate commands.md.

Covers:
  AC-1: typer-cli is declared in the dev dependency group in pyproject.toml.
  AC-2: bash cli/scripts/gen_docs.sh regenerates cli/docs/commands.md
        from the Typer app.
  AC-5: Running gen_docs.sh twice with no code change produces a
        byte-identical commands.md.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_DIR = REPO_ROOT / "cli"
PYPROJECT = CLI_DIR / "pyproject.toml"
GEN_DOCS_SCRIPT = CLI_DIR / "scripts" / "gen_docs.sh"
COMMANDS_MD = CLI_DIR / "docs" / "commands.md"


def generate_docs_to(
    output: Path, cwd: Path = REPO_ROOT
) -> subprocess.CompletedProcess:
    """Run gen_docs.sh writing to ``output`` so tracked files stay untouched."""
    return subprocess.run(
        ["bash", str(GEN_DOCS_SCRIPT), "--output", str(output)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


# ---------------------------------------------------------------------------
# AC-1: typer-cli in the dev dependency group
# ---------------------------------------------------------------------------


def test_typer_cli_declared_in_dev_dependency_group():
    """pyproject.toml must list typer-cli in the [dependency-groups] dev group."""
    import tomllib

    content = PYPROJECT.read_bytes()
    data = tomllib.loads(content.decode("utf-8"))

    # Confirm typer-cli is in the dev dependency group.
    dev_deps = data.get("dependency-groups", {}).get("dev", [])
    # Each entry may be a string (e.g. "typer-cli>=0.24.0") or a dict.
    found_in_dev = any(isinstance(dep, str) and "typer-cli" in dep for dep in dev_deps)
    assert found_in_dev, (
        "typer-cli must be listed in [dependency-groups] dev in cli/pyproject.toml"
    )

    # Confirm typer-cli is NOT in the runtime [project] dependencies.
    runtime_deps = data.get("project", {}).get("dependencies", [])
    found_in_runtime = any(
        isinstance(dep, str) and "typer-cli" in dep for dep in runtime_deps
    )
    assert not found_in_runtime, (
        "typer-cli must not appear in the [project] runtime dependencies"
    )


# ---------------------------------------------------------------------------
# AC-2: gen_docs.sh exists and regenerates commands.md
# ---------------------------------------------------------------------------


def test_gen_docs_script_exists():
    """cli/scripts/gen_docs.sh must exist and be a regular file."""
    assert GEN_DOCS_SCRIPT.is_file(), f"Expected script not found: {GEN_DOCS_SCRIPT}"


def test_gen_docs_script_produces_commands_md(tmp_path):
    """Running gen_docs.sh --output creates the target file with non-empty content."""
    output = tmp_path / "commands.md"
    result = generate_docs_to(output)
    assert result.returncode == 0, (
        f"gen_docs.sh exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert output.is_file(), "gen_docs.sh --output did not create the target file"
    assert len(output.read_text(encoding="utf-8")) > 100, (
        "generated commands.md is unexpectedly short or empty"
    )


def test_committed_commands_md_matches_generated_output(tmp_path):
    """The committed commands.md must equal freshly generated output."""
    output = tmp_path / "commands.md"
    result = generate_docs_to(output)
    assert result.returncode == 0, f"gen_docs.sh failed: {result.stderr}"
    assert COMMANDS_MD.read_bytes() == output.read_bytes(), (
        "cli/docs/commands.md is stale. "
        "Regenerate it with: bash cli/scripts/gen_docs.sh"
    )


def test_gen_docs_default_output_path_is_committed_commands_md():
    """Without arguments the script still targets cli/docs/commands.md."""
    script = GEN_DOCS_SCRIPT.read_text(encoding="utf-8")
    assert 'OUTPUT="${REPO_ROOT}/cli/docs/commands.md"' in script


def test_gen_docs_resolves_relative_output_against_caller_cwd(tmp_path):
    """A relative --output lands under the caller's cwd, not the script's."""
    result = subprocess.run(
        ["bash", str(GEN_DOCS_SCRIPT), "--output", "relative.md"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, f"gen_docs.sh failed: {result.stderr}"
    assert (tmp_path / "relative.md").is_file()


@pytest.mark.parametrize("arguments", [["--bogus"], ["--output"]])
def test_gen_docs_rejects_invalid_arguments(arguments):
    """Unknown arguments or a missing --output value fail with a clear error."""
    result = subprocess.run(
        ["bash", str(GEN_DOCS_SCRIPT), *arguments],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0
    assert "usage" in result.stderr.lower()


# ---------------------------------------------------------------------------
# AC-5: idempotent generation
# ---------------------------------------------------------------------------


def test_gen_docs_is_idempotent(tmp_path):
    """Running gen_docs.sh twice produces byte-identical output."""
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    result1 = generate_docs_to(first)
    assert result1.returncode == 0, f"First gen_docs.sh run failed: {result1.stderr}"
    result2 = generate_docs_to(second)
    assert result2.returncode == 0, f"Second gen_docs.sh run failed: {result2.stderr}"

    assert first.read_bytes() == second.read_bytes(), (
        "generated output changed between two consecutive gen_docs.sh runs "
        "with no code change"
    )
