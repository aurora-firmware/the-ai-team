"""`ai-team spec` command group for specification artifact operations."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import typer
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from slugify import slugify

from ai_team.commands._shared import artifact_object_from_file, hint_missing_overview
from ai_team.core.fs import ArtifactExists
from ai_team.core.ids import OVERVIEW_ID, next_spec_id, overview_exists
from ai_team.core.locator import find_project_root
from ai_team.core.lock import LockTimeout, create_artifact_with_lock
from ai_team.core.models import Spec
from ai_team.core.templates import load_template
from ai_team.render import print_json

NAME = "spec"
app = typer.Typer(help="Create and manage specification artifacts.")

SpecStatus = Literal["draft", "review", "approved", "superseded"]
DEFAULT_OVERVIEW_TITLE = "System Overview"


def _template_parts(template: str) -> tuple[CommentedMap, str]:
    """Return template frontmatter map and markdown body after the frontmatter block."""
    if not template.startswith("---"):
        raise ValueError("Spec template is missing opening frontmatter fence.")

    rest = template[3:]
    close_idx = rest.find("\n---")
    if close_idx == -1:
        raise ValueError("Spec template is missing closing frontmatter fence.")

    frontmatter = rest[:close_idx]
    body = rest[close_idx + 5 :]
    if body.startswith("\n"):
        body = body[1:]

    yaml = YAML(typ="rt")
    parsed = yaml.load(frontmatter)
    if parsed is None:
        return CommentedMap(), body
    return parsed, body


@app.command("new")
def new_spec(
    title: str | None = typer.Argument(
        None, help="Spec title. Optional with --overview."
    ),
    author: str = typer.Option("planner", "--author"),
    status: SpecStatus = typer.Option("draft", "--status"),
    overview: bool = typer.Option(
        False,
        "--overview",
        help="Create the S-000 system overview from the system-overview template.",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Create a new specification artifact from the bundled template."""
    if title is None:
        if not overview:
            typer.echo("Missing argument 'TITLE'.", err=True)
            raise typer.Exit(code=2)
        title = DEFAULT_OVERVIEW_TITLE
    spec_title = title
    root = find_project_root(Path.cwd())
    if not overview:
        hint_missing_overview(root)

    def allocate_id() -> str:
        if not overview:
            return next_spec_id(root)
        if overview_exists(root):
            raise ArtifactExists(
                f"{OVERVIEW_ID} already exists in specs/ or specs/archive/; "
                "refusing to create a second system overview."
            )
        return OVERVIEW_ID

    def build(spec_id: str) -> tuple[Path, Spec, str]:
        slug = slugify(spec_title)
        dest = root.specs / f"{spec_id}-{slug}.md"

        template = load_template("system-overview" if overview else "spec")
        source_map, body = _template_parts(template)

        model = Spec(
            title=spec_title,
            version="0.1",
            status=status,
            created=date.today().isoformat(),
            author=author,
            id=spec_id,
            _source_map=source_map,
        )

        body = body.replace("# [Specification Title]", f"# {spec_title}", 1)
        return dest, model, body

    try:
        spec_id, dest = create_artifact_with_lock(
            root.project_dir,
            allocate_id=allocate_id,
            build=build,
        )
    except ArtifactExists as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    except LockTimeout as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    absolute_path = str(dest.resolve())
    if as_json:
        print_json(artifact_object_from_file(dest, "spec"))
        return

    typer.echo(absolute_path)
