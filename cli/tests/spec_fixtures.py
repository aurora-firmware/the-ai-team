"""Complete feature-spec content shared by CLI validation tests."""

SPEC_SECTIONS = (
    "Purpose",
    "Users and Journeys",
    "Exclusions",
    "Alternatives Considered",
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

EXPORT_REQUIREMENT = """### REQ-001 — Deny unauthorized exports

The system SHALL reject exports requested by an actor without workspace access.

#### AC-001.1 — Access denied

- **Given:** an actor without access to workspace A
- **When:** the actor requests an export from workspace A
- **Then:** the request is rejected without returning workspace records

**Verification:** an authorization acceptance test for AC-001.1.
"""


def feature_spec_body() -> str:
    values = dict.fromkeys(SPEC_SECTIONS, "None — not applicable to this feature.")
    values["Purpose"] = "Prevent disclosure of workspace records."
    values["Users and Journeys"] = "Workspace users request exports (REQ-001)."
    values["Behavioral Requirements"] = EXPORT_REQUIREMENT
    values["Amendment Log"] = ""
    return "\n\n".join(f"## {name}\n\n{value}" for name, value in values.items())
