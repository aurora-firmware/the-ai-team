"""
Regression tests for B-027: docs must describe the package-owned source layout.

The scaffold sync script regenerates cli/src/ai_team/init/scaffolds/ from
cli/src/ai_team/init/sources/. The docs must not say it copies the repo-local
.claude/ folders, and the guides must not list TEMPLATE-*.md skill assets that
no part of the framework writes.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
USAGE_MD = REPO_ROOT / "cli" / "docs" / "usage.md"
CUSTOMIZATION_GUIDE = REPO_ROOT / "guides" / "customization-guide.md"
SETUP_GUIDE = REPO_ROOT / "guides" / "setup-guide.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"expected file not found: {path}"
    return path.read_text(encoding="utf-8")


def test_usage_md_does_not_say_sync_copies_repo_local_claude_folders():
    """usage.md must not describe the sync script as copying .claude/ into the package."""
    assert "copies the current" not in _read(USAGE_MD)


def test_usage_md_sync_paragraph_names_sources_and_generated_scaffolds():
    """The usage.md paragraph describing the sync script must name both source and output paths."""
    paragraphs = _read(USAGE_MD).split("\n\n")
    sync_paragraphs = [
        paragraph for paragraph in paragraphs if "sync_init_scaffolds.py`" in paragraph
    ]
    assert sync_paragraphs, "usage.md must describe sync_init_scaffolds.py in prose"
    sync_text = sync_paragraphs[0]
    assert "cli/src/ai_team/init/scaffolds/" in sync_text
    assert "cli/src/ai_team/init/sources/" in sync_text
    assert "copies" not in sync_text


def test_customization_guide_does_not_list_template_skill_assets():
    """customization-guide.md must not claim TEMPLATE-*.md files live in skill assets."""
    content = _read(CUSTOMIZATION_GUIDE)
    assert "TEMPLATE-" not in content
    assert "assets/" not in content


def test_setup_guide_does_not_list_template_skill_assets():
    """setup-guide.md must not claim or check TEMPLATE-*.md skill assets."""
    assert "TEMPLATE-" not in _read(SETUP_GUIDE)


def test_setup_guide_does_not_check_for_skill_assets_directories():
    """setup-guide.md verification must not ls skill assets/ folders that init never writes."""
    assert "/assets/" not in _read(SETUP_GUIDE)
