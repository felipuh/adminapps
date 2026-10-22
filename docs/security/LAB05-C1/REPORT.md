# LAB05-C1 — Cross-product HTTP prerequisite checkpoint

2026-10-22. **LAB05_C1_BLOCKED_PREREQUISITES**. This checkpoint records an
incomplete objective, not consumer E2E acceptance. LAB05-C2 was not started.

## A. Executive verdict

Eight actual loopback HTTP requests reproduce an unavailable SSO surface in the
existing LAB05 runtime profiles. Separately, static inspection demonstrates that
ISO Smart's current authentication privilege migration depends on financial
migrations prohibited by this task. No application policy or route was changed
to bypass either prerequisite. No production readiness claim.

## B. LAB05-C1 — ISO Smart

Baseline AdminApps HEAD and remote upstream both verified as
`e4f72061adf42eee97b0e2000a2e1a68a0d12550`. Local branch
`security/rec-git-sec-01-workspace-20261021`, upstream
`origin/security/rec-git-sec-01-20261021`. All three repositories initially clean.
ISO Smart HEAD `61bf5a27ac49f66cc8b57f083c752e8fe397d108`, branch/upstream
`checkpoint/rec-git-03-isosmart-20261020` / matching origin branch.

Reproduce from AdminApps root using the existing SEC-02 Python environment and
PostgreSQL binaries on PATH:

```sh
/tmp/adminapps-sec02-20261022/.venv-sec02/bin/python backend/lab04/run.py --http-sso-preflight
python backend/lab05/consumer_schema_preflight.py /home/felipe/proyectos/isosmart
```

The new opt-in mode reuses LAB04 provisioning/fixtures and the unchanged LAB05
WSGI processes, without running the LAB04 or LAB05-A/B acceptance suites.
Successful script exit means the blocker was reproduced, **not C1 PASS**.

| HTTP scenario | Observed result |
|---|---|
| Legitimate human IAM login `/api/auth/login/` | 200; access/refresh returned, held only in memory |
| IAM and CP `/api/integration/sso/login/` | 404 in both processes |
| IAM and CP `/api/integration/sso/introspect/` | 404 in both processes |
| IAM and CP `/api/integration/sso/logout/` | 404 in both processes |
| Human IAM logout `/api/auth/logout/` | 200 |

These integration paths already exist in `apps/integration/urls.py`, but
`config/urls_iam.py` and `config/urls_control_plane.py` do not mount them.
ISO's `integration/central_auth.py` calls `/sso/login/`, `/sso/introspect/` and
`/sso/logout/` relative to its configured integration base URL. It requires a
CENTRAL RS256 proof plus live introspection; the human IAM token is a separate
contract and was not substituted. The existing isolated lab uses HS256 for that
human token. Routing reproduction does not exercise SSO credential validation:
the supplied technical header is deliberately unregistered and receives 404
before the integration handler exists in this URL surface.

[HTTP evidence](http-result.json) records all request statuses, elapsed times and
actual PostgreSQL identities/PIDs. Each request used a fresh runtime connection.
Observed single-request latency: human login 496.159 ms, logout 84.248 ms;
missing-route requests 37.924–137.647 ms. These are unaggregated prerequisite
measurements, not consumer or revocation latency, throughput or service SLOs.

[Schema evidence](schema-preflight.json) records a static AST dependency witness
with source hashes at the unchanged ISO HEAD:
`authentication.0011_application_auth_runtime_privileges` → `core.0019` →
the core migration chain → `core.0012_billingpayment_evidence_fields` →
`core.0011_billing_models`. The latter creates `billing_subscriptions` and
`billing_payments`. Authentication 0011 also depends on foundation 0037. The
script follows literal core predecessors only; it is not a complete Django
migration planner and does not execute consumer code or migrations.

The consumer was **not started**. Valid SSO JWT issuance, issuer/audience/expiry,
product/tenant binding, insufficient grants/scopes, forged-header rejection,
central revocation followed by JWT reuse, zero protected-handler execution after
denial, and authority-outage behavior are all **NOT_EXECUTED** for ISO Smart.
The CP handler counter in the evidence is not consumer-handler evidence.
No functional defects corrected; changes are reproducible diagnostic harnesses
and this checkpoint. No mocks are counted as HTTP coverage.

## C. LAB05-C2 — MedSupplier

**NOT_STARTED** because C1 remains blocked. Baseline HEAD
`5bfcddc94e0ad5b8f0fe3e7449ba83b66ebc2bca`, branch/upstream
`checkpoint/rec-git-03-medsupplier-20261020` / matching origin branch.
No consumer changes, tests, cross-product isolation claim, commit or push.
Decisions B and D remain unchanged.

## D. Security invariants

Fresh disposable PostgreSQL cluster, TCP disabled, private Unix socket, separate
IAM/CP runtime SQL principals and ephemeral generated runtime credentials.
HTTP bound exclusively to ephemeral loopback ports. Synthetic user fixture
passwords are pre-existing LAB04 fixtures; no production credentials were used.
No shared database, external integrations, email, workers, deployments or
financial migrations. No operational settings, business rules or consumer
history changed. HTTP evidence omits bodies, tokens, cookies and passwords.

[HTTP cleanup](http-cleanup.json) confirms both workers terminated and waited;
[runtime cleanup](cleanup.json) confirms deletion after PostgreSQL stopped.
Private logs remain outside Git; runtime key/database files were removed.

PRODUCTION_READY = FALSE

PHASE31_5 = EXECUTION_HELD

S3_DECISION_02A_NOT_CLOSED

Historical credential exposure still requires rotation by its owners.

## E. Remaining blockers

1. Existing IAM/CP process routes do not expose the consumer's SSO contract.
   A follow-up needs narrowly scoped SSO routing, explicit ephemeral RSA trust
   and durable synthetic client/tenant registrations, with runtime ACL checks.
   This is a local integration gap, not an external-service outage.
2. The current consumer migration chain conflicts with the explicit prohibition
   on financial migrations. A reviewed non-financial consumer schema/provisioning
   path is needed before authentic consumer HTTP acceptance can proceed. This
   checkpoint does not claim such a path is impossible; it was not constructed
   by faking migration state, replacing models or activating held capabilities.
3. All consumer E2E acceptance and therefore C2 remain outstanding. The task is
   stopped at this scope dependency instead of starting a broader schema change.

## F. Git publication

Only AdminApps receives this diagnostic checkpoint on the existing sanitized
lineage. Publish after index and full reachable-history secret audits and
`git diff --check`, using normal commit/push and remote SHA equality verification.
The resulting SHA and audit counts are reported in the execution response,
avoiding a self-referential commit hash. Neither consumer is modified or pushed.
