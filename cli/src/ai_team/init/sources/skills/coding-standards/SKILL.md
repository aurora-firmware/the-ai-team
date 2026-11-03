---
name: coding-standards
description: Defines the framework coding standards that implementation code and tests must meet, and where a project's own coding guidelines override them. Use when a Developer writes or changes code or tests, or when a Reviewer checks code against the project's rules.
allowed-tools: Read
user-invocable: false
---

# Coding Standards

These standards are language-agnostic.
The project's own coding guidelines extend and override them: read the document the project guidance (`AGENTS.md` or the project's other rules) names, by default `docs/development/coding_guidelines.md`.
Where the two disagree, the project's guidelines win.
When the project has no such document, these standards apply alone.

## General

- **Clarity over cleverness.** No tricks, obscure idioms or compact expressions for their own sake.
- **Minimal scope.** Implement exactly what the task or fix specifies: no added features, unrelated refactors or unrequested "improvements".
- **Self-documenting code.** Descriptive names; comments explain *why*, not *what*.
- **Fail explicitly.** Surface a clear error rather than continue with bad state.

## Naming

- Follow the naming convention of the project's language (for example `camelCase` in JavaScript, `snake_case` in Python).
- Names describe purpose, not implementation: `get_active_users()`, not `query_db_filter_active()`.
- Booleans start with `is`, `has`, `can` or `should`. Constants use `UPPER_SNAKE_CASE`.

## Functions

- One function does one thing; split one that does several.
- Aim for under 30 lines, at most 3–4 parameters (use a configuration object or data class beyond that), and early returns over nesting.

## Error Handling

- Handle an error at the boundary where it can be meaningfully addressed.
- Never catch and silently ignore an exception.
- Error messages say what failed, which input caused it, and what the caller can do.

## Testing

- Work that adds or changes product behavior has tests, written test-first. The task's Verification section names its method (test, inspection or demonstration).
- Never write a test that asserts the wording of skills, process documents, guides or specs, or one that only proves something was removed; those changes are verified by inspection.
- Test behavior, not implementation details.
- Tests are independent (no shared mutable state) and named for the behavior: `test_returns_empty_list_when_no_users_match_filter`.

## Security

- Never hardcode credentials, API keys or secrets.
- Validate all external input: user input, API responses, file contents.
- Use parameterized database queries, never string concatenation.
- Grant least privilege for file access, network calls and permissions.

## Dependencies

- Minimize external dependencies; prefer the standard library when it meets the need.
- Pin dependency versions in lock files.
- Justify a new dependency in the Work Log or a decision record.

## File Organization

- One module per file, unless the language convention differs.
- Keep files under 300 lines; split a larger one when it has separable parts.
- Group related files in directories with a clear purpose.
