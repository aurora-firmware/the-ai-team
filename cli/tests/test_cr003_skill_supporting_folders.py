"""Skill supporting folders are copied into the scaffold export (CR-003 §7)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_init_scaffolds.py"

SKILL_TEXT = "---\nname: demo\ndescription: claude skill\n---\n\n# Body\n"

TEXT_ASSET = "project: {{project_dir}}\nbranch: {{integration_branch}}\n"
BINARY_ASSET = b"\xff\xfe\x00\x80binary\xc3\x28"


def _load_sync_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sync_init_scaffolds", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_skill(source_root: Path, name: str = "demo") -> Path:
    skill_dir = source_root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(SKILL_TEXT, encoding="utf-8")
    return skill_dir


def _add_supporting_folders(skill_dir: Path) -> None:
    (skill_dir / "assets").mkdir()
    (skill_dir / "assets" / "template.txt").write_text(TEXT_ASSET, encoding="utf-8")
    (skill_dir / "assets" / "logo.bin").write_bytes(BINARY_ASSET)
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "guide.md").write_text("ref\n", encoding="utf-8")
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "run.sh").write_text("echo hi\n", encoding="utf-8")


def _generate(source_root: Path, destination_root: Path) -> None:
    _load_sync_module()._replace_generated_skills(source_root, destination_root)


@pytest.mark.parametrize("tool", ["claude"])
def test_copies_supporting_folders_byte_for_byte_next_to_skill_md(
    tmp_path: Path, tool: str
) -> None:
    source_root = tmp_path / "sources"
    skill_dir = _make_skill(source_root)
    _add_supporting_folders(skill_dir)
    destination_root = tmp_path / "scaffolds"

    _generate(source_root, destination_root)

    exported = destination_root / tool / "skills" / "demo"
    assert (exported / "SKILL.md").read_text(encoding="utf-8") == SKILL_TEXT
    assert (exported / "assets" / "logo.bin").read_bytes() == BINARY_ASSET
    assert (exported / "assets" / "template.txt").read_bytes() == (
        skill_dir / "assets" / "template.txt"
    ).read_bytes()
    assert (exported / "references" / "guide.md").read_text(encoding="utf-8") == "ref\n"
    assert (exported / "scripts" / "run.sh").read_text(encoding="utf-8") == (
        "echo hi\n"
    )


@pytest.mark.parametrize("tool", ["claude"])
def test_leaves_placeholders_unchanged_in_copied_supporting_files(
    tmp_path: Path, tool: str
) -> None:
    source_root = tmp_path / "sources"
    _add_supporting_folders(_make_skill(source_root))
    destination_root = tmp_path / "scaffolds"

    _generate(source_root, destination_root)

    copied = destination_root / tool / "skills" / "demo" / "assets" / "template.txt"
    assert copied.read_text(encoding="utf-8") == TEXT_ASSET


@pytest.mark.parametrize("tool", ["claude"])
def test_does_not_export_other_files_or_folders_in_skill_directory(
    tmp_path: Path, tool: str
) -> None:
    source_root = tmp_path / "sources"
    skill_dir = _make_skill(source_root)
    _add_supporting_folders(skill_dir)
    (skill_dir / "notes.md").write_text("notes\n", encoding="utf-8")
    (skill_dir / "other").mkdir()
    (skill_dir / "other" / "x.txt").write_text("x\n", encoding="utf-8")
    destination_root = tmp_path / "scaffolds"

    _generate(source_root, destination_root)

    exported = destination_root / tool / "skills" / "demo"
    assert sorted(path.name for path in exported.iterdir()) == [
        "SKILL.md",
        "assets",
        "references",
        "scripts",
    ]


@pytest.mark.parametrize("tool", ["claude"])
def test_ignores_pycache_and_ds_store_in_supporting_folders(
    tmp_path: Path, tool: str
) -> None:
    source_root = tmp_path / "sources"
    skill_dir = _make_skill(source_root)
    _add_supporting_folders(skill_dir)
    (skill_dir / "scripts" / "__pycache__").mkdir()
    (skill_dir / "scripts" / "__pycache__" / "run.pyc").write_bytes(b"\x00")
    (skill_dir / "assets" / ".DS_Store").write_bytes(b"\x00")
    destination_root = tmp_path / "scaffolds"

    _generate(source_root, destination_root)

    exported = destination_root / tool / "skills" / "demo"
    assert not (exported / "scripts" / "__pycache__").exists()
    assert not (exported / "assets" / ".DS_Store").exists()


@pytest.mark.parametrize("tool", ["claude"])
def test_exports_only_skill_md_when_skill_has_no_supporting_folders(
    tmp_path: Path, tool: str
) -> None:
    source_root = tmp_path / "sources"
    _make_skill(source_root)
    destination_root = tmp_path / "scaffolds"

    _generate(source_root, destination_root)

    exported = destination_root / tool / "skills" / "demo"
    assert [path.name for path in exported.iterdir()] == ["SKILL.md"]


def test_copies_only_the_supporting_folders_that_exist(tmp_path: Path) -> None:
    source_root = tmp_path / "sources"
    skill_dir = _make_skill(source_root)
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "guide.md").write_text("ref\n", encoding="utf-8")
    destination_root = tmp_path / "scaffolds"

    _generate(source_root, destination_root)

    exported = destination_root / "claude" / "skills" / "demo"
    assert sorted(path.name for path in exported.iterdir()) == [
        "SKILL.md",
        "references",
    ]


def test_defines_copy_ignore_patterns_once_with_pycache_and_ds_store() -> None:
    patterns = _load_sync_module().COPY_IGNORE_PATTERNS

    assert patterns == ("__pycache__", ".DS_Store")


def test_excludes_every_shared_ignore_pattern_from_supporting_folder_and_replaced_tree(
    tmp_path: Path,
) -> None:
    module = _load_sync_module()
    source_root = tmp_path / "sources"
    skill_dir = _make_skill(source_root)
    _add_supporting_folders(skill_dir)
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "agent.md").write_text("agent\n", encoding="utf-8")
    for name in module.COPY_IGNORE_PATTERNS:
        (skill_dir / "scripts" / name).write_bytes(b"\x00")
        (agents_dir / name).write_bytes(b"\x00")
    destination_root = tmp_path / "scaffolds"
    replaced_tree = tmp_path / "replaced"

    module._replace_generated_skills(source_root, destination_root)
    module._replace_tree(agents_dir, replaced_tree)

    exported_scripts = destination_root / "claude" / "skills" / "demo" / "scripts"
    for name in module.COPY_IGNORE_PATTERNS:
        assert not (exported_scripts / name).exists()
        assert not (replaced_tree / name).exists()
    assert (replaced_tree / "agent.md").is_file()
