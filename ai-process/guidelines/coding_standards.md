# Coding Standards

These standards apply to any implementation code produced by AI roles using this framework.
They are intentionally language-agnostic.
When bootstrapping a new project, extend them with language-specific conventions, examples, and tooling rules relevant to your stack.
Project-specific overrides should be documented in the project's own guidelines.

**For project-specific rules** (language, tooling, naming and dependency specifics), see `ai-team/docs/coding_guidelines.md` (when working within a project). Each project should maintain its own extensions to these framework standards.

## General Principles

1. **Clarity over cleverness.** Code should be immediately understandable. Avoid tricks, obscure idioms, or unnecessarily compact expressions.
2. **Minimal scope.** Implement exactly what the task specifies. Do not add features, refactor unrelated code, or "improve" things that were not asked for.
3. **Self-documenting code.** Use descriptive names for variables, functions, and types. Comments explain *why*, not *what*.
4. **Fail explicitly.** When something goes wrong, surface a clear error rather than silently continuing with bad state.

## Naming

- Use the naming convention of the project's language (e.g., `camelCase` for JavaScript, `snake_case` for Python).
- Names should describe purpose, not implementation: `get_active_users()` not `query_db_filter_active()`.
- Boolean variables start with `is`, `has`, `can`, `should`: `is_valid`, `has_permission`.
- Constants use `UPPER_SNAKE_CASE`.

## Functions

- Do one thing. If a function does multiple things, split it.
- Keep functions short — aim for under 30 lines. If longer, check if it can be decomposed.
- Limit parameters to 3-4. If more are needed, use a configuration object or data class.
- Return early to reduce nesting.

## Error Handling

- Handle errors at the boundary where they can be meaningfully addressed.
- Do not catch and silently ignore exceptions.
- Include context in error messages: what failed, what input caused it, and what the caller can do about it.

## Testing

- Every task that adds or changes product behavior produces tests. The verification methods (test, inspection, demonstration) and when each applies are defined in `guides/spec_authoring_guide.md`.
- Never write a test that asserts the wording of skills, process documents, guides, or specs, or one that only proves something was removed; those changes are verified by inspection.
- Follow the test-driven implementation procedure: write the test first, verify it fails, implement, verify it passes.
- Test behavior, not implementation details.
- Each test should be independent — no shared mutable state between tests.
- Name tests descriptively: `test_returns_empty_list_when_no_users_match_filter`.

## Security

- Never hardcode credentials, API keys, or secrets.
- Validate all external input (user input, API responses, file contents).
- Use parameterized queries for database access — never string concatenation.
- Follow the principle of least privilege for file access, network calls, and permissions.

## Dependencies

- Minimize external dependencies. Prefer standard library when it meets the need.
- Pin dependency versions in lock files.
- New dependencies require justification in the task notes or a decision record.

## File Organization

- One module per file (unless the language convention differs).
- Keep files under 300 lines. If larger, consider splitting.
- Group related files in directories with clear purpose.
