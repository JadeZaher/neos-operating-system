# Implementation Plan: Exit & Portability (Layer X)

## Overview

This plan builds 5 governance skills for Layer X plus layer-level integration, organized into 4 phases. The build order starts with individual exit (the most common case), moves to the operational detail of commitment unwinding, then to data portability, then to collective exit (dissolution) and re-entry. This sequence reflects both frequency of use (individual exit is most common) and dependency (commitment unwinding is part of the exit flow, portable record is generated during exit, dissolution is collective exit, re-entry completes the cycle).

**Total skills:** 5
**Total phases:** 4
**Estimated scope:** 20-28 hours of focused implementation

### Build Order Rationale

Voluntary exit is the anchor skill because it defines the overall departure flow that all other skills plug into. Commitment unwinding is the detailed operational component within that flow. Portable record is generated as part of the exit process. ETHOS dissolution is collective exit that uses the same unwinding and record mechanisms at organizational scale. Re-entry integration is built last because it references the portable record format and the departure process from the other direction.

### Commit Strategy

- One commit per completed skill: `neos(layer-10): Add <skill-name> skill`
- Layer-level commit: `neos(layer-10): Complete layer 10 - Exit & Portability`

---

## Phase 1: Scaffolding and Individual Exit

**Goal:** Create the Layer X directory structure and build the two core individual exit skills: voluntary-exit (the overall process) and commitment-unwinding (the detailed operational component). After this phase, an individual member can depart through a structured process.

### Tasks

- [ ] **Task 1.1: Create Layer X directory scaffolding**
  Create the full directory tree:
  ```
  neos-core/
    layer-10-exit/
      README.md (empty placeholder)
      voluntary-exit/           (SKILL.md, assets/, references/, scripts/)
      commitment-unwinding/     (same structure)
      portable-record/          (same structure)
      ethos-dissolution/         (same structure)
      re-entry-integration/     (same structure)
  ```
  Each skill directory gets empty `SKILL.md`, empty `assets/`, `references/`, and `scripts/` subdirectories.
  **Acceptance:** All directories exist. `find neos-core/layer-10-exit -name SKILL.md | wc -l` returns 5.

- [ ] **Task 1.2: Draft voluntary-exit SKILL.md -- sections A through F**
  Using the SKILL_TEMPLATE.md, fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without a formal exit process, departure is either traumatic (burning bridges, orphaned commitments, lost history) or impossible (social pressure, financial entanglement, unclear obligations). This skill ensures exit is a right exercised through an orderly process that respects both the departing member and the remaining community.
  - **B. Domain Scope:** Any ecosystem member at any participation level (TH, AE, OSC, Builder, Co-creator, Collaborator). The process scales to the member's commitment depth.
  - **C. Trigger Conditions:** A member decides to leave the ecosystem. The trigger is the member's own decision -- no one else can initiate a voluntary exit on their behalf (involuntary removal is a Layer VI process).
  - **D. Required Inputs:** Departing member identity, departure timeline (immediate/urgent: 7-day minimum, standard: 30 days, extended: 60 days for complex commitments), reason (optional -- never required, never coerced), notification list (auto-generated from active commitments, roles, and agreements).
  - **E. Step-by-Step Process:** Member announces departure (formal notification to all affected parties), commitment inventory (comprehensive list generated from agreement registry, role registry, proposal registry, resource ledger), handoff plan (for each commitment: identify successor, create transfer plan, set handoff date), execute handoffs (commitment-unwinding skill), generate portable record (portable-record skill), formal departure ceremony or acknowledgment (optional, culturally determined), register Departure Record, update all affected registries, confirm re-entry eligibility.
  - **F. Output Artifact:** Departure Record containing: member identity, departure date, departure timeline used, commitment handoff summary (with link to Commitment Unwinding Ledger), portable record export confirmation, re-entry eligibility status, and attestation that exit was voluntary.
  Write with full substance. Frame exit positively -- as a right, not a failure.
  **Acceptance:** Sections A-F substantive (3+ lines each), exit is framed as a right, terminology matches product-guidelines.md.

- [ ] **Task 1.3: Draft voluntary-exit SKILL.md -- sections G through L**
  Complete the remaining structural sections:
  - **G. Authority Boundary Check:** No one can prevent a member from exiting. No body can impose conditions on exit beyond the handoff timeline. The handoff timeline exists to protect remaining participants (not to trap the departing member) and has a hard minimum (7 days for urgent situations). No approval is required for departure. The departure notification is informational, not a request.
  - **H. Capture Resistance Check:** Address exit as punishment (no punitive consequences -- no loss of earned resources, no public shaming, no social penalties, no blacklisting), exit as hostage-taking (commitments cannot be designed to make exit practically impossible -- if they are, that is a governance health issue, not an exit issue), silent departure (the process creates a record -- members cannot be pressured to leave quietly so that their departure is invisible), and exit prevention through social pressure (the voluntary attestation in the Departure Record confirms the exit was not coerced).
  - **I. Failure Containment Logic:** What happens when: a member departs without following the process (commitments enter emergency-transfer protocol -- the process continues without the member, it is not held hostage to their cooperation), a member is the sole holder of a critical role with no trained successor (this is treated as a governance health issue that should have been flagged by Layer VII, not as a reason to prevent departure -- temporary role coverage is arranged), multiple members depart simultaneously (each follows the standard process, but the combined departures trigger a governance health audit and the handoff processes may need to be coordinated to avoid overloading remaining members), a departing member disputes a commitment obligation (referred to Layer VI conflict resolution with an expedited timeline).
  - **J. Expiry / Review Condition:** The departure process has a defined timeline. If the timeline expires without completed handoffs, remaining commitments enter emergency-transfer protocol. The overall exit process is reviewed annually as part of governance health auditing.
  - **K. Exit Compatibility Check:** This IS the exit skill. It must be self-consistent: a member can exit the exit process (withdraw their departure notice) at any point before the formal departure date.
  - **L. Cross-Unit Interoperability Impact:** Departure from an ETHOS does not automatically mean departure from the ecosystem. A member may exit one ETHOS and remain in others, or exit all ETHOS. The skill handles both cases. Cross-ETHOS notifications ensure that inter-unit agreements are reviewed when a member departs an ETHOS.
  **Acceptance:** Sections G-L substantive. Exit is never preventable. Graceful degradation is addressed.

- [ ] **Task 1.4: Write voluntary-exit OmniOne walkthrough and stress tests**
  Walkthrough: An AE member (Builder profile) decides to leave the Bali SHUR after 2 years. They submit departure notification with 30-day timeline. Commitment inventory reveals: 2 active circle roles (Facilitation Circle lead, Economics Circle member), 4 active agreements (UAF, SHUR space agreement, ETHOS agreement field, a project-specific agreement), 1 pending proposal in ACT advice phase, Rp 5M in stewarded assets, 111 Current-Sees. Handoff plan: Facilitation Circle lead role transfers to the current backup facilitator (who consents), Economics Circle membership is simply closed (the circle has adequate membership), UAF and SHUR agreement obligations cease upon departure, ETHOS agreement is amended to remove the member as a party (other parties consent), pending proposal is withdrawn (the member offers it to another AE member who may want to adopt it), stewarded assets returned to the stewardship pool, Current-See balance zeroed per exit protocol. Portable record generated with full 2-year history. Departure acknowledged at the next TH gathering. Re-entry eligibility: confirmed. Edge case: the Facilitation Circle's backup facilitator declines to take over. The skill's process: the role enters emergency-transfer queue, the circle must find a new lead within 14 days or request support from another circle.
  All 7 stress tests as full narratives:
  1. **Capital Influx:** A major donor departs voluntarily, taking their funding commitment with them. Walk through how the departure process handles economic commitment unwinding and triggers a resource crisis assessment.
  2. **Emergency Crisis:** A member attempts to exit during an active emergency. Walk through how exit remains a right but the handoff timeline may need adjustment for emergency roles.
  3. **Leadership Charisma Capture:** The ecosystem's most influential leader announces departure. Walk through graceful degradation and how this tests the system's capture resistance (if one departure threatens collapse, the system was captured by indispensability).
  4. **High Conflict / Polarization:** A member departs because they lost a contentious decision. Walk through ensuring the exit process is neutral and does not frame the departure as the community's failure.
  5. **Large-Scale Replication:** 5,000-member ecosystem handles 50 departures per month. Walk through process scaling and batch handoff coordination.
  6. **External Legal Pressure:** A government pressures a member to leave the ecosystem. Walk through the voluntary attestation and how it distinguishes voluntary from coerced exit.
  7. **Sudden Exit of 30%:** 15 of 50 members depart within a week. Walk through the escalated response: batch commitment unwinding, governance health audit trigger, remaining governance continuity.
  **Acceptance:** Walkthrough names specific OmniOne roles and includes realistic commitment details. Stress tests are full narratives.

- [ ] **Task 1.5: Finalize voluntary-exit SKILL.md and create assets**
  Assemble SKILL.md with YAML frontmatter:
  ```yaml
  ---
  name: voluntary-exit
  description: "Process an individual member's voluntary departure -- notification, commitment handoff, data export, formal departure record, and re-entry eligibility confirmation. Exit is a right, not a failure."
  layer: 10
  version: 0.1.0
  depends_on: []
  ---
  ```
  Create `assets/departure-record-template.yaml` (member identity, departure date, timeline used, reason -- optional, commitment handoff summary, portable record export confirmation, re-entry eligibility, voluntary attestation).
  Create `assets/departure-checklist.yaml` (step-by-step checklist: notification sent, commitment inventory complete, handoff plan created, handoffs executed, portable record generated, registries updated, departure record filed).
  Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines. Both asset files complete.

- [ ] **Task 1.6: Draft commitment-unwinding SKILL.md -- full skill**
  Build the complete commitment unwinding skill:
  - **A:** A member's commitments do not vanish when they depart. Without structured unwinding, commitments become orphaned -- agreements have missing parties, roles have no holder, proposals have no author, and resources have no steward. This skill ensures every commitment is explicitly addressed: transferred, closed, or wound down.
  - **B:** Any departing member's active commitments, regardless of type or scope. Also applicable to ETHOS dissolution (collective commitment unwinding).
  - **C:** A voluntary-exit process has generated a commitment inventory, or an ETHOS dissolution process requires commitment settlement.
  - **D:** The commitment inventory (from voluntary-exit or dissolution process), the member's role registry entries, agreement registry entries, proposal registry entries, resource ledger entries, and active conflict resolution references.
  - **E:** Review each commitment by category and apply the appropriate protocol:
    1. **Role obligations:** Identify successor (from backup list or circle nomination). Transfer role with handoff meeting. If no successor: role enters emergency-transfer queue, circle distributes responsibilities temporarily.
    2. **Agreement obligations:** For agreements where the member is a party: amend to remove party (with consent of remaining parties) or transfer party status to a replacement. For the UAF: obligations cease upon departure.
    3. **Economic commitments:** Settle outstanding obligations (resource returns, debt settlement). Return stewarded assets to stewardship pool. Transfer access rights per agreement terms. For OmniOne: Current-See balance is zeroed per exit protocol.
    4. **Pending proposals:** Withdraw (proposer right) or transfer authorship to willing recipient (requires recipient's consent and re-entry into advice phase for the new author).
    5. **Active conflict resolutions:** If near completion (within one session): expedite to completion. If early stage: transfer mediator/party role or formally pause with documented context and timeline for resumption.
    Document each unwinding action. Get acknowledgment from receiving parties.
  - **F:** Commitment Unwinding Ledger (each commitment: original state, category, unwinding action, receiving party, acknowledgment status, completion date).
  - **G:** The departing member cannot be held beyond their departure timeline. If unwinding is incomplete at the deadline, remaining items enter emergency-transfer protocol. The receiving party cannot refuse a transfer that they are structurally obligated to accept (e.g., a circle must accept responsibility for roles within its domain) -- but individuals within the circle can consent to who specifically takes on the role.
  - **H:** Address weaponized commitments (designing commitments to prevent exit), selective unwinding (strategically abandoning some commitments while carefully transferring others), and pressure to rush unwinding (compromising handoff quality to get the member out faster).
  - **I-L:** Full structural sections.
  - Walkthrough: Unwinding for the departing AE member from the voluntary-exit walkthrough. Walk through each of the 5 commitment categories with specific actions, receiving parties, and timelines. Show one complication: the project-specific agreement has a clause requiring 60-day notice for party changes, but the member's departure timeline is 30 days. Resolution: the agreement's exit clause is negotiated with remaining parties for an expedited 30-day amendment.
  - All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines. All 5 commitment categories have clear unwinding protocols.

- [ ] **Task 1.7: Create commitment-unwinding assets**
  Create `assets/commitment-unwinding-ledger-template.yaml` (departure record reference, entries per commitment: commitment ID, category, description, original state, unwinding action, receiving party, acknowledgment status, completion date, notes).
  Create `assets/unwinding-protocols-by-type.yaml` (5 categories with step-by-step protocols: roles, agreements, economic, proposals, conflicts).
  **Acceptance:** Both templates complete.

- [ ] **Verification 1: Run validate_skill.py against both completed skills. Confirm both pass. Verify that commitment-unwinding is referenced by voluntary-exit. Verify that all 5 commitment categories are addressed. Verify that exit is never preventable in either skill's formulation.** [checkpoint marker]

---

## Phase 2: Data Portability

**Goal:** Build the portable record skill that enables governance history to travel with departing members. After this phase, members can depart with a verified, structured record of their participation.

### Tasks

- [ ] **Task 2.1: Draft portable-record SKILL.md -- full skill**
  Build the complete portable record skill:
  - **A:** Without portable governance history, members who move between ecosystems or ETHOS start from zero each time. This erases institutional knowledge, disincentivizes productive participation, and makes exit more costly (you lose your reputation). This skill ensures governance participation is owned by the participant, exportable in a standard format, and verifiable by receiving ecosystems.
  - **B:** Any ecosystem member, whether departing or simply requesting a copy of their record. The skill operates on demand (member request) or as part of the voluntary-exit process.
  - **C:** A member requests their portable record (at any time, not just during exit), a voluntary-exit process reaches the record generation step, or an ETHOS dissolution requires member record generation.
  - **D:** The member's identity, the source registries (agreement registry, proposal registry, decision logs, role registry, resource ledger, conflict resolution records, governance health audit participation records, Current-See transaction ledger for OmniOne).
  - **E:** Compile record from source registries, generate draft record with all available data, present to member for privacy review (member chooses which elements to include in the exported version -- mandatory elements limited to: identity verification, ecosystem membership dates, and departure status if applicable; all governance participation details are opt-in), generate structured export (YAML primary, JSON alternative), generate human-readable markdown summary, generate verification hash (cryptographic hash of the exported record computed against source registry snapshots -- allows a receiving ecosystem to verify the record was not modified after export without requiring ongoing connection), deliver to member.
  - **F:** Portable Governance Record (structured data file in YAML/JSON + human-readable markdown summary + verification hash + metadata: export date, exporting ecosystem, record version).
  - **G:** The member controls their record. The ecosystem cannot prevent export, cannot selectively filter unfavorable records, cannot add editorial commentary. The ecosystem retains its own copies of governance data (for its own continuity) but the member's exported copy is their own.
  - **H:** Address data hostage-taking (withholding the record to prevent exit -- the skill makes record generation a structural right, not a privilege). Address selective export by ecosystem (ecosystem filtering the record -- the member sees all their data and chooses what to include). Address record falsification (the verification hash prevents post-export modification). Address record inflation (members exaggerating their contributions -- the record is compiled from source registries, not self-reported).
  - **I:** What happens when: source registry data is incomplete (the record notes gaps -- "agreement registry data available from [date] to [date]"), the member requests data that the ecosystem does not maintain (the record reflects what exists, not what the member wishes existed), the verification hash does not match at a receiving ecosystem (the receiving ecosystem can request a re-export or contact the originating ecosystem for clarification -- but mismatch does not invalidate the record, it flags it for review).
  - **J-L:** Full structural sections.
  - OmniOne-specific record elements: Current-See transaction history, SHUR residence tenure, ETHOS membership records, NEXUS onboarding date.
  - Walkthrough: The departing AE member requests their portable record. The system compiles: 2 years of membership, 14 proposals authored (9 adopted, 3 under test, 2 reverted), 47 ACT consent participations, 2 circle lead roles (Facilitation: 8 months, Economics: 14 months), 3 conflict resolution participations (all resolved), 456 Current-See transactions. The member reviews and opts out of exporting conflict resolution details (privacy choice). The record is generated in YAML with markdown summary. Verification hash computed. The member later presents this record when joining the Costa Rica SHUR. The Costa Rica ETHOS verifies the hash, reviews the summary, and acknowledges the member's governance experience during onboarding. Edge case: one of the member's proposals was reverted after a negative test phase. This appears in the record as a factual entry -- the record does not editorialize about success or failure.
  - All 7 stress tests with specific attention to: Scenario 5 (Large-Scale Replication -- how does record generation scale to 5,000 members each with years of history?), Scenario 6 (External Legal Pressure -- a government demands access to a member's portable record), Scenario 7 (30% exit -- can the system generate 15 portable records simultaneously?).
  **Acceptance:** Passes validation. Under 500 lines. Privacy by design is structural. Verification mechanism is credible.

- [ ] **Task 2.2: Create portable-record assets**
  Create `assets/portable-record-schema.yaml` (record metadata: export date, exporting ecosystem, ecosystem ID, record version; member identity: verified name/pseudonym, membership dates; sections: roles held, agreements, proposals, act participation, conflict resolution, economic, governance health audit participation, ecosystem-specific data; verification: hash algorithm, hash value, source registry snapshot references).
  Create `assets/portable-record-example.yaml` (a complete example record for a fictional OmniOne member with 2 years of history, showing all fields populated).
  **Acceptance:** Both templates complete. Example record is realistic and comprehensive.

- [ ] **Verification 2: Run validate_skill.py against all 3 completed skills. Confirm all pass. Verify that portable-record is referenced by voluntary-exit in the correct process step. Verify the record schema covers data from all earlier layers. Verify privacy controls are structural, not aspirational.** [checkpoint marker]

---

## Phase 3: Collective Exit and Re-Entry

**Goal:** Build ETHOS dissolution and re-entry integration. After this phase, all 5 Layer X skills are complete.

### Tasks

- [ ] **Task 3.1: Draft ethos-dissolution SKILL.md -- full skill**
  Build the complete ETHOS dissolution skill:
  - **A:** Organizations end. Without a structured dissolution process, ending is chaotic: assets are disputed, commitments are orphaned, members are stranded, and records are lost. This skill ensures that collective exit is as orderly as individual exit, with fair treatment of all parties.
  - **B:** Any ETHOS within a NEOS ecosystem. The skill handles the entire dissolution lifecycle from proposal to completion.
  - **C:** A dissolution proposal is submitted by an ETHOS member (requiring supermajority consent), the ETHOS has been unable to achieve decision-making quorum for 3 consecutive scheduled meetings (governance incapacity trigger), or ecosystem-level intervention (rare, requires full ecosystem ACT process with ETHOS members as affected parties).
  - **D:** The dissolution proposal (if member-initiated), current membership list, asset inventory, active agreements list, active commitments list, inter-ETHOS relationship inventory, and the applicable dissolution protocol (from assets).
  - **E:** Phase 1: Proposal and impact assessment (submit dissolution proposal through ACT with extended 30-day advice period, conduct impact assessment covering members, agreements, assets, commitments, inter-unit relationships). Phase 2: Consent round (supermajority threshold: 2/3 of active members; if achieved, dissolution proceeds; if not, proposal fails and may be resubmitted after 6 months). Phase 3: Commitment settlement (apply commitment-unwinding at organizational scale -- settle all agreements, fulfill or transfer all obligations, notify all inter-ETHOS partners). Phase 4: Asset disposition (ordered process: settle debts and obligations, return stewarded assets to original stewards or their successors, distribute remaining assets per pre-agreed formula or consent of remaining members at time of dissolution). Phase 5: Member transition (each member either transfers to another ETHOS using re-entry-integration process, or exits the ecosystem using voluntary-exit process -- each member generates a portable record). Phase 6: Record preservation (all ETHOS governance records archived in ecosystem memory layer -- records are not destroyed). Phase 7: Formal dissolution record (registered in ecosystem records, all affected registries updated).
  - **F:** Dissolution Record (dissolution vote record, impact assessment, commitment settlement ledger, asset disposition ledger, member transition records, archive reference, formal dissolution date).
  - **G:** No external body can unilaterally dissolve an ETHOS. Ecosystem-level intervention requires full ACT process with ETHOS members having voice. The dissolution supermajority (2/3) protects minority voice without giving it veto. Asset disposition follows a defined order (debts first, then stewardship returns, then member distribution) -- no one can jump the queue.
  - **H:** Address forced dissolution (using dissolution as a weapon against a dissenting ETHOS -- the supermajority requirement and the ACT process protect against this), asset capture during dissolution (leadership directing assets to favored members -- the ordered disposition process prevents this), and dissolution avoidance (an ETHOS that should dissolve continuing to operate ineffectively because no one wants to propose dissolution -- the governance incapacity trigger addresses this automatically).
  - **I-L:** Full structural sections.
  - Walkthrough: A small ETHOS in Bali with 4 remaining members (down from 12) can no longer sustain operations. Two members have moved away, one has reduced participation, and the 4th is overloaded. One member submits a dissolution proposal. Impact assessment reveals: 2 inter-ETHOS agreements (one with the main Bali SHUR, one with the Costa Rica ETHOS), 1 shared resource allocation, minimal assets (shared equipment and a small operational fund), 3 active agreements (UAF, ETHOS charter, shared workspace agreement). Extended advice period: the main Bali SHUR offers to absorb the dissolving ETHOS's members and commitments. 2 of 4 members want to join the main SHUR, 1 wants to exit the ecosystem, 1 wants to transfer to Costa Rica. Consent round: 3 of 4 consent (supermajority met), 1 stands aside. Dissolution proceeds through the 7 phases. Edge case: the shared equipment was donated by a member who already exited -- the stewardship return goes to the original donor's designated successor per the asset's stewardship record.
  - All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines. All 7 dissolution phases are clear. No forced dissolution.

- [ ] **Task 3.2: Create ethos-dissolution assets**
  Create `assets/dissolution-record-template.yaml` (ETHOS ID, dissolution date, trigger type, proposal record, consent record, impact assessment, commitment settlement ledger, asset disposition ledger, member transition records, archive reference).
  Create `assets/dissolution-checklist.yaml` (step-by-step checklist for the 7 dissolution phases with specific items per phase).
  **Acceptance:** Both templates complete.

- [ ] **Task 3.3: Draft re-entry-integration SKILL.md -- full skill**
  Build the complete re-entry integration skill:
  - **A:** Governance systems often treat returning members either as strangers (ignoring their history) or as insiders (assuming nothing has changed). This skill provides a structured middle path: acknowledge history, verify credentials, update consent, and integrate with awareness of what has changed in both directions.
  - **B:** Any NEOS ecosystem or ETHOS that receives a re-entry request from a former member. Also applicable to cross-ecosystem entry using a portable record.
  - **C:** A former member requests re-entry, presenting a portable record. Or a member of one ETHOS requests entry to a different ETHOS within the same ecosystem.
  - **D:** The returning member's identity, their portable record (verified), the current UAF (may have changed since departure), current agreements applicable to the requested ETHOS/role, the member's original departure record, and any re-entry conditions from conflict resolution (if applicable).
  - **E:** Receive re-entry request, verify portable record (check verification hash against archived data if available -- for cross-ecosystem entry, contact originating ecosystem or accept hash-verified record), review departure circumstances (was it voluntary exit? were there conflict resolution conditions? are those conditions satisfied?), present current agreements (UAF, ETHOS-specific agreements -- the returning member must consent to current versions, not the versions they originally consented to), acknowledge governance history (the ecosystem recognizes the member's participation record without necessarily reinstating their previous roles), role eligibility assessment (previous experience is relevant but does not guarantee role reinstatement -- current role holders are not displaced, openings are filled through normal processes), create re-entry record (linked to departure record and portable record), update registries, welcome integration (optional community acknowledgment).
  - **F:** Re-Entry Record (member identity, portable record reference, departure record reference, verified history summary, current agreements consented to, role eligibility assessment, re-entry date, any special conditions and their status).
  - **G:** Re-entry cannot be denied arbitrarily. Rejection requires a specific, stated reason that is subject to Layer VI conflict resolution. However, re-entry is not unconditional: the returning member must consent to current agreements (which may have changed). If they cannot consent, they cannot re-enter (just as any new member who cannot consent to the UAF cannot enter). Role reinstatement is not guaranteed -- the skill defines eligibility, not entitlement.
  - **H:** Address gatekeeping (using re-entry process to selectively exclude political opponents -- the process is standardized with clear criteria), preferential treatment (fast-tracking allies -- timelines are fixed), history erasure (ignoring the portable record -- the skill structurally requires record review), and conditional re-entry used as leverage (placing unreasonable conditions -- conditions must come from formal conflict resolution, not informal authority, and are time-limited).
  - **I-L:** Full structural sections.
  - Walkthrough: A former AE member returns after 18 months. They present their portable record. The ecosystem verifies the hash against archived data -- match confirmed. Departure was voluntary, no conflict resolution conditions. The returning member reviews the current UAF and discovers it was amended 6 months after their departure (a new stewardship commitment was added). They consent to the current UAF. They express interest in rejoining the Economics Circle where they previously served as lead. The circle currently has a lead. The returning member is welcomed as a circle member with acknowledgment of their 14 months of previous lead experience. They are eligible for the lead role at the next rotation. Portable record's proposal history is noted -- their 9 adopted proposals inform the ecosystem's understanding of their capabilities. Edge case: the returning member's portable record includes a high-conflict proposal that divided the ecosystem before their departure. The skill's process: the record is factual, not editorial. The proposal's history is part of the record. The returning member is not penalized for having authored a controversial proposal.
  - All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines. Re-entry is neither automatic nor arbitrary. History is acknowledged, not ignored or weaponized.

- [ ] **Task 3.4: Create re-entry-integration assets**
  Create `assets/re-entry-record-template.yaml` (member identity, re-entry date, portable record reference, departure record reference, verification status, departure type, re-entry conditions -- if any, current agreements consented to, role eligibility assessment, integration notes).
  Create `assets/re-entry-checklist.yaml` (step-by-step checklist: receive request, verify record, review departure circumstances, present current agreements, consent check, role eligibility, create re-entry record, update registries).
  **Acceptance:** Both templates complete.

- [ ] **Verification 3: Run validate_skill.py against all 5 completed skills. All must pass. Verify that the exit lifecycle is coherent: a member can depart through voluntary-exit with commitment-unwinding, take a portable-record, and return through re-entry-integration. Verify that ethos-dissolution uses the same commitment-unwinding and portable-record mechanisms at organizational scale. No circular dependencies.** [checkpoint marker]

---

## Phase 4: Layer Integration and Cross-Layer Verification

**Goal:** Write the Layer X README, verify cross-layer references across all 10 layers, and confirm all quality gates pass.

### Tasks

- [ ] **Task 4.1: Write layer-10-exit README.md**
  Write the layer README summarizing:
  - Layer purpose: Ensure exit is a structural right with graceful degradation
  - Hirschman's framework: the design balance between too-costly and too-easy exit
  - The 5 skills and their relationships (individual exit flow, collective exit flow, re-entry flow)
  - Cross-layer dependencies (this is the capstone layer -- how it touches all 9 earlier layers)
  - The portable record as cross-ecosystem bridge
  - Graceful degradation principle
  **Acceptance:** README accurately describes all 5 skills and their relationships. Cross-layer dependency map is complete.

- [ ] **Task 4.2: Cross-layer reference verification**
  Review all 5 SKILL.md files for:
  - References to all earlier layers (I through IX) use correct skill names
  - The commitment unwinding categories map to actual commitment types from earlier layers (roles from Layer II, agreements from Layer I, proposals from Layer III, economics from Layer IV, conflicts from Layer VI)
  - Portable record schema includes data from all relevant earlier layers
  - Emergency role succession is addressed for departing members (Layer VIII cross-reference)
  - Governance health audit is triggered by mass departure (Layer VII cross-reference)
  - No circular authority dependencies
  **Acceptance:** All cross-references verified. Every earlier layer is appropriately referenced.

- [ ] **Task 4.3: Run full validation and quality gate review**
  Run `validate_skill.py` against all 5 skills. Review against per-skill and per-layer checklists:
  Per-skill:
  - [ ] All 12 sections (A-L) present and substantive
  - [ ] OmniOne walkthrough included with specific roles
  - [ ] At least one edge case documented
  - [ ] Stress-tested against 7 scenarios
  - [ ] No hidden sovereign authority
  - [ ] Exit compatibility confirmed (self-referential for this layer -- must be internally consistent)
  - [ ] Cross-unit interoperability impact stated
  Per-layer:
  - [ ] All 5 skills complete
  - [ ] Skills cross-reference each other correctly
  - [ ] Layer README summarizes skills and relationships
  - [ ] No circular authority dependencies
  - [ ] Exit is always treated as a right, never a punishment
  - [ ] Graceful degradation is structural, not aspirational
  **Acceptance:** All checks pass. Layer X is complete.

- [ ] **Verification 4: Final layer review. All 5 skills pass validation. README is complete. The layer provides a complete exit lifecycle: individual departure, commitment unwinding, data portability, collective dissolution, and re-entry. Cross-layer references are accurate across all 10 layers. Exit is structurally ensured as a right. Commit: `neos(layer-10): Complete layer 10 - Exit & Portability`** [checkpoint marker]
