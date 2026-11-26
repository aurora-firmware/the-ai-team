# Coding Standards

These standards apply to any implementation code and tests produced by AI roles using this framework.
They are language-agnostic and are a starting point: the project bootstrap starts the project's own coding guidelines from them, and the project edits that document freely to fit its stack, tooling and conventions.
`ai-team init` does not scaffold it.

The project's coding guidelines are the document the project guidance names (`AGENTS.md` or the project's other rules), by default `docs/development/coding_guidelines.md`, next to `architecture.md` and `tech_stack.md`.
Developers follow both the standards and the project's guidelines, and Reviewers check against both. Where they disagree, the project's guidelines win. When the project has no such document, these standards apply alone.

## Principles

1. **One program, one responsibility.** A function, a file and a module each do one clear thing and do it well. Build larger behavior by composing small parts, not by growing big ones.
2. **Simpler is better.** Choose the simplest solution that meets the requirement. Add no abstraction, option, layer or configuration until something needs it.
3. **Removing beats adding.** When a change or fix can be made by deleting or reducing code, do that instead of patching on top. Delete the dead code, unused options and duplicated logic your change makes obsolete.
4. **Minimal scope.** Implement exactly what the task or fix specifies: no added features, unrelated refactors or unrequested "improvements".
5. **Clarity over cleverness.** No tricks or obscure idioms.
6. **Self-documenting code.** Descriptive names; comments explain *why*, not *what*.
7. **Fail explicitly.** Surface a clear error rather than continue with bad state.

## Project Structure

- `src/` holds the product code, `test/` the tests, `docs/` the project documentation, and `README.md` at the root says what the project is and how to build, test and run it.
- `test/` mirrors the layout of `src/`, so a file's tests are easy to find.
- Every directory has one clear purpose and groups related files. No catch-all `utils`, `misc` or `common`.
- Where the language or framework requires a different layout, follow it.

## Naming

- Files and directories use `snake_case` and are named for the one thing the file does: `parse_config`, not `helpers`. Hand-written documents follow the same rule; `README.md` is the conventional exception.
- Variables and functions use `snake_case`, constants use `UPPER_SNAKE_CASE`, and types and classes use `PascalCase`.
- Names describe purpose, not implementation: `get_active_users()`, not `query_db_filter_active()`.
- Booleans start with `is`, `has`, `can` or `should`.

## Functions and Files

- A function does one thing; a file has one clear responsibility. If you cannot name it in a few words, split it.
- Keep functions and files short. When one grows long, look for the part that can be separated or removed.
- Keep parameter lists short; group related values into one object.
- Return early instead of nesting.

## Error Handling

- Handle an error at the boundary where it can be meaningfully addressed.
- Never catch and silently ignore an exception.
- Error messages say what failed, which input caused it, and what the caller can do.

## Testing

- Work that adds or changes product behavior has tests, written test-first: the test fails before the implementation and passes after. The task's Verification section names its method (test, inspection or demonstration).
- What a test may and may not check: Verification methods in `guides/spec_authoring_guide.md`.
- Test behavior, not implementation details.
- Tests are independent (no shared mutable state) and named for the behavior: `test_returns_empty_list_when_no_users_match_filter`.

## Security

- Never hardcode credentials, API keys or secrets.
- Validate all external input: user input, API responses, file contents.
- Use parameterized database queries, never string concatenation.
- Grant least privilege for file access, network calls and permissions.

## Dependencies

- Prefer the standard library; add an external dependency only when it clearly earns its place, and justify it in the Work Log or a decision record.
- Record exact dependency versions in the project's lock file.
