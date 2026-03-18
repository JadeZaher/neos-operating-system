# NEOS Product Guidelines

## Voice & Tone

**Inspirational & Structural** — NEOS documents combine precise protocol language with the philosophical grounding of the project.

- Use clear structural definitions (inputs, outputs, triggers, boundaries)
- Ground language in sovereignty, stewardship, and solutionary principles
- Avoid bureaucratic dryness — this is a living system, not a legal code
- Avoid vague idealism — every aspiration must have a structural mechanism
- When a concept could be misunderstood, define it explicitly
- Use active voice: "The proposer submits..." not "A proposal is submitted..."

## Terminology Standards

| Term | Meaning | Do NOT use |
|------|---------|------------|
| ETHOS | Emergent Thriving Holonic Organizational Structure — an organizational unit | "department", "team" (too corporate) |
| Current-See | Influence currency (111 per person, equal) | "token", "vote" (implies purchasability or majority-rule) |
| Domain | Invisible boundary within which a circle can make decisions | "jurisdiction" (implies sovereign authority) |
| Steward | Person who holds responsibility, not ownership | "owner", "manager" |
| ACT | Advice → Consent → Test decision protocol | "voting", "approval process" |
| Agreement Field | The set of active agreements governing a space or interaction | "contract", "rules" |
| Circle | A self-organizing group with a defined domain | "committee" |
| Ecosystem | The federated whole (e.g., OmniOne) | "organization", "company" |

## Skill Document Standards

### Every SKILL.md must include:
1. YAML frontmatter with `name` and `description` (description should be "pushy" — err toward triggering the skill)
2. All 12 required sections (A through L) from the skill template
3. A concrete OmniOne walkthrough example showing how the skill plays out with real roles (OSC, AE, TH, GEV, etc.)
4. Stress-test results against all 7 scenarios

### Writing principles:
- **Concrete over abstract** — If you can't explain how it works with a real example, it's not ready
- **Process over philosophy** — Every section must describe what happens, not what should be believed
- **Boundaries over permissions** — Define what authority CANNOT do, not just what it can
- **Degradation over perfection** — Describe what happens when the skill fails, not just when it succeeds

## Design Principles

1. **Modularity** — Every skill must function independently. No skill should require another skill to be "installed" to operate (though skills may reference each other)
2. **No hidden authority** — If a step requires someone to make a judgment call, that person's authority scope must be stated
3. **Reversibility by default** — Prefer reversible actions. Irreversible actions require higher consent thresholds
4. **Consent, not consensus** — "No one has a reasoned objection" is the bar, not "everyone enthusiastically agrees"
5. **Expiry over permanence** — Agreements, roles, and authority expansions should have review dates by default

## File Structure Per Skill

```
skill-name/
├── SKILL.md          # YAML frontmatter + markdown (< 500 lines)
├── scripts/          # Executable code for deterministic tasks
├── references/       # Docs loaded into context as needed
└── assets/           # Templates, schemas, examples
```

## UI Styling Standards

**All dashboard UI uses Tailwind CSS exclusively.**
- No custom CSS files, no `<style>` blocks, no CSS custom properties
- Tailwind 4.x via CDN
- NEOS brand colors in Tailwind config: `neos-primary` (#2D5A27), `neos-accent` (#7CB342), etc.
- Responsive: `sm:`, `md:`, `lg:` breakpoints
- Accessibility: focus rings, ARIA labels, semantic HTML

## OmniOne Example Standards

Every OmniOne walkthrough must:
- Name specific roles (e.g., "A TH member proposes...", "The OSC reviews...")
- Show the actual flow of a realistic scenario
- Include at least one edge case or complication
- End with the output artifact that gets produced
