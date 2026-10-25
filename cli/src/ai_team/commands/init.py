"""`ai-team init` command for scaffolding a fresh repository."""

from __future__ import annotations

import copy
import importlib.metadata
import importlib.resources as resources
import shutil
from dataclasses import dataclass
from pathlib import Path

import tomli_w
import typer

from ai_team.core.config import (
    DEFAULT_INTEGRATION_BRANCH,
    is_valid_branch_name,
    is_valid_project_dir,
    marker_integration_branch,
    marker_project_dir,
    read_marker,
    render_placeholders,
)
from ai_team.core.locator import DEFAULT_PROJECT_DIR
from ai_team.core.tool_paths import TOOL_EXPORT_PATHS, framework_skill_names
from ai_team.core.tracker import DEFAULT_TRACKER_DIR, resolve_tracker_dir

NAME = "init"
app = typer.Typer(
    help="Scaffold an AI-team repository.",
    invoke_without_command=True,
    context_settings={"allow_interspersed_args": True},
)

_SUPPORTED_TOOLS = ["claude", "codex"]

_ROOT_GUIDANCE_FILES = ["CLAUDE.md", "AGENTS.md"]

# Project skeleton files that belong to the project once written: init creates
# them only when missing, so a framework upgrade keeps the project's own copy.
_KEEP_IF_EXISTS_PROJECT_FILES = [Path("docs") / "coding_guidelines.md"]

# The ai-team docs an upgrade offers to refresh, relative to the project directory.
_PROJECT_DOC_FILES = ["AGENTS.md", "CLAUDE.md", ".gitignore"]

_UPDATE_DOCS_QUESTION = (
    "Update the ai-team docs (AGENTS.md, CLAUDE.md, .gitignore) in {project_dir}?"
)
_UPDATE_SKILLS_QUESTION = "Update the agents and skills for the configured tools?"

_ROOT_GUIDANCE_DECLINED_MESSAGE = (
    "To help agents run your project without guessing, add your test and run "
    "commands to a root CLAUDE.md and AGENTS.md. "
    "See `ai-team init --create-root-guidance` to generate starter templates."
)


def _iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def _tracker_ignore_rule(tracker_dir: str) -> str | None:
    """Return the root ``.gitignore`` rule for the configured tracker folder.

    The default folder keeps its historical rule (the whole ``/.ai-team/``
    folder); any other relative folder is ignored by its full path. Absolute
    and ``~`` paths live outside the repository and need no rule.
    """
    configured = Path(tracker_dir).expanduser()
    if configured.is_absolute():
        return None
    if tracker_dir == DEFAULT_TRACKER_DIR:
        return f"/{Path(DEFAULT_TRACKER_DIR).parts[0]}/"
    return f"/{configured.as_posix().strip('/')}/"


def _plan_copies(source: Path, destination: Path) -> list[tuple[Path, Path]]:
    return [
        (path, destination / path.relative_to(source)) for path in _iter_files(source)
    ]


def _plan_project_copies(source: Path, project_root: Path) -> list[tuple[Path, Path]]:
    """Plan the project skeleton copies, leaving out kept-if-existing files."""
    return [
        (path, destination)
        for path, destination in _plan_copies(source, project_root)
        if not (
            destination.exists()
            and destination.relative_to(project_root) in _KEEP_IF_EXISTS_PROJECT_FILES
        )
    ]


def _parse_tools(value: str) -> list[str]:
    token = value.strip().lower()
    if token == "all":
        return _SUPPORTED_TOOLS[:]
    if token == "none":
        return []

    result: list[str] = []
    for chunk in token.split(","):
        name = chunk.strip().lower()
        if not name:
            continue
        if name not in _SUPPORTED_TOOLS:
            raise ValueError(
                f"Unsupported tool '{name}'. Supported values: "
                + ", ".join(_SUPPORTED_TOOLS + ["all", "none"])
            )
        if name not in result:
            result.append(name)
    return result


def _resolve_tools(tools: str | None, no_interactive: bool) -> list[str]:
    if tools is not None:
        return _parse_tools(tools)
    if no_interactive:
        raise ValueError("When --no-interactive is set, you must provide --tools.")

    raw = typer.prompt(
        "Select tools (comma-separated, all, none)",
        default="claude",
    )
    return _parse_tools(raw)


def _configured_tools(marker: dict) -> list[str] | None:
    """Return the valid ``[init] tools`` of a parsed marker, else None."""
    value = marker.get("init", {}).get("tools")
    if isinstance(value, list) and all(tool in _SUPPORTED_TOOLS for tool in value):
        return list(value)
    return None


def _resolve_upgrade_tools(
    tools: str | None, marker: dict, no_interactive: bool
) -> list[str]:
    """Take the tools from ``--tools``, else from the marker, else ask as for a new run."""
    if tools is None:
        configured = _configured_tools(marker)
        if configured is not None:
            return configured
    return _resolve_tools(tools, no_interactive)


def _upgraded_marker(
    existing: dict,
    project_dir: str,
    integration_branch: str,
    tools: list[str],
    is_skills_updated: bool,
) -> dict:
    """Return *existing* with only the settings that differ from it changed.

    ``framework_version`` is set to the running version only when the agents
    and skills are updated; otherwise it is left alone.
    """
    data = copy.deepcopy(existing)
    changes = [
        (
            "project",
            "dir",
            project_dir,
            marker_project_dir(existing) or DEFAULT_PROJECT_DIR,
        ),
        (
            "git",
            "integration_branch",
            integration_branch,
            marker_integration_branch(existing) or DEFAULT_INTEGRATION_BRANCH,
        ),
        ("init", "tools", tools, _configured_tools(existing)),
    ]
    if is_skills_updated:
        changes.append(
            (
                "init",
                "framework_version",
                importlib.metadata.version("ai-team"),
                existing.get("init", {}).get("framework_version"),
            )
        )
    for table, key, value, current in changes:
        if value != current:
            data.setdefault(table, {})[key] = value
    return data


@dataclass
class _UpgradeRequest:
    """Everything one upgrade run needs, gathered once by ``init_command``."""

    target_root: Path
    scaffolds_path: Path
    project_dir: str
    tools: list[str]
    settings: dict[str, str]
    existing_marker: dict
    update_docs: bool
    update_skills: bool
    no_interactive: bool
    dry_run: bool


def _would_verb(destination: Path) -> str:
    return "WOULD OVERWRITE" if destination.exists() else "WOULD WRITE"


def _ask_upgrade_question(
    question: str,
    is_answered_yes: bool,
    covered: list[Path],
    request: _UpgradeRequest,
) -> bool:
    """Answer one upgrade question; return True when it is answered yes.

    A dry run never prompts: it names the files an unanswered question would
    prompt for and, for an answered one, the files it would write. The caller
    writes only when the answer is yes and the run is not a dry run.
    """
    if is_answered_yes:
        answer = True
    elif request.no_interactive:
        answer = False
    elif request.dry_run:
        for destination in covered:
            typer.echo(f"WOULD PROMPT: {destination}")
        return False
    else:
        answer = typer.confirm(question, default=False)

    if answer and request.dry_run:
        for destination in covered:
            typer.echo(f"{_would_verb(destination)}: {destination}")
        return True
    return answer


def _write_all(plan: list[tuple[Path, Path]], settings: dict[str, str]) -> None:
    for source, destination in plan:
        _write_rendered(source, destination, settings)


def _upgrade_marker(
    request: _UpgradeRequest, integration_branch: str, is_skills_updated: bool
) -> None:
    marker = request.target_root / ".ai-team.toml"
    data = _upgraded_marker(
        request.existing_marker,
        request.project_dir,
        integration_branch,
        request.tools,
        is_skills_updated,
    )
    if data == request.existing_marker:
        return
    if request.dry_run:
        typer.echo(f"WOULD OVERWRITE: {marker}")
        return
    marker.write_text(tomli_w.dumps(data), encoding="utf-8")
    _report_write(marker, existed=True)


def _stale_definitions(request: _UpgradeRequest) -> list[Path]:
    """Return agents and skills in the tool folders that the running version does not ship."""
    stale: list[Path] = []
    for tool in request.tools:
        for scaffold_subfolder, destination in TOOL_EXPORT_PATHS[tool]:
            shipped = {
                entry.name
                for entry in (
                    request.scaffolds_path / tool / scaffold_subfolder
                ).iterdir()
            }
            installed = request.target_root / destination
            if not installed.is_dir():
                continue
            stale.extend(
                entry
                for entry in sorted(installed.iterdir())
                if entry.name not in shipped
            )
    return stale


def _warn_about_stale_definitions(stale: list[Path]) -> None:
    if not stale:
        return
    typer.echo(
        "Warning: these skills or agents are not shipped by this version of ai-team; "
        "they were neither updated nor removed:\n"
        + "\n".join(f"- {path}" for path in stale),
        err=True,
    )


def _recreate_missing_skeleton(
    plan: list[tuple[Path, Path]], request: _UpgradeRequest
) -> None:
    """Write files that are missing and that no upgrade question covers."""
    if request.dry_run:
        for _, destination in plan:
            typer.echo(f"{_would_verb(destination)}: {destination}")
    else:
        _write_all(plan, request.settings)


def _plan_tool_copies(
    tools: list[str], request: _UpgradeRequest
) -> list[tuple[Path, Path]]:
    """Return the (source, destination) pairs of every agent and skill of *tools*."""
    plan: list[tuple[Path, Path]] = []
    for tool in tools:
        for scaffold_subfolder, destination in TOOL_EXPORT_PATHS[tool]:
            plan.extend(
                _plan_copies(
                    request.scaffolds_path / tool / scaffold_subfolder,
                    request.target_root / destination,
                )
            )
    return plan


def _run_upgrade(request: _UpgradeRequest) -> None:
    """Upgrade a repository that already has ``.ai-team.toml``.

    Settings are kept, a missing project directory is recreated, and the docs
    and the agents and skills are rewritten only where their question is yes.
    """
    if request.dry_run:
        typer.echo("CASE: upgrade")
    project_root = request.target_root / request.project_dir
    project_plan = _plan_project_copies(
        request.scaffolds_path / "project", project_root
    )
    docs = {project_root / name for name in _PROJECT_DOC_FILES}

    if project_root.is_dir():
        docs_plan = [(s, d) for s, d in project_plan if d in docs]
        recreated = [
            (s, d) for s, d in project_plan if d not in docs and not d.exists()
        ]
    else:
        docs_plan = []
        recreated = project_plan
    _recreate_missing_skeleton(recreated, request)

    configured_tools = _configured_tools(request.existing_marker) or []
    added_tools = [tool for tool in request.tools if tool not in configured_tools]
    skills_plan = _plan_tool_copies(
        [tool for tool in request.tools if tool in configured_tools], request
    )
    # No question covers a newly added tool, so only its missing files are
    # written: a tool dropped earlier keeps its files, and they stay untouched.
    added_plan = [
        (s, d) for s, d in _plan_tool_copies(added_tools, request) if not d.exists()
    ]
    _recreate_missing_skeleton(added_plan, request)

    answers: list[bool] = []
    for question, is_yes, plan in (
        (
            _UPDATE_DOCS_QUESTION.format(project_dir=request.project_dir),
            request.update_docs,
            docs_plan,
        ),
        (_UPDATE_SKILLS_QUESTION, request.update_skills, skills_plan),
    ):
        is_answered_yes = _ask_upgrade_question(
            question, is_yes, [d for _, d in plan], request
        )
        answers.append(is_answered_yes)
        if is_answered_yes and not request.dry_run:
            _write_all(plan, request.settings)

    is_skills_updated = answers[1]
    # Dropping codex, or adding it in this run, never removes legacy folders.
    is_codex_kept = "codex" in configured_tools and "codex" in request.tools
    if is_skills_updated and is_codex_kept:
        _remove_legacy_codex_skills(request.target_root, request.dry_run)
    if is_skills_updated:
        _warn_about_stale_definitions(_stale_definitions(request))
    _upgrade_marker(request, request.settings["integration_branch"], is_skills_updated)


_ADOPTION_QUESTION = "Overwrite these existing files?"


def _decide_adoption_overwrite(
    collisions: list[Path], force: bool, no_interactive: bool, dry_run: bool
) -> bool | None:
    """Answer the single adoption question; None means a dry run left it unanswered.

    ``--force`` answers yes, ``--no-interactive`` answers no, and a dry run never
    prompts. The real run and the dry run both use this, so they cannot disagree.
    """
    if not collisions or force:
        return True
    if no_interactive:
        return False
    if dry_run:
        return None
    typer.echo("These files already exist:\n" + "\n".join(f"- {p}" for p in collisions))
    return typer.confirm(_ADOPTION_QUESTION, default=False)


def _report_skipped(skipped: list[Path]) -> None:
    typer.echo(
        "Kept existing files (not overwritten):\n"
        + "\n".join(f"- {path}" for path in skipped),
        err=True,
    )


def _skill_invocation(skill: str, tools: list[str]) -> str:
    """Return how to invoke ``skill`` in the configured tools.

    Claude Code runs a skill as ``/name``; Codex has no per-skill slash command
    and runs it as ``$name``. With no tool configured, keep the ``/name`` form.
    """
    if tools == ["codex"]:
        return f"${skill}"
    if "claude" in tools and "codex" in tools:
        return f"/{skill} (Claude Code) or ${skill} (Codex)"
    return f"/{skill}"


def _next_steps(tools: list[str]) -> list[str]:
    return [
        f"Run {_skill_invocation('brainstorm', tools)} to explore the request and constraints.",
        f"Run {_skill_invocation('spec-breakdown', tools)} to break the approved spec into tasks.",
        f"Run {_skill_invocation('dev-loop', tools)} to execute tasks through review and integration.",
    ]


def _ensure_tracker(target_root: Path, tracker_dir: str, dry_run: bool) -> None:
    """Create the configured tracker folder and make git ignore it (spec S-006).

    The folder is the one every tracker command resolves, so in a linked
    worktree it is created in the main working tree.

    The ignore rule is appended to the repository's root ``.gitignore`` only when
    no identical line exists, so re-running ``init`` never duplicates or removes
    rules.

    The real run reports ``CREATED`` and ``UPDATED`` for the same cases its dry
    run reports ``WOULD CREATE`` and ``WOULD UPDATE``.
    """
    tracker = resolve_tracker_dir(target_root)
    ignore_rule = _tracker_ignore_rule(tracker_dir)
    gitignore = target_root / ".gitignore"
    existing = (
        gitignore.read_text(encoding="utf-8").splitlines()
        if gitignore.is_file()
        else []
    )
    needs_rule = ignore_rule is not None and ignore_rule not in (
        line.strip() for line in existing
    )

    if dry_run:
        if not tracker.exists():
            typer.echo(f"WOULD CREATE: {tracker}")
        if needs_rule:
            typer.echo(f"WOULD UPDATE: {gitignore}")
        return

    is_tracker_missing = not tracker.exists()
    tracker.mkdir(parents=True, exist_ok=True)
    if is_tracker_missing:
        typer.echo(f"CREATED: {tracker}")
    if needs_rule:
        prefix = ""
        if existing:
            text = gitignore.read_text(encoding="utf-8")
            prefix = "" if text.endswith("\n") else "\n"
            prefix += "\n"
        with gitignore.open("a", encoding="utf-8") as stream:
            stream.write(
                f"{prefix}# ai-team local work-item tracker (tasks, bugs, change-requests)\n"
                f"{ignore_rule}\n"
            )
        typer.echo(f"UPDATED: {gitignore}")


def _write_rendered(source: Path, destination: Path, settings: dict[str, str]) -> None:
    """Copy *source* to *destination*, filling the packaged-source placeholders.

    A source that is not valid UTF-8 (for example an image) is copied byte for
    byte, without placeholder substitution.

    Reports ``OVERWROTE: <path>`` once the write succeeds when *destination*
    already existed, and ``WROTE: <path>`` when it did not.
    """
    existed = destination.exists()
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_bytes()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        destination.write_bytes(content)
    else:
        destination.write_text(render_placeholders(text, **settings), encoding="utf-8")
    shutil.copymode(source, destination)
    _report_write(destination, existed)


def _report_write(destination: Path, existed: bool) -> None:
    verb = "OVERWROTE" if existed else "WROTE"
    typer.echo(f"{verb}: {destination}")


def _copy_root_guidance_file(
    source: Path,
    destination: Path,
    force: bool,
    settings: dict[str, str],
) -> None:
    """Copy a single root guidance file; overwrite only when *force* is True."""
    if destination.exists() and not force:
        return
    _write_rendered(source, destination, settings)


def _root_guidance_action(
    destination: Path,
    force: bool,
    create_root_guidance: bool,
    no_interactive: bool,
) -> str:
    """Decide what ``init`` does with one root guidance file.

    Returns ``"skip"``, ``"write"`` or ``"prompt"``. The real run and the dry
    run both use this, so the dry run cannot disagree with the real run.
    """
    if destination.exists() and not force:
        return "skip"
    if create_root_guidance:
        return "write"
    if no_interactive:
        return "skip"
    return "prompt"


def _would_write_verb(destination: Path, force: bool) -> str:
    return "WOULD OVERWRITE" if destination.exists() and force else "WOULD WRITE"


def _handle_root_guidance(
    target_root: Path,
    sources_root: Path,
    no_interactive: bool,
    create_root_guidance: bool,
    force: bool,
    dry_run: bool,
    settings: dict[str, str],
) -> bool:
    """Prompt for or create root guidance files.  Returns True if any file was declined."""
    declined = False

    for filename in _ROOT_GUIDANCE_FILES:
        destination = target_root / filename
        source = sources_root / "root" / filename
        action = _root_guidance_action(
            destination, force, create_root_guidance, no_interactive
        )

        if dry_run:
            if action == "write":
                typer.echo(f"{_would_write_verb(destination, force)}: {destination}")
            elif action == "prompt":
                typer.echo(f"WOULD PROMPT: {destination}")
        elif action == "write":
            _copy_root_guidance_file(source, destination, force, settings)
        elif action == "prompt":
            create = typer.confirm(
                f"Create root {filename} from the starter template?",
                default=True,
            )
            if create:
                _copy_root_guidance_file(source, destination, force, settings)
            else:
                declined = True

    return declined


def _remove_legacy_codex_skills(target_root: Path, dry_run: bool) -> None:
    """Remove framework skill copies left in ``.codex/skills`` by older releases.

    Codex lists same-named skills from ``.codex/skills`` and ``.agents/skills``
    side by side, so the old framework copies would show every skill twice.
    Folders the framework does not own are left alone, and the legacy root is
    removed only once it is empty. With *dry_run* nothing changes.
    """
    legacy_root = target_root / ".codex" / "skills"
    if not legacy_root.is_dir():
        return

    framework_names = set(framework_skill_names("codex"))
    for folder in sorted(path for path in legacy_root.iterdir() if path.is_dir()):
        if folder.name not in framework_names:
            typer.echo(f"LEFT IN PLACE: {folder}")
        elif dry_run:
            typer.echo(f"WOULD REMOVE: {folder}")
        else:
            if folder.is_symlink():
                folder.unlink()
            else:
                shutil.rmtree(folder)
            typer.echo(f"REMOVED: {folder}")

    if not dry_run and not any(legacy_root.iterdir()):
        legacy_root.rmdir()


def _report_completion(tools: list[str], declined: bool) -> None:
    typer.echo("Initialization complete.")
    typer.echo("Next steps:")
    for line in _next_steps(tools):
        typer.echo(f"- {line}")

    if declined:
        typer.echo(f"\nNote: {_ROOT_GUIDANCE_DECLINED_MESSAGE}")


@app.callback()
def init_command(
    path: Path = typer.Argument(Path(".")),
    tools: str | None = typer.Option(None, "--tools"),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    no_interactive: bool = typer.Option(False, "--no-interactive"),
    create_root_guidance: bool = typer.Option(False, "--create-root-guidance"),
    update_docs: bool = typer.Option(
        False,
        "--update-docs",
        help="On an upgrade, update the ai-team docs without asking.",
    ),
    update_skills: bool = typer.Option(
        False,
        "--update-skills",
        help="On an upgrade, update the agents and skills without asking.",
    ),
    project_dir: str | None = typer.Option(
        None,
        "--project-dir",
        help="Artifact folder, at any depth (default: the configured one, else 'ai-team').",
    ),
    integration_branch: str | None = typer.Option(
        None,
        "--integration-branch",
        help="Branch work integrates into (default: the configured one, else 'dev-agent').",
    ),
) -> None:
    """Initialize scaffold files in *path*.

    On a repository that already has ``.ai-team.toml``, the configured
    ``[project] dir``, ``[tracker] dir``, and ``[git] integration_branch`` are
    kept, so ``--force`` refreshes generated agents and skills without
    rewriting user configuration.
    """
    target_root = path.resolve()
    existing_marker = read_marker(target_root)
    is_upgrade = (target_root / ".ai-team.toml").is_file()
    try:
        if is_upgrade:
            selected_tools = _resolve_upgrade_tools(
                tools, existing_marker, no_interactive
            )
        else:
            selected_tools = _resolve_tools(tools, no_interactive)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    project_dir = (
        project_dir or marker_project_dir(existing_marker) or DEFAULT_PROJECT_DIR
    )
    integration_branch = (
        integration_branch
        or marker_integration_branch(existing_marker)
        or DEFAULT_INTEGRATION_BRANCH
    )
    if not is_valid_project_dir(project_dir):
        typer.echo(
            f"Invalid project dir '{project_dir}': use a relative folder path "
            "inside the repository without '..'.",
            err=True,
        )
        raise typer.Exit(code=1)
    if not is_valid_branch_name(integration_branch):
        typer.echo(f"Invalid integration branch '{integration_branch}'.", err=True)
        raise typer.Exit(code=1)
    settings = {"project_dir": project_dir, "integration_branch": integration_branch}
    tracker_dir = existing_marker.get("tracker", {}).get("dir") or DEFAULT_TRACKER_DIR

    scaffolds = resources.files("ai_team.init") / "scaffolds"
    sources = resources.files("ai_team.init") / "sources"
    with (
        resources.as_file(scaffolds) as scaffolds_path,
        resources.as_file(sources) as sources_path,
    ):
        if is_upgrade:
            _run_upgrade(
                _UpgradeRequest(
                    target_root=target_root,
                    scaffolds_path=scaffolds_path,
                    project_dir=project_dir,
                    tools=selected_tools,
                    settings=settings,
                    existing_marker=existing_marker,
                    update_docs=update_docs or force,
                    update_skills=update_skills or force,
                    no_interactive=no_interactive,
                    dry_run=dry_run,
                )
            )
            _ensure_tracker(target_root, tracker_dir, dry_run=dry_run)
            declined = _handle_root_guidance(
                target_root,
                sources_path,
                no_interactive,
                create_root_guidance,
                force,
                dry_run=dry_run,
                settings=settings,
            )
            if not dry_run:
                _report_completion(selected_tools, declined)
            return

        planned: list[tuple[Path, Path]] = []
        planned.extend(
            _plan_project_copies(scaffolds_path / "project", target_root / project_dir)
        )

        for tool in selected_tools:
            for scaffold_subfolder, destination in TOOL_EXPORT_PATHS[tool]:
                planned.extend(
                    _plan_copies(
                        scaffolds_path / tool / scaffold_subfolder,
                        target_root / destination,
                    )
                )

        marker = target_root / ".ai-team.toml"
        collisions = [destination for _, destination in planned if destination.exists()]

        if dry_run:
            has_root_guidance = any(
                (target_root / filename).exists() for filename in _ROOT_GUIDANCE_FILES
            )
            is_adoption = bool(collisions) or has_root_guidance
            typer.echo(f"CASE: {'adoption' if is_adoption else 'new project'}")

        overwrite = _decide_adoption_overwrite(
            collisions, force, no_interactive, dry_run
        )
        is_overwrite_approved = force or (bool(collisions) and bool(overwrite))
        if overwrite:
            to_write = planned
        else:
            to_write = [(s, d) for s, d in planned if d not in collisions]
            if not dry_run or no_interactive:
                _report_skipped(collisions)

        if dry_run:
            for _, destination in to_write:
                typer.echo(
                    f"{_would_write_verb(destination, force or bool(overwrite))}: {destination}"
                )
            for destination in collisions if overwrite is None else []:
                typer.echo(f"WOULD PROMPT: {destination}")
            typer.echo(f"WOULD WRITE: {marker}")
            if force and "codex" in selected_tools:
                _remove_legacy_codex_skills(target_root, dry_run=True)
            _handle_root_guidance(
                target_root,
                sources_path,
                no_interactive,
                create_root_guidance,
                force,
                dry_run=True,
                settings=settings,
            )
            _ensure_tracker(target_root, tracker_dir, dry_run=True)
            return

        _write_all(to_write, settings)
        if is_overwrite_approved and "codex" in selected_tools:
            _remove_legacy_codex_skills(target_root, dry_run=False)

        # Keep every setting the user already configured; only the values this
        # command owns (project, tracker, git, init) are refreshed.
        marker_data = dict(existing_marker)
        marker_data["project"] = {
            **existing_marker.get("project", {}),
            "dir": project_dir,
        }
        marker_data["tracker"] = {
            **existing_marker.get("tracker", {}),
            "dir": tracker_dir,
        }
        marker_data["git"] = {
            **existing_marker.get("git", {}),
            "integration_branch": integration_branch,
        }
        marker_data["init"] = {
            **existing_marker.get("init", {}),
            "tools": selected_tools,
            "framework_version": importlib.metadata.version("ai-team"),
        }
        marker_existed = marker.exists()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(tomli_w.dumps(marker_data), encoding="utf-8")
        _report_write(marker, marker_existed)
        _ensure_tracker(target_root, tracker_dir, dry_run=False)

        # Handle root guidance files (outside the collision-checked scaffold set)
        declined = _handle_root_guidance(
            target_root,
            sources_path,
            no_interactive,
            create_root_guidance,
            force,
            dry_run=False,
            settings=settings,
        )

    _report_completion(selected_tools, declined)
