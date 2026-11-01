"""Tests for T-012: ai-team spec new command."""

import json
import threading
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from ai_team.core.models import parse_spec


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def test_spec_new_creates_spec_with_defaults_and_prints_absolute_path(
    monkeypatch, tmp_path
):
    """`ai-team spec new` creates one spec file at S-NNN-<slug>.md with default values."""
    from ai_team.cli import app

    _mkdir(tmp_path / "ai-team" / "specs")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "Launch Plan"])

    expected = tmp_path / "ai-team" / "specs" / "S-001-launch-plan.md"

    assert result.exit_code == 0
    assert result.stdout.strip() == str(expected)

    files = list((tmp_path / "ai-team" / "specs").glob("*.md"))
    assert files == [expected]

    spec = parse_spec(expected)
    assert spec.title == "Launch Plan"
    assert spec.version == "0.1"
    assert spec.status == "draft"
    assert spec.created == date.today().isoformat()
    assert spec.author == "planner"

    content = expected.read_text(encoding="utf-8")
    assert "id: S-001" in content


def test_spec_new_supports_custom_flags_and_json_output(monkeypatch, tmp_path):
    """`spec new --json` emits id/path at S-NNN-<slug>.md from supplied flags."""
    from ai_team.cli import app

    _mkdir(tmp_path / "ai-team" / "specs")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "spec",
            "new",
            "Auth Spec",
            "--author",
            "architect",
            "--status",
            "review",
            "--json",
        ],
    )

    expected = tmp_path / "ai-team" / "specs" / "S-001-auth-spec.md"
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["id"] == "S-001"
    assert payload["status"] == "review"
    assert payload["path"] == str(expected)
    assert "┏" not in result.stdout

    spec = parse_spec(expected)
    assert spec.title == "Auth Spec"
    assert spec.version == "0.1"
    assert spec.status == "review"
    assert spec.created == date.today().isoformat()
    assert spec.author == "architect"

    content = expected.read_text(encoding="utf-8")
    assert "id: S-001" in content


def test_spec_new_refuses_to_overwrite_when_allocated_path_exists(
    monkeypatch, tmp_path
):
    """Existing output path causes non-zero exit and preserves file bytes."""
    import ai_team.commands.spec as spec_mod
    from ai_team.cli import app

    specs = tmp_path / "ai-team" / "specs"
    _mkdir(specs)

    # Force the allocator to always return S-001 so we can pre-create the target.
    monkeypatch.setattr(spec_mod, "next_spec_id", lambda _root: "S-001")

    existing = specs / "S-001-launch-plan.md"
    existing.write_text("existing bytes\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "Launch Plan"])

    assert result.exit_code != 0
    assert "already exists" in result.stderr.lower()
    assert existing.read_text(encoding="utf-8") == "existing bytes\n"


def test_spec_new_substitutes_body_h1_with_provided_title(monkeypatch, tmp_path):
    """`spec new` replaces the body H1 placeholder with the provided title."""
    from ai_team.cli import app

    _mkdir(tmp_path / "ai-team" / "specs")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "My New Spec"])

    assert result.exit_code == 0

    expected = tmp_path / "ai-team" / "specs" / "S-001-my-new-spec.md"
    content = expected.read_text(encoding="utf-8")

    assert "# My New Spec" in content
    assert "# [Specification Title]" not in content


def test_spec_new_allocates_next_id_from_existing_spec_frontmatter(
    monkeypatch, tmp_path
):
    """Allocator should use existing spec frontmatter IDs, not filename patterns."""
    from ai_team.cli import app

    specs_dir = tmp_path / "ai-team" / "specs"
    _mkdir(specs_dir)
    (specs_dir / "the-intern-agent-service-architecture.md").write_text(
        """---
id: S-001
title: "The Intern Agent Service Architecture"
version: "0.1"
status: approved
created: 2026-05-16
author: planner
---

# The Intern Agent Service Architecture
""",
        encoding="utf-8",
    )
    (specs_dir / "bob-service-shell-architecture.md").write_text(
        """---
id: S-002
title: "Bob Service Shell Architecture"
version: "0.1"
status: approved
created: 2026-05-16
author: planner
---

# Bob Service Shell Architecture
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "Verification Spec", "--json"])

    expected = specs_dir / "S-003-verification-spec.md"
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["id"] == "S-003"
    assert payload["path"] == str(expected)
    assert "id: S-003" in expected.read_text(encoding="utf-8")


def test_spec_new_allocates_distinct_ids_for_two_concurrent_callers(
    monkeypatch, tmp_path
):
    """B-014: two racing `new_spec` calls must never write the same S-NNN id.

    ``CliRunner.invoke`` is not thread-safe (it patches global ``sys.stdout``
    per call), so this drives ``new_spec`` directly. It reproduces the
    diagnosed race deterministically by delaying the *first* caller's
    ``slugify`` call (the step between "id computed" and "file written") with
    a ``threading.Event`` -- never ``time.sleep`` -- so the second caller's
    directory scan is forced to attempt to run while the first is still
    mid-critical-section.
    """
    import ai_team.commands.spec as spec_cmd

    specs_dir = tmp_path / "ai-team" / "specs"
    _mkdir(specs_dir / "archive")

    monkeypatch.chdir(tmp_path)

    real_slugify = spec_cmd.slugify
    call_count = {"value": 0}
    count_lock = threading.Lock()
    first_call_started = threading.Event()
    release_first_call = threading.Event()

    def patched_slugify(title: str) -> str:
        with count_lock:
            call_count["value"] += 1
            this_call = call_count["value"]
        result = real_slugify(title)
        if this_call == 1:
            first_call_started.set()
            assert release_first_call.wait(timeout=5), "never released"
        return result

    monkeypatch.setattr(spec_cmd, "slugify", patched_slugify)

    errors: list[BaseException] = []

    def worker(title: str) -> None:
        try:
            spec_cmd.new_spec(
                title=title,
                author="planner",
                status="draft",
                overview=False,
                as_json=False,
            )
        except BaseException as exc:  # noqa: BLE001 - surfaced via `errors`
            errors.append(exc)

    t1 = threading.Thread(target=worker, args=("Parallel Alpha",))
    t1.start()
    assert first_call_started.wait(timeout=5)

    t2 = threading.Thread(target=worker, args=("Parallel Beta",))
    t2.start()
    t2.join(timeout=1)
    assert t2.is_alive(), "second caller should still be blocked by the lock"

    release_first_call.set()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert not t1.is_alive()
    assert not t2.is_alive()

    assert errors == []

    files = sorted(specs_dir.glob("S-*.md"))
    assert len(files) == 2
    ids = {parse_spec(path).id for path in files}
    assert len(ids) == 2, f"expected two distinct spec ids, got files: {files}"


def _specs_dir(tmp_path: Path) -> Path:
    specs = tmp_path / "ai-team" / "specs"
    _mkdir(specs)
    return specs


def test_spec_new_overview_creates_s_000_from_system_overview_template(
    monkeypatch, tmp_path
):
    from ai_team.cli import app

    specs = _specs_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "--overview", "Acme Overview"])

    expected = specs / "S-000-acme-overview.md"
    assert result.exit_code == 0
    assert result.stdout.strip() == str(expected)
    content = expected.read_text(encoding="utf-8")
    assert "id: S-000" in content
    assert "# Acme Overview" in content
    assert "# [Specification Title]" not in content
    assert "system overview spec (S-000)" in content


def test_spec_new_overview_json_emits_the_spec_object(monkeypatch, tmp_path):
    from ai_team.cli import app

    specs = _specs_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "--overview", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == "S-000"
    assert payload["status"] == "draft"
    assert payload["path"] == str(specs / "S-000-system-overview.md")


def test_spec_new_overview_defaults_title_to_system_overview(monkeypatch, tmp_path):
    from ai_team.cli import app

    specs = _specs_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "--overview"])

    assert result.exit_code == 0
    spec = parse_spec(specs / "S-000-system-overview.md")
    assert spec.title == "System Overview"


def test_spec_new_overview_refuses_when_s_000_exists_in_specs(monkeypatch, tmp_path):
    from ai_team.cli import app

    specs = _specs_dir(tmp_path)
    (specs / "S-000-existing.md").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "--overview"])

    assert result.exit_code == 1
    assert "S-000" in result.stderr
    assert sorted(p.name for p in specs.glob("*.md")) == ["S-000-existing.md"]


def test_spec_new_overview_refuses_when_s_000_exists_in_archive(monkeypatch, tmp_path):
    from ai_team.cli import app

    specs = _specs_dir(tmp_path)
    _mkdir(specs / "archive")
    (specs / "archive" / "old.md").write_text("---\nid: S-000\n---\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new", "--overview"])

    assert result.exit_code == 1
    assert "S-000" in result.stderr
    assert list(specs.glob("*.md")) == []


def test_spec_new_without_title_and_without_overview_fails(monkeypatch, tmp_path):
    from ai_team.cli import app

    specs = _specs_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["spec", "new"])

    assert result.exit_code != 0
    assert list(specs.glob("*.md")) == []


def test_spec_new_allocates_s_001_when_s_000_is_the_only_spec(monkeypatch, tmp_path):
    from ai_team.cli import app

    specs = _specs_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    CliRunner().invoke(app, ["spec", "new", "--overview"])
    result = CliRunner().invoke(app, ["spec", "new", "Feature"])

    assert result.exit_code == 0
    assert result.stdout.strip() == str(specs / "S-001-feature.md")
