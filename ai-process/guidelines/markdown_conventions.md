# Markdown Conventions

Generated project artifacts are Markdown.
These conventions apply to bugs, tasks, specs, ADRs, and role/procedure outputs created by the AI team.

## Frontmatter

Every artifact the `ai-team` CLI creates from a bundled template (task, bug, change-request, spec, ADR, status report) starts with YAML frontmatter enclosed in `---` fences:

```yaml
---
title: "Document Title"
status: draft
created: 2026-01-15
---
```

Additional fields depend on document type. The bundled templates in the CLI package (`cli/src/ai_team/templates/<type>.md`) show the required fields.
Hand-written documents — guides, project guidance, coding guidelines, process documents — carry no frontmatter.

## Headings

- Use ATX-style headings (`#`, `##`, `###`).
- Do not skip levels (no `#` followed directly by `###`).
- One `#` heading per file (the document title).
- Leave a blank line before and after headings.

## Text

- Use one sentence per line in the source file.
- Use blank lines to separate paragraphs.
- Do not use trailing spaces for line breaks — use blank lines instead.

## Lists

- Use `-` for unordered lists.
- Use `1.` for ordered lists (actual numbers, not all `1.`).
- Use `- [ ]` for checklists.
- Indent nested lists with 2 spaces.

## Code

- Use fenced code blocks with language identifiers:
  ````
  ```python
  def example():
      pass
  ```
  ````
- Use inline code (`backticks`) for file paths, variable names, and short code references.

## Tables

- Use pipe tables with header separators.
- Align columns for readability in source (optional, but preferred).
- Always include a header row.

```markdown
| Column A | Column B | Column C |
|---|---|---|
| Value | Value | Value |
```

## Links and References

- Use relative paths for cross-references within the repo: `[Quality Gates](ai-process/processes/quality_gates.md)`.
- Use descriptive link text — not "click here" or bare URLs.

## Diagrams

- Use ASCII art in fenced code blocks for diagrams.
- Use box-drawing characters or simple ASCII (`|`, `-`, `+`, `→`, `↓`).
- Label all components clearly.

## File Naming

- Hand-written documents use lowercase snake_case: `my_document_name.md`.
- Conventional entry-point files keep their usual names: `README.md`, `AGENTS.md`, `SKILL.md`.
- Artifacts keep the names the `ai-team` CLI gives them: `T-NNN-<slug>.md`, `B-NNN-<slug>.md`, `CR-NNN-<slug>.md`, `S-NNN-<slug>.md`, `ADR-NNN-<slug>.md`.
- Skill folders use lowercase names with hyphens (`spec-breakdown/`), as Claude Code requires.
- Bundled artifact templates are named after the artifact type they render: `task.md`, `change-request.md`.
