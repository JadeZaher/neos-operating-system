# Markdown Style Guide — NEOS Documents

## SKILL.md Format
- YAML frontmatter: `name` (kebab-case), `description` (1 sentence, pushy)
- Max 500 lines per SKILL.md
- Use ATX headers (`#`, `##`, `###`) — never setext
- One blank line before and after headers

## Section Ordering (Required)
A through L sections must appear in order. Use `## A. Structural Problem It Solves` format.

## Lists
- Use `-` for unordered lists (not `*`)
- Use `1.` for ordered lists (not auto-numbering)
- Indent nested lists with 2 spaces

## Emphasis
- **Bold** for key terms on first use
- *Italic* for OmniOne-specific terms
- `code` for file names, script names, technical identifiers

## Tables
- Use markdown tables for structured comparisons
- Always include header row and alignment

## OmniOne Examples
- Wrap in `> **OmniOne Example:**` blockquote sections
- Use concrete role names (OSC, AE, TH, GEV)

## Links
- Use relative links within the repo
- Reference other skills as `[Agreement Creation](../layer-01-agreement/agreement-creation/SKILL.md)`
