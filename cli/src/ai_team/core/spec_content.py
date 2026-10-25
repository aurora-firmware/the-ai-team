"""Structural checks for feature specifications, separate from semantic review."""

from __future__ import annotations

import re
from collections import Counter

FEATURE_SECTIONS = (
    "Purpose",
    "Users and Journeys",
    "Exclusions",
    "Architecture",
    "Interfaces",
    "Workflow",
    "Behavioral Requirements",
    "Quality Requirements",
    "Configuration Requirements",
    "Assumptions and Dependencies",
    "Success Criteria",
    "Implementation Order",
    "Open Questions",
    "Amendment Log",
)
SPEC_STATUSES = ("draft", "review", "approved", "superseded")
Issue = tuple[str, str]
REQ_HEADING = re.compile(r"REQ-(\d{3}) — \S.*")
AC_HEADING = re.compile(r"AC-(\d{3})\.([1-9]\d*) — \S.*")
VERIFICATION = re.compile(
    r"^ {0,3}(?:(?:[-+*]|\d+[.)])[ \t]+)?\*\*Verification:\*\*[ \t]*(\S[^\n]*)$", re.M
)
LIST_ITEM = re.compile(r"^ {0,3}(?:[-+*]|\d+[.)])[ \t]")
COMMENT_OR_CODE = re.compile(r"(`+).*?\1|<!--")
TEMPLATE_TITLE = re.compile(
    r"^ {0,3}#{3,4} (?:REQ|AC)-[\d.]+ — (?:Requirement|Scenario) title[ \t]*$", re.M
)


def _strip_comments(line: str) -> tuple[str, bool]:
    """Remove HTML comments outside inline code; report an unclosed opener."""
    kept = []
    position = 0
    while match := COMMENT_OR_CODE.search(line, position):
        if match[0] != "<!--":
            kept.append(line[position : match.end()])
            position = match.end()
            continue
        kept.append(line[position : match.start()])
        end = line.find("-->", match.end())
        if end < 0:
            return "".join(kept), True
        position = end + 3
    kept.append(line[position:])
    return "".join(kept), False


def _prose(text: str) -> str:
    """Exclude frontmatter, comments, and code from structural interpretation."""
    text = re.sub(r"\A---[^\n]*\n.*?\n---[^\n]*(?:\n|$)", "", text, count=1, flags=re.S)
    lines = []
    fence = ""
    indented_code = in_list = in_comment = False
    previous_blank = True
    for line in text.splitlines():
        if in_comment:
            end = line.find("-->")
            if end < 0:
                continue
            in_comment = False
            line = line[end + 3 :]
            if not line.strip():
                continue
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (
                marker
                and marker[1][0] == fence[0]
                and len(marker[1]) >= len(fence)
                and not marker[2].strip()
            ):
                fence = ""
            continue
        if not marker:
            line, in_comment = _strip_comments(line)
        blank = not line.strip()
        if marker:
            fence = marker[1]
        elif line.startswith(("    ", "\t")) and (
            indented_code or (previous_blank and not in_list)
        ):
            # Indented code, unless the indentation continues a list item.
            indented_code = True
        else:
            if not blank:
                indented_code = False
                if not line.startswith((" ", "\t")):
                    in_list = bool(LIST_ITEM.match(line)) or (
                        in_list and not previous_blank
                    )
            lines.append(line)
        previous_blank = blank
    return "\n".join(lines)


def _blocks(text: str, level: int) -> list[tuple[str, str]]:
    """Split headings of one level; deeper headings remain inside the body."""
    headings = list(re.finditer(rf"^ {{0,3}}#{{{level}}} ([^\n]+)$", text, re.M))
    return [
        (
            re.sub(r"[ \t]+#+[ \t]*$", "", heading[1]).strip(),
            text[
                heading.end() : headings[i + 1].start()
                if i + 1 < len(headings)
                else len(text)
            ].strip(),
        )
        for i, heading in enumerate(headings)
    ]


def _section_issues(sections: list[tuple[str, str]]) -> list[Issue]:
    issues = []
    counts = Counter(title for title, _ in sections)
    for title in FEATURE_SECTIONS:
        if not counts[title]:
            issues.append(
                ("spec-section-missing", f"Missing required section '## {title}'.")
            )
        elif counts[title] > 1:
            issues.append(
                ("spec-section-duplicate", f"Section '## {title}' is repeated.")
            )
    for title, body in sections:
        content = re.sub(r"(?m)^ {0,3}#{1,6}[ \t]+.*$", "", body).strip()
        if title in FEATURE_SECTIONS and title != "Amendment Log" and not content:
            issues.append(
                (
                    "spec-section-empty",
                    f"Fill section '## {title}' or explain why it is not applicable.",
                )
            )
    return issues


def _acceptance_issues(number: str, body: str) -> list[Issue]:
    issues = []
    cases = _blocks(body, 4)
    if not cases:
        return [
            (
                "spec-acceptance-missing",
                f"REQ-{number} needs at least one '#### AC-{number}.1 — Title' scenario.",
            )
        ]
    for title, scenario in cases:
        match = AC_HEADING.fullmatch(title)
        if not match:
            issues.append(
                (
                    "spec-acceptance-heading",
                    f"Invalid acceptance heading '{title}'; use AC-NNN.M — Title.",
                )
            )
            continue
        identifier = f"AC-{match[1]}.{match[2]}"
        if match[1] != number:
            issues.append(
                (
                    "spec-acceptance-owner",
                    f"{identifier} must be nested under REQ-{match[1]}, not REQ-{number}.",
                )
            )
        verification = VERIFICATION.search(scenario)
        if not verification:
            issues.append(
                (
                    "spec-verification-missing",
                    f"{identifier} needs a nonempty '**Verification:**' method.",
                )
            )
        content = VERIFICATION.sub("", scenario).strip()
        if not content:
            issues.append(
                (
                    "spec-acceptance-empty",
                    f"{identifier} needs concrete acceptance conditions and outcomes.",
                )
            )
    return issues


def _acceptance_inventory(
    sections: list[tuple[str, str]],
) -> tuple[list[Issue], list[str]]:
    """Inventory every AC, including accidentally misnested ones."""
    issues = []
    identifiers = []
    for section, text in sections:
        prefix = text
        if section in ("Behavioral Requirements", "Quality Requirements"):
            prefix = re.split(r"(?m)^ {0,3}### ", text, maxsplit=1)[0]
        for title, _ in _blocks(prefix, 4):
            if title.startswith("AC-"):
                issues.append(
                    (
                        "spec-acceptance-orphan",
                        f"Acceptance '{title}' must appear beneath its REQ-NNN in Behavioral Requirements or Quality Requirements.",
                    )
                )
        for title, _ in _blocks(text, 4):
            match = AC_HEADING.fullmatch(title)
            if match:
                identifiers.append(f"AC-{match[1]}.{match[2]}")
    return issues, identifiers


def _requirement_issues(sections: list[tuple[str, str]]) -> list[Issue]:
    issues, acceptance = _acceptance_inventory(sections)
    requirements = []
    for section, text in sections:
        if section not in ("Behavioral Requirements", "Quality Requirements"):
            continue
        blocks = _blocks(text, 3)
        if section == "Behavioral Requirements" and not blocks:
            issues.append(
                (
                    "spec-requirements-missing",
                    "Behavioral Requirements needs at least one REQ-NNN heading.",
                )
            )
        if (
            section == "Quality Requirements"
            and not blocks
            and text
            and not re.match(r"None\b\W*\w", text, re.I)
        ):
            issues.append(
                (
                    "spec-quality-disposition",
                    "Quality Requirements needs REQ/AC obligations or 'None' with a non-applicability reason.",
                )
            )
        for title, body in blocks:
            match = REQ_HEADING.fullmatch(title)
            if not match or int(match[1]) == 0:
                issues.append(
                    (
                        "spec-requirement-heading",
                        f"Invalid requirement heading '{title}'; use REQ-NNN — Title with NNN >= 001.",
                    )
                )
                continue
            number = match[1]
            requirements.append(f"REQ-{number}")
            statement = re.split(r"(?m)^ {0,3}#### ", body, maxsplit=1)[0]
            if not re.search(r"\b(?:SHALL|MUST)\b", statement):
                issues.append(
                    (
                        "spec-requirement-statement",
                        f"REQ-{number} needs an explicit SHALL or MUST obligation before its acceptance scenarios.",
                    )
                )
            issues.extend(_acceptance_issues(number, body))
    for identifiers, kind in (
        (requirements, "requirement"),
        (acceptance, "acceptance"),
    ):
        for identifier, count in Counter(identifiers).items():
            if count > 1:
                issues.append(
                    (
                        f"spec-{kind}-duplicate",
                        f"Duplicate identifier '{identifier}'; identifiers must be unique within the spec.",
                    )
                )
    return issues


def validate_feature_content(text: str, *, status: str) -> list[Issue]:
    """Return structural findings without rewriting the artifact."""
    if status not in ("review", "approved"):
        return []
    prose = _prose(text)
    sections = _blocks(prose, 2)
    preamble = re.split(r"(?m)^ {0,3}## ", prose, maxsplit=1)[0]
    issues = _section_issues(sections) + _requirement_issues(
        [("", preamble), *sections]
    )
    placeholder_text = re.sub(r"(`+).*?\1", "", prose)
    if re.search(
        r"\[(?:TODO|TBD|TBR)(?:[ \t]*:[^\]\n]*)?\]|\[NEEDS CLARIFICATION\b"
        r"|^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+(?:\[[ xX]\][ \t]+)?)?"
        r"(?:TODO|TBD|TBR)(?:[ \t]*:|[ \t]*$)",
        placeholder_text,
        re.I | re.M,
    ) or TEMPLATE_TITLE.search(prose):
        issues.append(
            (
                "spec-placeholder",
                "Resolve TODO/TBD/TBR, clarification, and template-title placeholders before review or approval.",
            )
        )
    return issues
