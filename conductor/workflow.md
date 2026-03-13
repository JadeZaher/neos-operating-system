# NEOS Development Workflow

## Methodology: Context-Driven Development (Conductor)

Each skill layer is developed as a **track** with spec, plan, and TDD-style implementation.

## Track Structure

Each track targets one or more skill layers:
```
conductor/tracks/<track_id>/
├── spec.md       # What we're building and why
├── plan.md       # Step-by-step implementation tasks
└── metadata.json # Track state and timing
```

## Implementation Cycle

For each skill within a track:

1. **Draft SKILL.md** — Write all 12 required sections (A through L)
2. **Add OmniOne walkthrough** — Concrete example with real roles
3. **Write validation script** — Python script to verify SKILL.md structure
4. **Run stress tests** — Apply all 7 scenarios, document results in SKILL.md
5. **Create assets** — Templates, schemas, reference docs as needed
6. **Review** — Cross-reference against NEOS principles and capture resistance checks

## Quality Gates

### Per-Skill Checklist
- [ ] All 12 sections (A-L) present and substantive
- [ ] OmniOne walkthrough included with specific roles
- [ ] At least one edge case documented
- [ ] Stress-tested against 7 scenarios
- [ ] No hidden sovereign authority
- [ ] Exit compatibility confirmed
- [ ] Cross-unit interoperability impact stated

### Per-Layer Checklist
- [ ] All skills in the layer are complete
- [ ] Skills cross-reference each other correctly
- [ ] Layer README summarizes the skills and their relationships
- [ ] No circular authority dependencies

## Commit Strategy

- One commit per completed skill
- Commit message format: `neos(layer-XX): Add <skill-name> skill`
- Layer-level commits: `neos(layer-XX): Complete layer XX - <layer-name>`

## Git Notes

Used to annotate commits with:
- Stress-test results
- Review notes
- Cross-layer dependency flags

## Coverage Target

Every skill layer must have:
- 100% of required sections filled (no placeholders)
- At least 1 OmniOne walkthrough per skill
- Stress-test pass on all 7 scenarios

## Track Ordering

Priority order (foundation first):
1. Layer I (Agreement) + Layer III (ACT Engine) — these are the bedrock
2. Layer II (Authority & Role) — depends on agreements and decisions
3. Layer IX (Memory & Traceability) — needed by all other layers
4. Layer IV (Economic) — depends on agreements, authority, decisions
5. Layer V (Inter-Unit) — depends on agreements, authority, economics
6. Layer VI (Conflict & Repair) — depends on ACT, agreements, authority
7. Layer VII (Safeguard & Capture) — cross-cutting, depends on most layers
8. Layer VIII (Emergency) — depends on authority, safeguards
9. Layer X (Exit & Portability) — capstone, references all other layers
10. Global: README, validation scripts, packaging
