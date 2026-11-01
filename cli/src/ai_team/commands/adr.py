"""`ai-team adr` command group for ADR artifact operations."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import typer
from slugify import slugify

from ai_team.commands._shared import artifact_object_from_file, hint_missing_overview
from ai_team.core.fs import ArtifactExists, write_artifact
from ai_team.core.ids import next_adr_id
from ai_team.core.locator import find_project_root
from ai_team.core.models import Adr
from ai_team.core.templates import load_template
from ai_team.render import print_json

NAME = "adr"
app = typer.Typer(help="Create and manage ADR artifacts.")

AdrStatus = Literal["proposed", "accepted", "superseded"]


def _template_body(template: str) -> str:
    """Return markdown body text after the YAML frontmatter block."""
    if not template.startswith("---"):
        raise ValueError("ADR template is missing opening frontmatter fence.")

    rest = template[3:]
    close_idx = rest.find("\n---")
    if close_idx == -1:
        raise ValueError("ADR template is missing closing frontmatter fence.")

    body = rest[close_idx + 5 :]
    if body.startswith("\n"):
        body = body[1:]
    return body


@app.command("new")
def new_adr(
    title: str,
    status: AdrStatus = typer.Option("proposed", "--status"),
    supersedes: str | None = typer.Option(None, "--supersedes"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Create a new ADR artifact from the bundled template."""
    root = find_project_root(Path.cwd())
    hint_missing_overview(root)
    adr_id = next_adr_id(root)
    slug = slugify(title)
    dest = root.decisions / f"{adr_id}-{slug}.md"

    template = load_template("adr")
    body = _template_body(template)
    body = body.replace("# ADR-000: [Decision Title]", f"# {adr_id}: {title}", 1)
    model = Adr(
        id=adr_id,
        title=title,
        status=status,
        created=date.today().isoformat(),
        supersedes=supersedes,
    )

    try:
        write_artifact(dest, model, body, overwrite=False)
    except ArtifactExists as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    absolute_path = str(dest.resolve())
    if as_json:
        print_json(artifact_object_from_file(dest, "adr"))
        return

    typer.echo(absolute_path)
