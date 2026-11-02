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


## Bounded generation retries

`provider.py` owns generation retries: at most three attempts, within the original caller timeout measured monotonically. Both each network await and each async sleep use the remaining deadline. Only explicit HTTP 429/503 rejection is retried. Retry-After seconds or HTTP-date is a minimum wait; if it cannot fit, return unavailable rather than shortening it. Missing valid headers use bounded exponential delays. Timeout, connection, authorization and payment errors do not cause blind replays. Cancellation propagates. A returned streaming iterator is never restarted after content or an iterator error.

Both per-request `num_retries=0` and `max_retries=0` disable the LiteLLM wrapper/OpenAI-client layers; no retry_policy is supplied. The pinned configured provider/model/key remain the same. The installed local LiteLLM 1.82.6 source was captured read-only in `.omc/research/litellm-1.82.6-retry-snippets.txt`, confirming the kwargs retry policy and max_retries forwarding. Upstream response headers come first from `exception.response.headers`; explicit exception.headers are defensive fallback only.

A sanitized `AICompletionUnavailable` carries status, retry delay and attempt count without provider bodies or credential hints. A 429 admission-control rejection is not evidence of exhausted funds; 402 is a separate status and is not retried by this policy. Chat emits only those safe fields and preserves completed usage/own record navigation if a later generation fails. The wrapper retries generation only, never an entire user turn or application tool dispatch.

Primary contracts: [OpenRouter errors](https://openrouter.ai/docs/api_reference/errors-and-debugging), [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits), [LiteLLM exception mapping](https://docs.litellm.ai/docs/exception_mapping), and installed/upstream `litellm/{utils.py,exceptions.py,llms/openai/openai.py}`. Official source captures live under `.omc/research/openrouter-retry-20261102/`. Tests: `test_provider.py`, `test_live_agent_hardening.py`; authored before the coordinated end sweep.
