# AdminApps AI Financial S2 Implementation Report

## A. Executive verdict

`ADMINAPPS_AI_FINANCIAL_S2_PASS`

S2 adds a deliberately non-operational producer-identity and financial-RBAC
foundation.  It creates no admission, reservation, settlement, financial HTTP
route, provider call, customer-data change, production credential operation, or
deployment capability.

## B. Human authorization reference

Execution is bounded by the owner's explicit 2026-10-08 authorization:
`ADMINAPPS_AI_FINANCIAL_S2_EXECUTION = AUTHORIZED`.  The reviewed governing
sources were:

- `/home/felipe/proyectos/isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md`
- `/home/felipe/proyectos/isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_AMENDMENT_01_DECISION_RECORD_2026-10-08.md`
- `/home/felipe/proyectos/isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_IMPLEMENTATION_READINESS_2026-10-08.md`
- `/home/felipe/proyectos/adminapps/docs/financial/ADMINAPPS_AI_FINANCIAL_S1_IMPLEMENTATION_REPORT_2026-10-08.md`

ISO Smart was read only.  S3 through S6, real OpenAI inference, deployment,
credential rotation, commit, merge, and push were not performed or enabled.

## C. Starting Git state and preserved S1 baseline

- Repository: `/home/felipe/proyectos/adminapps`
- Branch: `hardening/p0-p1-enterprise-readiness`
- Baseline HEAD: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`
- Initial unrelated/local work preserved: `backend/config/settings.py` modified;
  `backend/apps/financial/`, `backend/scripts/verify_financial_s1_postgres.sh`,
  and `docs/financial/` untracked.

S1's original model/migration foundation was retained.  Its PostgreSQL roles,
FORCE RLS, immutable evidence triggers, tenant policies, and no producer-table
grant remain in place.  The S2 migration only adds protected append-only tables
and an INSERT policy for immutable producer-registration creation.

## D. Producer identity and registered IntegrationAPIKey authentication

`ProducerRegistration` remains the immutable identity/binding record.  The new
`ProducerRegistrationLifecycleEvent` is the append-only source for its current
lifecycle state.  `apps.financial.services` creates a pending registration and
its initial event atomically; lifecycle changes append evidence, and revoked or
retired registrations cannot reactivate.

`apps.financial.authorization.authenticate_registered_producer` accepts only an
active, registered `hashed_v1` `IntegrationAPIKey` with a credential ID and a
matching fingerprint.  It fails closed for invalid, revoked, legacy,
unregistered, settings-only fallback, ambiguous, mismatched, disabled, or
revoked identities.  The generic IntegrationAPIKey verifier is never a
financial-authority fallback.

Exact `controlled_test`/`staging`/`production` environment, explicit product
UUID, and explicit allowed S2 operation are required.  The allowed operation
set is `admit_reserve`, `settle`, `status_read`, and `submit_evidence`; its
presence only authenticates the producer scope and does not implement any of
those future workflows.  The returned principal deliberately contains no
organization authority, so it cannot make a tenant admission decision.

There is no S2 HTTP endpoint and no transport header is consumed.  Consequently
no spoofed forwarded-transport header can authorize S2.  Any future HTTP adapter
must require `request.is_secure()` after direct TLS or a trusted ingress that
strips client-supplied forwarding headers before Django's
`SECURE_PROXY_SSL_HEADER` is configured; that deployment/infrastructure work is
outside S2.

## E. Financial RBAC and auditability

The `financial` permission family is explicitly separate from platform,
organization, staff, and producer roles:

- `financial_policy_admin`, `financial_budget_admin`,
  `financial_tariff_approve`, `financial_evidence_review`
- `financial_reconcile`, `financial_manual_resolution`,
  `financial_audit_read`, `financial_admin`

`apps.financial.rbac` requires a direct, explicit financial permission; it does
not use Django's superuser shortcut.  Only an explicitly assigned
`financial_admin` may grant or revoke another financial permission.  Each grant,
revocation, and denied privileged check creates a secret-free,
append-only `FinancialPermissionAuditEvent`.

## F. PostgreSQL and tenant/product isolation

Migration `0003_producer_identity_and_financial_rbac` protects
`financial_producer_registration_events` and
`financial_permission_audit_events` with ENABLE/FORCE RLS, public-grant
revocation, migration-role ownership, audit-only reads, runtime append-only
inserts, and the existing immutable-evidence trigger.  The reusable disposable
PostgreSQL harness confirms 12 financial tables are FORCE-RLS and migration-role
owned, tenant A/B/no-context isolation remains `1/1/0`, producer credentials
have zero direct financial-table grants, and direct lifecycle/audit mutation is
rejected.

## G. Validation evidence

```text
USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test apps.financial --verbosity 2
# 12 passed

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test apps.financial apps.integration --verbosity 1
# 46 passed, 1 skipped

bash scripts/verify_financial_s1_postgres.sh
# ADMINAPPS_FINANCIAL_S1_POSTGRES_VERIFICATION_PASS
# 12 FORCE-RLS financial tables; lifecycle/audit immutability verified

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py makemigrations --check --dry-run
# No changes detected

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py check
# System check identified no issues (0 silenced)

git diff --check
# passed
```

The disposable PostgreSQL cluster and synthetic roles/data are removed by the
harness exit trap.  The complete suite was started in this constrained session,
but its final exit summary was not captured before the execution transport
window closed; it is not counted as passing evidence in this report.

## H. Modified files and final boundaries

- `backend/apps/financial/models.py`
- `backend/apps/financial/authorization.py`
- `backend/apps/financial/rbac.py`
- `backend/apps/financial/services.py`
- `backend/apps/financial/migrations/0003_producer_identity_and_financial_rbac.py`
- `backend/apps/financial/tests.py`
- `backend/scripts/verify_financial_s1_postgres.sh`
- this report

No financial admission, budget reservation, settlement/recovery, reconciliation
workflow, or customer-facing endpoint exists.  S3 prerequisite: retain this
registration/RBAC boundary and separately authorize policy/tariff semantics,
atomic PostgreSQL admission, tenant entitlement verification, and concurrency
tests.  The recommended next governed batch is S3 only after its separate human
authorization.
