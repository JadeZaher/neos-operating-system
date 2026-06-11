"""
Personas for the NEOS seed-data fixture.

14 named members of the OmniOne ecosystem, each with a consistent
identity, role, and backstory.  Every persona exists as a User + Member
record and can be referenced by UUID across all other seed modules.

Canon characters (do not change identity or role):
  - Lani   — resource pool steward
  - Kai    — conflict facilitator / triager
  - Manu   — ecosystem architect (OmniOne co-founder)

Design note: UUIDs are deterministic (namespace v5) so cross-module
references are stable without a live database.
"""

from __future__ import annotations

import uuid

# Deterministic namespace for generating stable persona UUIDs
_PERSONA_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _pid(name: str) -> uuid.UUID:
    """Deterministic persona UUID."""
    return uuid.uuid5(_PERSONA_NS, name)


# ── Persona definitions ────────────────────────────────────────────

PERSONAS: list[dict] = [
    # ── Canon ──────────────────────────────────────────────────────
    {
        "id": _pid("lani"),
        "username": "lani",
        "display_name": "Lani Wijaya",
        "member_id": "M-001",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["resource stewardship", "participatory budgeting"],
            "secondary": ["permaculture design", "community facilitation"],
        },
        "skills_needed": {"seeking": ["legal advisory for commons trusts"]},
        "interests": {"focus": ["regenerative agriculture", "water commons"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Canon.  Lani stewards the OmniOne resource pool.  She grew up in a "
            "Balinese subak (water temple cooperative) and brings 12 years of "
            "experience managing shared irrigation resources.  Her core belief: "
            "'A commons is not a resource — it is a relationship.'  She is warm, "
            "methodical, and allergic to financial opacity."
        ),
        "backstory": (
            "Born in Ubud, Bali.  Worked as a subak water scheduler for 8 years "
            "before joining GEV.  Co-designed OmniOne's participatory allocation "
            "process.  Holds a degree in ecological economics from Udayana University.  "
            "Fluent in Balinese, Indonesian, and English."
        ),
    },
    {
        "id": _pid("kai"),
        "username": "kai",
        "display_name": "Kai Nakamura",
        "member_id": "M-002",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["conflict facilitation", "NVC mediation", "triage assessment"],
            "secondary": ["trauma-informed facilitation", "circle-keeping"],
        },
        "skills_needed": {"seeking": ["cross-cultural conflict frameworks"]},
        "interests": {"focus": ["restorative justice", "transformative justice"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Canon.  Kai is OmniOne's lead conflict facilitator and escalation triager.  "
            "He spent 10 years mediating land disputes in post-conflict Sri Lanka before "
            "moving to Bali.  His approach blends NVC, transformative justice, and "
            "a dry sense of humor.  He believes 'every conflict is a governance gap "
            "asking to be filled.'"
        ),
        "backstory": (
            "Born in Kyoto, Japan.  Trained in NVC at BayNVC (Oakland, CA).  "
            "Worked with the Asia Justice and Rights network in Colombo for a decade.  "
            "Joined OmniOne in 2024 to build a conflict system that doesn't rely on "
            "courts or punishment.  Speaks Japanese, English, Sinhala, and basic Indonesian."
        ),
    },
    {
        "id": _pid("manu"),
        "username": "manu",
        "display_name": "Manu Dewantara",
        "member_id": "M-003",
        "current_status": "active",
        "profile": "co_creator",
        "skills_offered": {
            "primary": ["ecosystem architecture", "governance design", "systems thinking"],
            "secondary": ["facilitation", "strategic foresight"],
        },
        "skills_needed": {"seeking": []},
        "interests": {"focus": ["polycentric governance", "exit-to-community", "Ostrom"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Canon.  Manu co-founded OmniOne and serves as the ecosystem architect.  "
            "He designed the original 10-layer NEOS stack.  His intellectual north star "
            "is Elinor Ostrom; his operational obsession is that governance must survive "
            "its own success.  He is reflective, soft-spoken, and relentless about "
            "structural integrity."
        ),
        "backstory": (
            "Born in Yogyakarta, Indonesia.  PhD in institutional economics from ANU.  "
            "Studied under scholars who worked directly with Ostrom.  Spent 5 years "
            "consulting for community land trusts across Southeast Asia.  Founded OmniOne "
            "with GEV after witnessing the collapse of three well-intentioned co-ops — "
            "all of which failed due to governance design flaws he now recognizes."
        ),
    },

    # ── Extended cast ──────────────────────────────────────────────
    {
        "id": _pid("nirmala"),
        "username": "nirmala",
        "display_name": "Nirmala Sari",
        "member_id": "M-004",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["agreement drafting", "legal translation", "policy analysis"],
            "secondary": ["community organizing", "advocacy"],
        },
        "skills_needed": {"seeking": ["environmental law mentorship"]},
        "interests": {"focus": ["universal agreement field", "legal pluralism"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Nirmala is OmniOne's agreement steward.  She drafts and reviews agreements "
            "at every hierarchy level.  A former environmental lawyer turned community "
            "organizer, she is precise with language and fierce about accessibility — "
            "'If a farmer can't read our UAF, the UAF is broken.'"
        ),
        "backstory": (
            "Born in Denpasar, Bali.  LL.B from Universitas Indonesia, practiced "
            "environmental law for 6 years at WALHI (Friends of the Earth Indonesia).  "
            "Left formal legal practice after watching communities lose land rights "
            "despite winning court cases.  Joined OmniOne to build agreements that "
            "communities can enforce themselves."
        ),
    },
    {
        "id": _pid("dewa"),
        "username": "dewa",
        "display_name": "Dewa Putra",
        "member_id": "M-005",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["emergency coordination", "disaster response", "logistics"],
            "secondary": ["first aid training", "radio communication"],
        },
        "skills_needed": {"seeking": ["crisis mental health support"]},
        "interests": {"focus": ["emergency preparedness", "circuit breaker design"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Dewa is OmniOne's emergency coordinator.  A former SAR (search and rescue) "
            "team leader who responded to the 2018 Lombok earthquakes.  He designed "
            "OmniOne's emergency criteria and pre-authorization protocols.  His motto: "
            "'Crisis planning happens on sunny days.'  He is calm under pressure and "
            "deeply suspicious of anyone who wants emergency powers extended."
        ),
        "backstory": (
            "Born in Singaraja, North Bali.  Served in BASARNAS (national SAR) for 7 years.  "
            "Deployed to Aceh tsunami, Lombok earthquakes, and Mount Agung eruption.  "
            "Left government service frustrated by bureaucratic inertia during crises.  "
            "Joined OmniOne to build a governance system where emergencies trigger "
            "pre-authorized responses, not power grabs."
        ),
    },
    {
        "id": _pid("indra"),
        "username": "indra",
        "display_name": "Indra Gunawan",
        "member_id": "M-006",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["software development", "database design"],
            "secondary": ["open-source governance tools", "API design"],
        },
        "skills_needed": {"seeking": ["UX research collaboration"]},
        "interests": {"focus": ["digital governance infrastructure", "data portability"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Indra builds the NEOS agent and the digital governance infrastructure.  "
            "He is the bridge between the governance design and the software that runs it.  "
            "Self-taught programmer from a farming family in East Java.  Deeply committed "
            "to data portability and the right to exit — he knows what it's like to be "
            "locked into a platform."
        ),
        "backstory": (
            "Born in Banyuwangi, East Java.  Learned to code through online communities "
            "while helping his family's coffee farm.  Built digital tools for community "
            "land-mapping projects across Indonesia.  Joined OmniOne to ensure the "
            "governance system has a digital backbone that respects exit rights."
        ),
    },
    {
        "id": _pid("sari"),
        "username": "sari",
        "display_name": "Sari Dewi",
        "member_id": "M-007",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["proposal facilitation", "ACT process guidance"],
            "secondary": ["meeting design", "consensus-building"],
        },
        "skills_needed": {"seeking": ["large-group facilitation techniques"]},
        "interests": {"focus": ["decision-making systems", "deliberative democracy"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Sari is OmniOne's proposal steward.  She shepherds proposals through the "
            "ACT process — advice, consent, test — and ensures no step is skipped.  "
            "A former high-school civics teacher who discovered Sociocracy at a workshop "
            "and never looked back.  Known for her patience and her refusal to let "
            "proposals get 'informally resolved' in hallway conversations."
        ),
        "backstory": (
            "Born in Mataram, Lombok.  Taught civics at SMAN 2 Mataram for 9 years.  "
            "After a school-funding decision was made by fiat with catastrophic results, "
            "she started researching alternative decision-making systems.  Found Sociocracy "
            "3.0 and co-founded a community decision-making circle.  Joined OmniOne in 2025."
        ),
    },
    {
        "id": _pid("gede"),
        "username": "gede",
        "display_name": "Gede Artha",
        "member_id": "M-008",
        "current_status": "active",
        "profile": "townhall",
        "skills_offered": {
            "primary": ["construction", "bamboo engineering"],
            "secondary": ["traditional Balinese architecture"],
        },
        "skills_needed": {"seeking": ["sustainable building materials sourcing"]},
        "interests": {"focus": ["eco-construction", "community housing"]},
        "onboarding_status": "complete",
        "kyc_status": "unverified",
        "notes": (
            "Gede joined OmniOne through the Town Hall track — he is a craftsman, not "
            "a governance wonk, and that is exactly why his participation matters.  He "
            "represents the people NEOS is designed to serve.  He struggles with the "
            "English-heavy documentation and has pushed (successfully) for Balinese-language "
            "versions of core agreements."
        ),
        "backstory": (
            "Born in Karangasem, East Bali.  Third-generation bamboo builder.  Built "
            "three of GEV's SHUR facilities.  Joined OmniOne because the SHUR he built "
            "was governed by people who never stepped on the construction site.  He believes "
            "'the people who build the place should help decide how it runs.'"
        ),
    },
    {
        "id": _pid("melati"),
        "username": "melati",
        "display_name": "Melati Kusuma",
        "member_id": "M-009",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["governance auditing", "capture detection", "data analysis"],
            "secondary": ["organizational psychology", "power-mapping"],
        },
        "skills_needed": {"seeking": ["blockchain governance analysis experience"]},
        "interests": {"focus": ["capture resistance", "oligarchy detection"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Melati is OmniOne's governance health auditor.  She runs the periodic "
            "governance health audits and monitors capture-risk indicators.  Her background "
            "is in organizational psychology, and she has a gift for detecting power "
            "concentration before it becomes visible to the community.  She is the ecosystem's "
            "immune system."
        ),
        "backstory": (
            "Born in Jakarta.  MSc in Organizational Psychology from UI.  Worked at "
            "a governance consultancy that audited Indonesian SOEs (state-owned enterprises) "
            "for corruption.  Burned out after watching audit recommendations get ignored "
            "by politically connected boards.  Joined OmniOne because 'here, the audit "
            "triggers action, not a press conference.'"
        ),
    },
    {
        "id": _pid("putu"),
        "username": "putu",
        "display_name": "Putu Ardana",
        "member_id": "M-010",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["cultural preservation", "cross-generational bridge-building"],
            "secondary": ["ceremonial coordination", "oral history"],
        },
        "skills_needed": {"seeking": ["digital archiving skills"]},
        "interests": {"focus": ["cultural governance", "indigenous knowledge systems"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Putu is the Culture Code steward for the TH (Town Hall) ETHOS.  He ensures "
            "that OmniOne's governance does not erase Balinese cultural governance "
            "traditions — the banjar assembly system, the subak water cooperatives, "
            "and the desa adat (customary village) structures.  He is the bridge between "
            "NEOS and the living governance traditions of Bali."
        ),
        "backstory": (
            "Born in Tabanan, Bali.  Trained as a priest (pemangku) in his family's temple "
            "but chose community organizing over formal priesthood.  Served as kelian adat "
            "(customary village leader) for 6 years.  Joined OmniOne to ensure that imported "
            "governance systems don't colonize indigenous ones.  Speaks Balinese, Kawi "
            "(Old Javanese), Indonesian, and English."
        ),
    },
    {
        "id": _pid("ayu"),
        "username": "ayu",
        "display_name": "Ayu Pertiwi",
        "member_id": "M-011",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["inter-ETHOS coordination", "liaison facilitation"],
            "secondary": ["translation", "cross-cultural communication"],
        },
        "skills_needed": {"seeking": ["federation design expertise"]},
        "interests": {"focus": ["inter-unit coordination", "polycentric navigation"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Ayu is the inter-ETHOS liaison between the TH and AE units.  She facilitates "
            "cross-unit requests and ensures that neither ETHOS dominates the other.  "
            "She speaks four languages and navigates cultural boundaries with the ease "
            "of someone who grew up with a Javanese mother and a Balinese father."
        ),
        "backstory": (
            "Born in Malang, East Java, raised in Denpasar.  BA in International Relations "
            "from UGM.  Worked at ASEAN Secretariat in Jakarta for 3 years on "
            "cross-border cooperation.  Left because 'ASEAN coordinates states, I want "
            "to coordinate communities.'  Joined OmniOne in 2025."
        ),
    },
    {
        "id": _pid("budi"),
        "username": "budi",
        "display_name": "Budi Santoso",
        "member_id": "M-012",
        "current_status": "active",
        "profile": "townhall",
        "skills_offered": {
            "primary": ["organic farming", "seed-saving"],
            "secondary": ["farmers market coordination"],
        },
        "skills_needed": {"seeking": ["soil science", "water management"]},
        "interests": {"focus": ["food sovereignty", "seed commons"]},
        "onboarding_status": "complete",
        "kyc_status": "unverified",
        "notes": (
            "Budi is a smallholder farmer from the highlands of Kintamani.  He joined "
            "OmniOne through Gede's invitation and participates primarily in the TH ETHOS.  "
            "He is skeptical of complex governance systems and has a sharp instinct for "
            "when 'the process' is being used to exclude people like him.  Ground truth."
        ),
        "backstory": (
            "Born in Kintamani, Bali.  Third-generation coffee and vegetable farmer.  "
            "His family lost land in a development project due to a contract they couldn't "
            "read.  This experience fuels his insistence on accessible governance.  Joined "
            "OmniOne because the UAF was explained to him in Balinese, not just English."
        ),
    },
    {
        "id": _pid("rani"),
        "username": "rani",
        "display_name": "Rani Maheswari",
        "member_id": "M-013",
        "current_status": "prospective",
        "profile": "townhall",
        "skills_offered": {
            "primary": ["graphic design", "visual communication"],
            "secondary": ["social media", "storytelling"],
        },
        "skills_needed": {"seeking": ["governance literacy"]},
        "interests": {"focus": ["visualizing governance", "information design"]},
        "onboarding_status": "in_progress",
        "kyc_status": "pending",
        "notes": (
            "Rani is in onboarding.  She heard about OmniOne through a visual storytelling "
            "workshop and was drawn to the idea of designing governance processes so they're "
            "legible.  She is still in her cooling-off period and hasn't yet consented to "
            "the full UAF.  Her journey represents the onboarding pipeline."
        ),
        "backstory": (
            "Born in Bandung, West Java.  Freelance graphic designer for 6 years.  "
            "Designed information campaigns for environmental NGOs.  Moved to Bali in 2026.  "
            "Fascinated by how governance systems communicate — or fail to communicate — "
            "their own rules to participants."
        ),
    },
    {
        "id": _pid("ketut"),
        "username": "ketut",
        "display_name": "Ketut Arsana",
        "member_id": "M-014",
        "current_status": "active",
        "profile": "builder",
        "skills_offered": {
            "primary": ["data portability", "GDPR compliance", "information architecture"],
            "secondary": ["digital ethics", "privacy engineering"],
        },
        "skills_needed": {"seeking": ["decentralized identity (DID) expertise"]},
        "interests": {"focus": ["exit rights", "data sovereignty", "digital self-determination"]},
        "onboarding_status": "complete",
        "kyc_status": "verified",
        "notes": (
            "Ketut is OmniOne's exit coordinator and data portability steward.  A former "
            "data protection officer for a Singaporean tech company, he left after seeing "
            "how platforms weaponize data lock-in.  He designed OmniOne's portable record "
            "format and manages the exit process for departing members."
        ),
        "backstory": (
            "Born in Singaraja, Bali.  MSc in Information Security from NTU Singapore.  "
            "Worked as a DPO for 4 years.  Watched dozens of users try to export their data "
            "from a platform that made it technically possible but practically impossible.  "
            "Joined OmniOne with a mission: 'Exit must be as smooth as entry.'"
        ),
    },
]


# ── Convenience accessors ──────────────────────────────────────────

def get_persona(name: str) -> dict:
    """Return a persona dict by display-name substring match."""
    name_lower = name.lower()
    for p in PERSONAS:
        if name_lower in p["display_name"].lower():
            return p
    raise KeyError(f"No persona matching '{name}'")


def persona_id(name: str) -> uuid.UUID:
    """Return the deterministic UUID for a persona by name."""
    return get_persona(name)["id"]
