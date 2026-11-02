# Prompt routing

`skill_decision.py` selects a workflow context for the current request. It
does not authorize writes, infer roles, evaluate lifecycle gates, or replace
the generation model. Authentication, caller-scoped tools and bound
confirmations remain authoritative.

The decision request asks an independent `noul` question about whether a
governance workflow is useful and a `choice` over every named registry
candidate. It also asks a direct-context choice: platform help/live-record
lookups, framework explanations, or general conversation. Presence below
the provisional 0.5 gate chooses direct context and does not consult the
skill choice. A single-candidate registry needs no forced one-option choice.

Candidate metadata consists of names, bounded descriptions and layers.
Request state contains the latest user message, at most four bounded
user/assistant history entries, a page section/view, and a previous skill
hint only when that skill remains in the registry. Raw tool messages,
member objects, cookies, search parameters, active-view payloads and skill
bodies are excluded. The latest request wins over a previous workflow or
classification instructions embedded in the user's text.

An explicit `requested_skill` is validated against the live registry and
bypasses classification. `active_skill` from an earlier turn is only a hint;
the caller must be able to clear it when the new request needs no skill.
Unknown manual names, empty state, unavailable classification, malformed
answers and timeouts all return general context with no stale skill.

`SkillDecision.as_event()` exposes mode, skill and source only. Raw routing
probabilities, provider model, costs and input state remain internal. The
coordinator can record metadata for non-secret calibration probes through
`build_decision_request` and `PROBE_CASES`.
Successful model routes log only the resolved pinned model, mode, skill,
presence probability and cost for calibration traceability. These records
exclude message, history, page, member and credential data. Invalid explicit
manual values retain their identity through the chat boundary and fall back
directly without spending a classification call.

The 0.5 presence gate is the documented provisional rule, not an assertion
of calibrated production accuracy. Live probes must cover clear workflows,
direct definitions/navigation, live record queries, topic changes,
ambiguity, off-topic text, negation and adversarial classification claims.
Choose and pin the model using those observed answers, latency and cost;
repeat calibration after model or question changes. Unit tests prove
validation and deterministic policy branches; they do not prove the model's
semantic judgments.
