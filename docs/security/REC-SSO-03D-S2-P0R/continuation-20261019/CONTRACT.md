# P0R continuation — contract delta, 2026-10-19

This is a local code change. No settings, credentials, grants, migrations or deployments were activated.
The preceding [session/service contract](../CONTRACT.md) remains the baseline, with the following explicit amendments.

## Consumer HTTP rejection

Both actual `AdminAppsClient` implementations now classify every HTTP 4xx as rejection:
`allowed=false`, `authorization_denied=true`, and a generic authorization error. This includes 404,
which the central handlers use to hide missing or inactive tenants. A JSON object can retain descriptive
fields, but cannot override these negative authority fields. Non-object or malformed JSON becomes an
empty denial body. None of these responses may enter an existing local fallback.

HTTP server error bodies are discarded as authorization evidence. The clients return only
`{"error":"AdminApps request failed","code":"http_error"}`. A 500/502/503 body containing
`allowed=true`, `valid=true` or modules does not grant access. The existing explicit test/demo fallback
policy for transport/service failure is preserved; `IS_PRODUCTION=true` disables it, including an
explicit per-call fallback request. No fallback was added and no active configuration was changed.

The seven service operations, credential hash verification, grants by authenticated credential_id,
tenant/product allowlists and independence from SSOClient remain unchanged. Provisioning requirements
are exactly those in [the preceding contract](../CONTRACT.md#grants-de-servicio), with no real IDs/secrets.

## Subscription invoice payment

`POST /api/subscriptions/invoices/{id}/mark_paid/` retains its existing human platform/staff/model-permission
admission and response `{"status":"paid"}`. It now executes `MarkInvoicePaidSerializer`.
The only writable input is optional `payment_reference`, a non-null string of at most 255 characters;
empty is accepted and whitespace is preserved. Unknown fields and structured/boolean reference values
are rejected with 400 before a business effect. Numeric values follow DRF CharField normalization.

For an invoice in `pending` or `overdue`, the handler marks it paid, records paid_at and the reference,
and retains the existing activation of a `trial`/`past_due` subscription. This does not enable a new
commercial operation or change trial/pricing/ownership policy.

For an already `paid` invoice, omitting the reference or repeating the existing reference returns 200
without a save or subscription activation. A different reference returns 409 with
`payment_reference_conflict`. Draft/cancelled/refunded/unknown states return 400 with `invoice_state_denied`.
This is explicit state/payload tightening of the historical endpoint, not a claim that historical
invalid transitions remain supported. An already paid invoice cannot be used to restore authority
withdrawn after the payment.

Sequential idempotence is verified offline. No row lock, transaction, billing ledger, external payment
confirmation or outbox was added here. Concurrent payment writes and invoice/subscription atomicity
remain NOT_EVIDENCED; failure between the two existing saves remains a local transactional gap.
No new payment audit/event contract is claimed.

## Session scope remains explicit

The central action revokes only owned SSOSession records under the B fence. `revoke_sessions` only
deactivates UserSession registry records, preserving the JTI obtained from verified authentication.
It does not invalidate local access JWTs, refresh families or Django cookies. Logout remains optional
owned-refresh blacklisting. This continuation does not silently turn these endpoints into global logout.
A session-family binding, historical-token policy and universal access/refresh verification still need
an explicit implementation contract. Central PostgreSQL triggers, locks and durable effects remain unverified.
