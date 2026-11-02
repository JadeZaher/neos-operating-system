# Fixture scope and entry requirements

The shared onboarding world includes a real configured entry quiz. Consent-only
regressions explicitly select `agreement_only`, which removes that entry
configuration before requests while retaining the learning content and member
assignment. Entry-quiz queue and onboarding-authority tests keep the configured
world. Do not seed passing results or weaken product gates to satisfy an
agreement-only expectation.

Journey placement tests use actual non-AI steps so requested progress indices
are in range. A different ecosystem's member row remains the assertion under
test; an empty journey is not proof of valid progress.

UAF-link validation tests first prove the general settings authorization refusal,
then give the synthetic caller actual domain stewardship before testing valid
and foreign agreement references. An ecosystem moderator label alone does not
satisfy the existing domain-steward settings policy.
