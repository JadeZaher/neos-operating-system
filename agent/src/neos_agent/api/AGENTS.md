# API architecture

## OAuth return origins

The production backend serves more than one frontend origin. OAuth initiation therefore carries the initiating frontend through the provider round trip in signed `state`, instead of relying on one global redirect URL.

Only origins listed in `CORS_ORIGINS` or `FRONTEND_URL` may be encoded or accepted. The signed state must also match the short-lived, HttpOnly transaction cookie set for the initiating browser; callbacks consume that cookie and reject missing or mismatched state before token exchange.

Keep the provider callback itself on `OAUTH_REDIRECT_BASE`; changing the consumer origin must not require additional provider callback registrations or permit an open redirect.
