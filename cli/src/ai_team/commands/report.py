"""`ai-team report` command for writing Gate 5 progress-report markdown files."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import typer

from ai_team.commands._shared import hint_missing_overview, project_root
from ai_team.commands.status import _payload
from ai_team.core.models import parse_adr, parse_bug, parse_spec, parse_task
from ai_team.core.templates import load_template
from ai_team.core.tracker import iter_items

NAME = "report"
app = typer.Typer(help="Write a Gate 5 progress report.", invoke_without_command=True)


def _iter_markdown_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        path
        for path in folder.glob("*.md")
        if path.is_file()
        and path.name != ".gitkeep"
        and not path.match("TEMPLATE-*.md")
    )


def _summary_line(payload: dict[str, object]) -> str:
    counts = payload["counts"]
    assert isinstance(counts, dict)
    tasks = counts["tasks"]
    assert isinstance(tasks, dict)
    bugs = counts["bugs"]
    assert isinstance(bugs, dict)

    return (
        f"Active specs: {counts['specs_active']}. "
        f"Planned tasks: {tasks['planned']}. "
        f"Pending tasks: {tasks['pending']}. "
        f"In progress tasks: {tasks['in_progress']}. "
        f"Completed tasks: {tasks['completed']}. "
        f"Blocked tasks: {tasks['blocked']}. "
        f"Cancelled tasks: {tasks['cancelled']}. "
        f"Open bugs: {bugs['open']}. "
        f"Bugs in progress: {bugs['in_progress']}. "
        f"Blocked bugs: {bugs['blocked']}. "
        f"Resolved bugs: {bugs['resolved']}. "
        f"ADRs: {counts['adrs']}. "
        f"Latest integration result: {payload['latest_integration_result']}."
    )


def _as_rows(rows: list[str], fallback: str) -> str:
    if not rows:
        return fallback
    return "\n".join(rows)


def _spec_rows(root) -> str:
    rows: list[str] = []
    for path in _iter_markdown_files(root.specs):
        spec = parse_spec(path)
        note = (
            "Current Gate 5 target"
            if spec.status == "approved"
            else "Review in progress"
        )
        rows.append(f"| {path.name} | {spec.status} | {note} |")
    return _as_rows(rows, "| none | n/a | No active specs |")


def _completed_rows(root) -> str:
    rows: list[str] = []
    for path in iter_items(root.tasks):
        task = parse_task(path)
        if task.status != "completed":
            continue
        rows.append(f"| {task.id} | {task.title} | {task.assigned_role} |")
    return _as_rows(rows, "| none | n/a | n/a |")


def _in_progress_rows(payload: dict[str, object]) -> str:
    in_progress = payload["in_progress_tasks"]
    assert isinstance(in_progress, list)
    rows: list[str] = []
    for row in in_progress:
        if isinstance(row, dict):
            rows.append(
                f"| {row['id']} | {row['title']} | {row['assigned_role']} | "
                "actively progressing |"
            )
    return _as_rows(rows, "| none | n/a | n/a | no in-progress tasks |")


def _blocked_items(payload: dict[str, object]) -> list[object]:
    """Return the blocked task rows followed by the blocked bug rows."""
    blocked_tasks = payload["blocked_tasks"]
    assert isinstance(blocked_tasks, list)
    blocked_bugs = payload["blocked_bugs"]
    assert isinstance(blocked_bugs, list)
    return [*blocked_tasks, *blocked_bugs]


def _blocked_rows(payload: dict[str, object]) -> str:
    blocked = _blocked_items(payload)
    rows: list[str] = []
    for row in blocked:
        if isinstance(row, dict):
            reason = str(row["blocking_reason"])
            rows.append(
                f"| {row['id']} | {row['title']} | {reason} | "
                f"Resolve blocker: {reason} |"
            )
    return _as_rows(rows, "| none | n/a | n/a | no action needed |")


def _diagnosis_status(state: str) -> str:
    if state == "open":
        return "n/a"
    if state in ("in-progress", "blocked"):
        return "in progress"
    return "complete"


def _bug_rows(root) -> str:
    rows: list[str] = []
    bugs = [parse_bug(path) for path in iter_items(root.bugs)]
    for state in ("open", "in-progress", "blocked", "resolved"):
        for bug in bugs:
            if bug.status != state:
                continue
            rows.append(
                f"| {bug.id} | {bug.title} | {bug.severity} | {state} | "
                f"{_diagnosis_status(state)} |"
            )
    return _as_rows(rows, "| none | n/a | n/a | n/a | n/a |")


def _decision_rows(root) -> str:
    rows: list[str] = []
    for path in _iter_markdown_files(root.decisions):
        adr = parse_adr(path)
        rows.append(f"| {adr.id} | {adr.title} | {adr.status} |")
    return _as_rows(rows, "| none | n/a | n/a |")


def _next_actions(payload: dict[str, object]) -> str:
    blocked = _blocked_items(payload)
    critical_high = payload["critical_high_open_bugs"]
    assert isinstance(critical_high, list)
    in_progress = payload["in_progress_tasks"]
    assert isinstance(in_progress, list)

    actions: list[str] = []
    for row in blocked:
        if isinstance(row, dict):
            actions.append(f"Unblock {row['id']}: {row['blocking_reason']}")
    for row in critical_high:
        if isinstance(row, dict):
            actions.append(f"Triage {row['id']}: {row['title']}")
    for row in in_progress:
        if isinstance(row, dict):
            actions.append(f"Advance {row['id']}: {row['title']}")
    if not actions:
        actions.append("No immediate actions.")

    selected = actions[:3]
    return "\n".join(f"{idx}. {value}" for idx, value in enumerate(selected, start=1))


def _risks_and_concerns(payload: dict[str, object]) -> str:
    blocked_tasks = payload["blocked_tasks"]
    assert isinstance(blocked_tasks, list)
    blocked_bugs = payload["blocked_bugs"]
    assert isinstance(blocked_bugs, list)
    critical_high = payload["critical_high_open_bugs"]
    assert isinstance(critical_high, list)

    risks: list[str] = []
    if blocked_tasks:
        risks.append("Blocked tasks may delay delivery.")
    if blocked_bugs:
        risks.append("Blocked bugs stay unfixed until they are unblocked.")
    if critical_high:
        risks.append("Critical/high bugs may impact release quality.")
    if not risks:
        risks.append("No immediate risks identified.")
    return "\n".join(f"- {risk}" for risk in risks)


def _replace(text: str, old: str, new: str) -> str:
    return text.replace(old, new)


def _render_report(
    template: str, payload: dict[str, object], report_date: str, root
) -> str:
    report = template
    replacements: list[tuple[str, str]] = [
        (
            'title: "Progress Report — [Date or Sprint]"',
            f'title: "Progress Report — {report_date}"',
        ),
        ("created: YYYY-MM-DD", f"created: {report_date}"),
        ("# Progress Report — [Date or Sprint]", f"# Progress Report — {report_date}"),
        ("One-paragraph overview of current project state.", _summary_line(payload)),
        (
            "| specification-name.md | approved | Current Gate 5 target |",
            _spec_rows(root),
        ),
        (
            "- Latest integration-test result:",
            f"- Latest integration-test result: {payload['latest_integration_result']}",
        ),
        (
            "- Source:",
            "- Source: latest Work Log session of completed tasks and resolved bugs",
        ),
        ("- Date:", f"- Date: {report_date}"),
        (
            "| T-001 | Task title | Role |\n| T-002 | Task title | Role |",
            _completed_rows(root),
        ),
        ("| T-003 | Task title | Role | Current state |", _in_progress_rows(payload)),
        (
            "| T-004 | Task title | What is blocking | What must happen to unblock |",
            _blocked_rows(payload),
        ),
        ("| B-001 | Bug title | high | open | not started |", _bug_rows(root)),
        ("| 001 | Decision title | accepted |", _decision_rows(root)),
        (
            (
                "1. Next priority action\n"
                "2. Second priority action\n"
                "3. Third priority action"
            ),
            _next_actions(payload),
        ),
        ("- Risk or concern 1\n- Risk or concern 2", _risks_and_concerns(payload)),
    ]

    for old, new in replacements:
        report = _replace(report, old, new)
    return report


@app.callback()
def default(
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Override destination path.",
    ),
) -> None:
    """Write the bundled progress-report template to disk."""
    root = project_root()
    hint_missing_overview(root)
    report_date = date.today().isoformat()
    payload: dict[str, Any] = _payload(root)

    destination = out
    if destination is None:
        destination = root.docs / "reports" / f"progress-report-{report_date}.md"

    destination.parent.mkdir(parents=True, exist_ok=True)
    template = load_template("report")
    destination.write_text(
        _render_report(template, payload, report_date, root),
        encoding="utf-8",
    )
    typer.echo(str(destination.resolve()))
