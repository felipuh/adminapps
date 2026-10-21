# AdminApps AI Financial S3 — Final Validation Report

## A. Executive verdict

`ADMINAPPS_AI_FINANCIAL_S3_BLOCKED_BY_SECURITY_CONTRACT`

The reviewed `SECURITY DEFINER` boundary correctly prevents direct table access
by the restricted runtime role, but the required direct-SQL identity-abuse
test found a real cross-tenant admission path.  A session that can assume
`adminapps_financial_runtime` can invoke the function with a known active
registration ID and a different eligible tenant ID, producing a reservation
for that tenant.  This is incompatible with the requested S3 acceptance
criterion that direct database access cannot bypass tenant restrictions.

No remediation was applied: binding a PostgreSQL call to the producer's
hashed Django credential, a producer database identity, or a signed
database-verifiable capability requires a trust/privilege-model decision not
defined or approved for this S3 slice.  S4--S6 remain unimplemented.

## B. Starting Git state

- Branch: `hardening/p0-p1-enterprise-readiness`
- HEAD: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`
- Pre-existing changes: modified `backend/config/settings.py`; untracked
  financial app, PostgreSQL verifiers, and financial documentation.
- No reset, clean, commit, merge, push, ISO Smart change, endpoint activation,
  provider call, deployment, or credential rotation occurred.

## C--G. Privileged function, authentication boundary, and database controls

The disposable PostgreSQL run applied `financial.0001` through
`financial.0005`.  Its reviewed function is
`public.financial_admit_reserve(...)`:

- `SECURITY DEFINER`; owner `adminapps_financial_admission`, which is
  `NOLOGIN`, `NOINHERIT`, `NOSUPERUSER`, and `NOBYPASSRLS`, without ownership
  of a `financial_%` table or membership edge.
- Fixed `search_path=pg_catalog, public`; financial references are schema
  qualified; the function has no dynamic SQL.
- `PUBLIC EXECUTE` is revoked.  The only explicit non-owner executor is
  `adminapps_financial_runtime`.
- The runtime role has no direct decision read, budget update, audit insert,
  reservation insert, or immutable-evidence mutation path.  The budget guard
  permits counter changes only while the function owner is effective.  S1
  confirmed FORCE RLS on all 12 financial tables, immutable evidence, no
  producer table grants, and forged tenant-GUC denial for direct table reads.

Django authenticates the registered `hashed_v1` credential and validates the
tenant assertion before calling PostgreSQL.  PostgreSQL independently checks
registration lifecycle, registration environment/product/operation scope,
organization/product/entitlement state, effective policy, tariff, bounds,
budget, and idempotency.  It does **not** verify the hashed credential, bind
the function session to a producer, bind a registration to a tenant, or verify
a signed tenant assertion.  `registration_id`, `organization_id`, `product_id`,
and financially material inputs are accepted function parameters.

## H--I. Tenant/product matrix and concurrency

| Scenario | Result |
| --- | --- |
| Restricted runtime, permitted direct function invocation | `reserved`; function path works |
| Runtime direct budget update/audit insert/decision read | denied |
| Runtime, registered product outside producer scope | `denied`, `PRODUCER_INACTIVE` |
| Runtime with active registration and a separately eligible Tenant B | **`reserved` for Tenant B**; security failure |
| Cross-product shared global-budget race | one `reserved`, one `denied`; global exposure `20.0000000000` |
| Concurrent exact replay | one immutable decision/reservation; both replies replayed |
| Same-product race, independent-tenant race, product-only exhaustion, conflicting concurrent replay | not executed after identity blocker |

The cross-tenant exploit was reproduced by
`FinancialAdmissionPostgresRuntimeRoleTests.test_runtime_direct_call_can_forge_an_eligible_tenant_identity`
using a separate non-superuser evidence login, `SET ROLE
adminapps_financial_runtime`, a valid registration from Tenant A, and a
synthetic eligible Tenant B.  The function returned `reserved` and persisted a
Tenant-B reservation.  It is a passing *reproduction* test, not a passing
security control.

## J--N. Policy changes, faults, recovery, and atomicity

- Policy activation/deactivation/replacement, tariff change/expiry, period
  expiry, entitlement revocation/expiry, product disablement, producer
  revocation, and budget-scope modification races: **not executed**.
- Observed PostgreSQL `40001`, bounded retry, retry exhaustion, and `40P01`:
  **not executed**.  The source retries only `40001`; lock ordering is global
  then product then UUID, but that is static inspection rather than deadlock
  proof.
- Connection loss before commit, lost response after commit, uncertain commit,
  and authoritative reconciliation readback: **not executed**.  No production
  status endpoint was added.
- Positive admissions shown by the PostgreSQL race contain one decision, one
  reservation, scope counter updates, and an audit event in the transaction;
  exact replay had no extra effect.  This does not overcome the identity
  boundary failure.

## O--Q. Commands and exact outcomes

```text
bash backend/scripts/verify_financial_s3_postgres.sh
# 3 PostgreSQL tests passed: 2 control/concurrency checks and 1 cross-tenant
# exploit reproduction; migrations through 0005 applied.
# ADMINAPPS_FINANCIAL_S3_POSTGRES_EVIDENCE_COMPLETE_WITH_IDENTITY_BOUNDARY_BLOCKER

bash backend/scripts/verify_financial_s1_postgres.sh
# PASS; 12 FORCE-RLS financial tables and S1 negative checks verified.

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test apps.financial apps.integration --verbosity 1
# 52 run: 48 passed, 4 skipped.

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test --verbosity 0
# 219 run: 215 passed, 4 skipped.

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py makemigrations --check --dry-run
# No changes detected

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py check
# System check identified no issues (0 silenced)

git diff --check
# PASS
```

The PostgreSQL scripts used an isolated loopback-only cluster, synthetic
roles/data, a bounded test process, and an exit trap.  Both completed and
reported cleanup; no run-scoped cluster, database, socket directory, roles,
secrets, or process remains.

## R--V. Changes, final state, blockers, and S4 prerequisites

Changed in this validation:

- `backend/apps/financial/tests.py` — reproducible cross-tenant runtime-role
  exploit evidence.
- `backend/scripts/verify_financial_s3_postgres.sh` — result text now reports
  the identity-boundary blocker rather than a misleading PASS.
- This report.  No migration was created or changed.

Final Git status preserves the pre-existing modified/untracked S1--S3 work;
the additional files above are likewise uncommitted.  The immediate blocker is
an approved producer-to-database trust binding that prevents an untrusted
runtime SQL session from choosing another active registration/tenant pair.
Until that decision, the security matrix cannot pass and additional concurrency
coverage cannot turn S3 into PASS.

For a separately authorized later slice, define the authenticated status lookup
and its producer/tenant access control for ambiguous outcomes, then validate
that recovery path.  Do not use it to settle, release, or otherwise implement
S4 in advance.
