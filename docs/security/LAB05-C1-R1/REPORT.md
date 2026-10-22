# LAB05-C1-R1 — Central SSO HTTP runtime

2026-10-22. Scope: AdminApps disposable laboratory only.

## A. Executive verdict

**LAB05_C1_R1_CENTRAL_SSO_HTTP_PASS**. Existing central issuance, live
introspection, rotation, OTP verification and durable logout exercised over real
loopback HTTP and disposable PostgreSQL: 49 HTTP requests and 6 actual SQL
rejections passed. No authentication/persistence mocks.
Neither ISO Smart nor MedSupplier was started; no consumer E2E claim.

## B. Root cause and fix

Baseline local/upstream SHA: `21961bdb86034a99127111c0e836415e694b5dd3`;
clean branch `security/rec-git-sec-01-workspace-20261021`, upstream
`origin/security/rec-git-sec-01-20261021`, fetch confirmed zero divergence.
IAM/CP URLConfs deliberately do not mount integration. Add an explicit lab-only
`lab05.sso_urls` with exactly login, login/verify-2fa, introspect, logout and
rotate under `/api/integration/sso/`. Existing handlers, registry, trust codec,
session lifecycle, operational URLConfs and SQL migrations are unchanged.

Reproduce with PostgreSQL binaries on PATH:

```sh
/tmp/adminapps-sec02-20261022/.venv-sec02/bin/python backend/lab04/run.py --http-central-sso
```

The opt-in flag reuses LAB04 provisioning and fixtures, runs only this acceptance
suite, and destroys its runtime. It does not run LAB04 or LAB05-A/B acceptance.

## C. SSO runtime / SQL principal

Three separate loopback WSGI workers: IAM, CP and SSO. The latter authenticates
as `lab04_sso` directly, with no membership or SET ROLE. Its settings reuse the
IAM boundary verifier as an ACL ceiling, then explicitly replace only the lab
URLConf and load ephemeral CENTRAL trust. It is not a production runtime profile.

Maintenance provisions the reviewed IAM ceiling for the new role and removes
human-session, cookie, invitation, permission and business-write capabilities.
Users are read-only except login/activity timestamps and failed-login counters;
memberships, tenant/client registries, credentials, products, plans and existing
subscription relations are read-only. SSO session/fence/outbox and MFA state
retain the existing lifecycle grants. All sequence permissions are removed.
Table grants are recorded in `http-result.json`; user column grants are explicit
in `sso_seed.py`. IAM and CP receive no new privileges.

Provisioning checks role attributes, ownership, memberships, namespace privileges
and eight retention triggers. Every HTTP request verifies its actual SQL identity
and uses a new backend connection. Runtime binds only loopback; PostgreSQL has
TCP disabled and a private Unix socket. Synthetic ISO_SMART entitlement uses the
existing non-billing fixture; no financial migration or shared DB is touched.

## D. HTTP acceptance matrix

See [request-level evidence](http-result.json), including SQL identities/PIDs and
protected-stage counters. HTTP 200 with `active:false` is a denial in the existing
introspection contract, not successful authentication.

| Scenario | Observed acceptance |
|---|---|
| Registered client login / live introspection | 200; CENTRAL access token; active authorization with exact catalog scope |
| Unregistered credential row / wrong client / request audience / product | 401; no tokens or protected-stage execution |
| Foreign tenant login | 403 |
| Forged client/product/tenant/role headers without credential | 401 |
| Wrong signed token audience / issuer / product / expiry | 200, inactive |
| Wrong signed tenant | 401 |
| Wrong RSA signature / HS256 / unknown key ID | 200, inactive |
| Missing 2FA payload | 400; route exists |
| Actual OTP challenge / verification / introspection | 200; `amr` is pwd + otp |
| Replay OTP challenge after verification | 403, invalid_or_expired_challenge |
| Rotation / new token introspection | 200; old generation rejected with 401 |
| Logout | 200, revoked |
| Revoked token introspection and rotation after reconnection | 401 |
| Revoked token after rejected SQL mutations | 401 |
| All five SSO paths on IAM and CP | 404 |
| Integration health/organizations/analytics/demo/AI, products, billing, human login, admin on SSO | 404 |

Denied requests leave token-rendering and live-authorization counters unchanged.
These are central protected-stage observations, not consumer-handler evidence.
The initial core suite passed; adding OTP replay exposed an incorrect test
expectation of 401, corrected to the existing 403 consumed-challenge rejection.
No production behavior was changed to satisfy the test.

## E. CENTRAL RS256 trust verification

Fresh 2048-bit RSA keypair per run; public key verification checks algorithm,
issuer, audience, key ID, family, client, tenant and ISO_SMART product binding.
Registered client passes `full_clean()` and uses a hashed_v1 credential row.
Synthetic issuer `https://central.lab.example.invalid`, client `lab05-iso-smart`,
audience `urn:lab05:iso-smart`, key ID `lab05-c1-r1`; these are lab registrations,
not assumed production consumer configuration. Scope `ISO_SMART:core.document:read`
is taken from the existing authorization catalog, not an invented grant.
Human HS256 tokens are not used for CENTRAL authentication. Private keys,
passwords, OTP secrets, raw credentials and JWT bodies are excluded from evidence.

## F. Revocation invariants

SQL confirms the original session remains revoked with reason logout and exactly
one logout outbox record. DELETE, TRUNCATE, resurrection, client-registry writes,
product writes and superuser escalation are rejected by actual SQL ACL/triggers.
Distinct PostgreSQL backend PIDs establish fresh connections for each SSO request.
Existing monotonic and retention triggers are preserved; no definer function,
revoked-row deletion/reinsertion or runtime administrative grants are introduced.
This is reconnection durability, not an additional PostgreSQL restart test.

[HTTP cleanup](http-cleanup.json) confirms three workers stopped;
[SQL cleanup](cleanup.json) confirms the owned runtime was removed after shutdown.

## G. Remaining blockers

No blocker remains for this central laboratory objective. ISO Smart's previously
recorded schema dependency remains: authentication.0011 → core.0019 → core.0012
→ core.0011 billing tables. Consumer schema/provisioning, consumer protected
handlers and cross-product E2E remain unexecuted. Operational activation and
production credentials are outside this checkpoint.

## H. Commit / push / remote SHA

Publish on the existing sanitized lineage with normal commit and push after
index and reachable-history secret audits and diff review. The execution response
reports the resulting SHA and remote equality, avoiding a self-referential hash.

## I. Final Git status

Execution response records post-push status. Only AdminApps lab harness and this
evidence/report are included; consumers and operational modules remain unchanged.

## J. Precise next step for ISO Smart

Prepare and review a non-financial isolated consumer schema/provisioning path
without faking migration state. Then, in a separately authorized consumer test,
configure its CENTRAL trust and registry contract against this central runtime
and exercise real consumer login, introspection, denial and revocation handlers.
Do not begin LAB05-C2 until the required C1 acceptance is complete.

PRODUCTION_READY = FALSE

PHASE31_5 = EXECUTION_HELD

S3_DECISION_02A_NOT_CLOSED

NO_DEPLOYMENT

NO_SHARED_DB_MUTATION
