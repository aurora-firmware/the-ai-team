"""`ai-team status` command for Gate 5 inline summaries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import typer
from rich.markdown import Markdown

from ai_team.commands._shared import hint_missing_overview, project_root
from ai_team.core.fs import ArtifactKind, read_artifact
from ai_team.core.ids import is_overview_reference
from ai_team.core.locator import ProjectRoot
from ai_team.core.models import parse_bug, parse_spec, parse_task
from ai_team.core.tracker import iter_items
from ai_team.render import console, print_json

NAME = "status"
app = typer.Typer(help="Show a Gate 5 status summary.", invoke_without_command=True)


@dataclass(frozen=True)
class InProgressTask:
    id: str
    title: str
    assigned_role: str


@dataclass(frozen=True)
class BlockedItem:
    id: str
    title: str
    blocking_reason: str


@dataclass(frozen=True)
class CriticalBug:
    id: str
    title: str
    severity: str


def _should_skip(path: Path) -> bool:
    return path.name == ".gitkeep" or path.match("TEMPLATE-*.md")


def _iter_markdown_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        path
        for path in folder.glob("*.md")
        if path.is_file() and not _should_skip(path)
    )


def _count(folder: Path) -> int:
    return len(_iter_markdown_files(folder))


def _count_active_specs(folder: Path) -> int:
    """Count specs that are not superseded, leaving out the S-000 overview."""
    count = 0
    for path in _iter_markdown_files(folder):
        if is_overview_reference(path.name):
            continue
        spec = parse_spec(path)
        if spec.status != "superseded" and not is_overview_reference(spec.id or ""):
            count += 1
    return count


def _latest_work_log_session(path: Path, kind: ArtifactKind) -> tuple[str, str] | None:
    """Return the last Work Log session heading and its first non-empty line."""
    _, body = read_artifact(path, kind)

    lines = body.splitlines()
    start = None
    end = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == "## Work Log":
            start = idx + 1
            continue
        if start is not None and line.startswith("## "):
            end = idx
            break

    if start is None:
        return None

    work_log = lines[start:end]
    heading_indexes = [
        idx for idx, line in enumerate(work_log) if line.startswith("### Session")
    ]
    if not heading_indexes:
        return None

    last_heading = heading_indexes[-1]
    for line in work_log[last_heading + 1 :]:
        stripped = line.strip()
        if stripped:
            return work_log[last_heading].strip(), stripped
    return None


def _latest_work_log_line(path: Path, kind: ArtifactKind) -> str:
    session = _latest_work_log_session(path, kind)
    return session[1] if session else "not recorded"


def _blocking_reason(path: Path, item: object, kind: ArtifactKind) -> str:
    """Return a blocked task's or bug's frontmatter reason, else its latest Work Log line."""
    source_map = getattr(item, "_source_map", None) or {}
    for key in ("blocking-reason", "blocking_reason"):
        value = source_map.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return _latest_work_log_line(path, kind)


_SESSION_HEADING = re.compile(r"^### Session (\d+) — (\d{4}-\d{2}-\d{2})\s*$")
_ID_NUMBER = re.compile(r"(\d+)$")


def _latest_integration_result(
    tasks_by_status: dict[str, list[tuple[Path, object]]],
    bugs_by_status: dict[str, list[tuple[Path, object]]],
) -> str:
    """Cite the newest Work Log session of a completed task or resolved bug."""
    candidates: list[tuple[str, int, str, str, str]] = []
    finished = [
        (path, item, "task") for path, item in tasks_by_status.get("completed", [])
    ] + [(path, item, "bug") for path, item in bugs_by_status.get("resolved", [])]
    for path, item, kind in finished:
        session = _latest_work_log_session(path, kind)
        if session is None:
            continue
        heading_match = _SESSION_HEADING.match(session[0])
        id_match = _ID_NUMBER.search(item.id)
        if heading_match is None or id_match is None:
            continue
        number, date = heading_match.groups()
        candidates.append(
            (date, int(id_match.group(1)), item.id, f"Session {number}", session[1])
        )

    if not candidates:
        return "not found"
    date, _, item_id, session_label, line = max(candidates, key=lambda c: c[:3])
    return f"{item_id} {session_label} ({date}): {line}"


def _by_status(paths: list[Path], parser) -> dict[str, list[tuple[Path, object]]]:
    """Group parsed work items by their frontmatter ``status``."""
    grouped: dict[str, list[tuple[Path, object]]] = {}
    for path in paths:
        model = parser(path)
        grouped.setdefault(model.status, []).append((path, model))
    return grouped


def _payload(root: ProjectRoot) -> dict[str, object]:
    tasks_by_status = _by_status(iter_items(root.tasks), parse_task)
    bugs_by_status = _by_status(iter_items(root.bugs), parse_bug)

    def count_tasks(status: str) -> int:
        return len(tasks_by_status.get(status, []))

    def count_bugs(status: str) -> int:
        return len(bugs_by_status.get(status, []))

    in_progress_tasks: list[InProgressTask] = [
        InProgressTask(id=task.id, title=task.title, assigned_role=task.assigned_role)
        for _, task in tasks_by_status.get("in-progress", [])
    ]

    blocked_tasks: list[BlockedItem] = [
        BlockedItem(
            id=task.id,
            title=task.title,
            blocking_reason=_blocking_reason(path, task, "task"),
        )
        for path, task in tasks_by_status.get("blocked", [])
    ]

    blocked_bugs: list[BlockedItem] = [
        BlockedItem(
            id=bug.id,
            title=bug.title,
            blocking_reason=_blocking_reason(path, bug, "bug"),
        )
        for path, bug in bugs_by_status.get("blocked", [])
    ]

    critical_high_bugs: list[CriticalBug] = [
        CriticalBug(id=bug.id, title=bug.title, severity=bug.severity)
        for _, bug in bugs_by_status.get("open", [])
        if bug.severity in {"critical", "high"}
    ]

    payload: dict[str, object] = {
        "counts": {
            "specs_active": _count_active_specs(root.specs),
            "tasks": {
                "planned": count_tasks("planned"),
                "pending": count_tasks("pending"),
                "in_progress": count_tasks("in-progress"),
                "completed": count_tasks("completed"),
                "blocked": count_tasks("blocked"),
                "cancelled": count_tasks("cancelled"),
            },
            "bugs": {
                "open": count_bugs("open"),
                "in_progress": count_bugs("in-progress"),
                "blocked": count_bugs("blocked"),
                "resolved": count_bugs("resolved"),
            },
            "adrs": _count(root.decisions),
        },
        "in_progress_tasks": [
            {
                "id": task.id,
                "title": task.title,
                "assigned_role": task.assigned_role,
            }
            for task in in_progress_tasks
        ],
        "blocked_tasks": [
            {
                "id": task.id,
                "title": task.title,
                "blocking_reason": task.blocking_reason,
            }
            for task in blocked_tasks
        ],
        "blocked_bugs": [
            {
                "id": bug.id,
                "title": bug.title,
                "blocking_reason": bug.blocking_reason,
            }
            for bug in blocked_bugs
        ],
        "critical_high_open_bugs": [
            {"id": bug.id, "title": bug.title, "severity": bug.severity}
            for bug in critical_high_bugs
        ],
        "latest_integration_result": _latest_integration_result(
            tasks_by_status, bugs_by_status
        ),
    }
    return payload


def _list_lines(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _to_markdown(payload: dict[str, object]) -> str:
    counts = payload["counts"]
    assert isinstance(counts, dict)
    tasks = counts["tasks"]
    assert isinstance(tasks, dict)
    bugs = counts["bugs"]
    assert isinstance(bugs, dict)

    in_progress = payload["in_progress_tasks"]
    assert isinstance(in_progress, list)
    blocked_tasks = payload["blocked_tasks"]
    assert isinstance(blocked_tasks, list)
    blocked_bugs = payload["blocked_bugs"]
    assert isinstance(blocked_bugs, list)
    critical_high = payload["critical_high_open_bugs"]
    assert isinstance(critical_high, list)

    in_progress_lines = _list_lines(
        [
            f"{row['id']} — {row['title']} ({row['assigned_role']})"
            for row in in_progress
            if isinstance(row, dict)
        ]
    )
    blocked_lines = _list_lines(
        [
            f"{row['id']} — {row['title']}: {row['blocking_reason']}"
            for row in [*blocked_tasks, *blocked_bugs]
            if isinstance(row, dict)
        ]
    )
    critical_high_lines = _list_lines(
        [
            f"{row['id']} — {row['title']} ({row['severity']})"
            for row in critical_high
            if isinstance(row, dict)
        ]
    )

    return (
        "## Status Report\n\n"
        "### Summary\n"
        f"- Active specs: {counts['specs_active']}\n"
        f"- Planned tasks: {tasks['planned']}\n"
        f"- Pending tasks: {tasks['pending']}\n"
        f"- In progress: {tasks['in_progress']}\n"
        f"- Completed: {tasks['completed']}\n"
        f"- Blocked: {tasks['blocked']}\n"
        f"- Cancelled tasks: {tasks['cancelled']}\n"
        f"- Open bugs: {bugs['open']}\n"
        f"- Bugs in progress: {bugs['in_progress']}\n"
        f"- Blocked bugs: {bugs['blocked']}\n"
        f"- Resolved bugs: {bugs['resolved']}\n"
        f"- ADRs: {counts['adrs']}\n"
        f"- Latest integration result: {payload['latest_integration_result']}\n\n"
        "### In Progress\n"
        f"{in_progress_lines}\n\n"
        "### Blocked\n"
        f"{blocked_lines}\n\n"
        "### Critical/High Bugs\n"
        f"{critical_high_lines}\n"
    )


@app.callback()
def default(
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    root = project_root()
    hint_missing_overview(root)
    payload = _payload(root)
    if as_json:
        print_json(payload)
        return
    console.print(Markdown(_to_markdown(payload)))
