# AI transports

## Typed decisions

`decisions.py` calls OpenRouter's typed probability API at
`https://openrouter.ai/api/alpha/decisions`. It is separate from Gemini chat
generation in `provider.py`. The shared configured key remains server-side.

Requests contain only JSON state and named `noul`/`choice` questions. The
client validates a version-pinned non-Anthropic model, question shapes,
bounded request/response sizes, every expected answer type, candidate names,
finite probability ranges, and optional confidence/usage fields. Optional
probabilities must name exactly the submitted options. Choice is read from
the returned choice field, not recomputed from confidence.
The returned model must exactly match the requested pinned build so routing
never silently uses a model that has not passed calibration.

The fixed endpoint refuses redirects so credentials cannot follow another
host. Blocking standard-library I/O runs in a worker thread under a bounded
timeout; no extra runtime dependency is needed. Errors expose neither the
provider body nor authentication data. There are no implicit retries.

The coordinator lists the live decisions catalog and probes pinned builds
before setting `AI_DECISION_MODEL`. An empty value disables automatic
selection. `AI_DECISION_TIMEOUT_SECONDS` defaults to six seconds and is
limited to 0.25–15 seconds. Transport failure leaves the caller a safe
direct-answer fallback; it never changes tool permissions.

Contract source: <https://openrouter.ai/skills/openrouter-decisions> and its
`references/decisions-api.md`. Captured official references live in the
local ignored `.omc/research/` directory.
