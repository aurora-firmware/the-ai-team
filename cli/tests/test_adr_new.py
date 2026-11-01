"""Tests for T-013: ai-team adr new command."""

import json
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from ai_team.core.models import parse_adr


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def test_adr_new_creates_decision_with_defaults_and_prints_absolute_path(
    monkeypatch, tmp_path
):
    """`ai-team adr new` creates one decision file and echoes its absolute path."""
    from ai_team.cli import app

    _mkdir(tmp_path / "ai-team" / "decisions")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["adr", "new", "Use event bus"])

    expected = tmp_path / "ai-team" / "decisions" / "ADR-001-use-event-bus.md"

    assert result.exit_code == 0
    assert result.stdout.strip() == str(expected)

    files = list((tmp_path / "ai-team" / "decisions").glob("*.md"))
    assert files == [expected]

    adr = parse_adr(expected)
    assert adr.id == "ADR-001"
    assert adr.title == "Use event bus"
    assert adr.status == "proposed"
    assert adr.created == date.today().isoformat()
    assert adr.supersedes is None


def test_adr_new_supports_custom_flags_and_json_output(monkeypatch, tmp_path):
    """`adr new --json` emits id/path and writes frontmatter from supplied flags."""
    from ai_team.cli import app

    _mkdir(tmp_path / "ai-team" / "decisions")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "adr",
            "new",
            "Use event bus",
            "--status",
            "superseded",
            "--supersedes",
            "ADR-010",
            "--json",
        ],
    )

    expected = tmp_path / "ai-team" / "decisions" / "ADR-001-use-event-bus.md"
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["id"] == "ADR-001"
    assert payload["supersedes"] == "ADR-010"
    assert payload["path"] == str(expected)
    assert "┏" not in result.stdout

    adr = parse_adr(expected)
    assert adr.id == "ADR-001"
    assert adr.title == "Use event bus"
    assert adr.status == "superseded"
    assert adr.created == date.today().isoformat()
    assert adr.supersedes == "ADR-010"


def test_adr_new_refuses_to_overwrite_when_allocated_path_exists(monkeypatch, tmp_path):
    """Existing output path causes non-zero exit and preserves file bytes."""
    from ai_team.cli import app

    decisions = tmp_path / "ai-team" / "decisions"
    _mkdir(decisions)

    existing = decisions / "ADR-001-use-event-bus.md"
    existing.write_text("existing bytes\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("ai_team.commands.adr.next_adr_id", lambda _root: "ADR-001")
    result = CliRunner().invoke(app, ["adr", "new", "Use event bus"])

    assert result.exit_code != 0
    assert "already exists" in result.stderr.lower()
    assert existing.read_text(encoding="utf-8") == "existing bytes\n"


def test_adr_new_fills_the_heading_with_id_and_title(monkeypatch, tmp_path):
    """`adr new` replaces the template heading placeholder with the ADR id and title."""
    from ai_team.cli import app

    _mkdir(tmp_path / "ai-team" / "decisions")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["adr", "new", "Use event bus"])

    assert result.exit_code == 0
    text = Path(result.stdout.strip()).read_text(encoding="utf-8")
    assert "# ADR-001: Use event bus" in text
    assert "[Decision Title]" not in text
