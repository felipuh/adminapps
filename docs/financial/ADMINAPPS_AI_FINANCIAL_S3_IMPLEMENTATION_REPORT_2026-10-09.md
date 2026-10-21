# AdminApps AI Financial S3 Implementation Report

## A. Executive verdict

`ADMINAPPS_AI_FINANCIAL_S3_PARTIAL`

S3 implements a non-HTTP, synthetic-only admission/reservation service and
proves its core global-budget and replay invariant with a disposable PostgreSQL
race. It does not authorize S4--S6, provider dispatch, real OpenAI inference,
production financial admission, deployment, credential rotation, commit, merge,
or push.

The verdict is deliberately not PASS: the disposable race runs as the local
cluster administrator, while the deployed `adminapps_financial_runtime` role
does not yet have a reviewed narrow stored-procedure/service boundary for the
reservation insert and budget-counter update. That runtime-role proof is a
mandatory acceptance gap, not an assumption.

## B--E. Authorization, traceability, and preserved baseline

The owner authorization supplied on 2026-10-09 explicitly authorized S3 only.
The implementation followed the V1.1 contract, Amendment 01, implementation
readiness record, and the S1/S2 reports. ISO Smart was not modified.

Starting AdminApps state:

- branch: `hardening/p0-p1-enterprise-readiness`
- HEAD: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`
- pre-existing local work: `backend/config/settings.py` modified; the financial
  app, S1 verifier, and financial documentation were untracked.

S1/S2 tables, FORCE RLS, immutable evidence, dedicated roles, producer
registration, lifecycle evidence, and financial RBAC remain in place.

## F--P. S3 admission behavior implemented

`apps.financial.services.admit_and_reserve` is an internal function only; no
URL, view, provider client, or dispatch path was added. It:

1. authenticates the S2 registered `hashed_v1` producer credential for exact
   environment/product/`admit_reserve` scope, then locks and rechecks the
   registration and credential;
2. requires a tenant assertion whose canonical AdminApps tenant UUID matches
   the authoritative organization; locks organization, product, and live
   organization-product entitlement;
3. selects exactly one current approved policy and verified effective tariff,
   rejects missing/ambiguous tariff or policy, model mismatch, FX/currency
   mismatch, invalid/absent input bound, and output-bound excess;
4. uses `Decimal`, policy precision, and the approved rounding rule for the
   worst-case synthetic amount;
5. starts PostgreSQL transactions at `SERIALIZABLE`, locks global then product
   budget rows sorted by immutable UUID, retries only SQLSTATE `40001` and only
   with the original immutable identity; and
6. writes the immutable admission decision, reservation, all-scope counters,
   and immutable audit record before commit. Failures persist an immutable
   denial after identity is known; no reservation is created.

Migration `financial.0004_s3_admission_controls` adds explicit input/output
bounds, request quota counters, non-negative accounting checks, and a
PostgreSQL trigger that rejects direct budget-counter mutation outside the S3
admission transaction.

The admission identity remains
`(producer_registration, organization, product, invocation_id)`. The server
hashes canonical financially material input; identical replay returns the
original decision, while changed material rejects `IDEMPOTENCY_CONFLICT` with
no additional reservation.

## Q--V. Validation evidence

Completed commands and exact results:

```text
USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test apps.financial --verbosity 1
# 16 passed, 1 skipped (PostgreSQL-only race)

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test apps.financial apps.integration --verbosity 1
# 50 passed, 2 skipped

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test --verbosity 0
# 217 passed, 2 skipped

bash scripts/verify_financial_s1_postgres.sh
# ADMINAPPS_FINANCIAL_S1_POSTGRES_VERIFICATION_PASS
# FORCE RLS, tenant A/B/no-context isolation, immutable evidence, and no
# producer table grants verified.

bash scripts/verify_financial_s3_postgres.sh
# ADMINAPPS_FINANCIAL_S3_POSTGRES_CONCURRENCY_PASS
# 1 PostgreSQL test passed using two independent backend connections.

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py makemigrations --check --dry-run
# No changes detected

USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py check
# System check identified no issues (0 silenced)

git diff --check
# passed
```

The S3 PostgreSQL test uses two synthetic products sharing a tenant-global
budget of 30.00. Two simultaneous 20.00 admissions produced exactly one
`reserved` and one `denied`, leaving exactly 20.00 reserved. The test records
two distinct PostgreSQL backend PIDs. Simultaneous replays of the committed
identity returned the same immutable decision without another reservation.
The cluster, roles, test database, temporary secrets, and socket directory are
removed by the verifier exit trap.

## W--Z. Files, final state, limitations, and next governed work

S3 changes:

- `backend/apps/financial/models.py`
- `backend/apps/financial/services.py`
- `backend/apps/financial/migrations/0004_s3_admission_controls.py`
- `backend/apps/financial/tests.py`
- `backend/scripts/verify_financial_s3_postgres.sh`
- `backend/config/settings.py` (explicit PostgreSQL-test opt-in)
- this report

No commit, merge, push, deployment, endpoint activation, ISO Smart change, or
provider request occurred.

Before a future S3 PASS/operational successor, complete the remaining
multi-tenant, connection-loss/ambiguous-commit, stale-policy, and runtime-role
matrix cases. S4 remains separately governed and is not authorized by this
work.

## S3 continuation — runtime-role closure evidence

### Root cause and selected boundary

The prior S3 service used direct ORM inserts and counter updates.  Its
PostgreSQL race therefore exercised the local administrator rather than the
restricted `adminapps_financial_runtime` role.

Migration `financial.0005_s3_runtime_admission_boundary` creates a reviewed,
fixed-`search_path` `SECURITY DEFINER` function,
`public.financial_admit_reserve`.  It is owned by a new dedicated
`adminapps_financial_admission` role which is `NOLOGIN`, `NOINHERIT`,
`NOSUPERUSER`, and `NOBYPASSRLS`; it is not the owner of any financial table.
The function rechecks active producer lifecycle/scope, authoritative
organization/product/entitlement state, policy, tariff, bounds, canonical
global-then-product locks, quota/budget availability, immutable idempotency,
and then writes the decision, reservation, counters, and audit row in the
caller transaction.  An advisory transaction lock makes a concurrent exact
identity call a replay rather than a uniqueness race.

The runtime role has only `EXECUTE` on that function plus the central S2
hashed-credential/registration reads needed before invocation.  It has no
direct access to tenant decisions, reservations, budgets, tariffs, policies,
or audit evidence, and no direct financial insert/update/delete grant.  The
budget trigger now checks the non-login function owner rather than a
caller-controlled session setting.  No `PUBLIC` function grant was added.

### Actual evidence

- `bash backend/scripts/verify_financial_s3_postgres.sh`: 2 PostgreSQL tests
  passed.  The first used independent backend connections for the
  cross-product global-budget race and concurrent exact replay; one 20.00
  reservation and one denial resulted from the 30.00 shared global budget.
  The second ran the application service with `current_user` set to the real
  restricted runtime role: `rolsuper=false`, `rolbypassrls=false`, no
  financial-table ownership, successful permitted admission, and direct
  counter update, audit insertion, and decision read denials.
- `bash backend/scripts/verify_financial_s1_postgres.sh`: passed.  All 12
  financial tables remain FORCE RLS and migration-role owned; runtime direct
  decision reads (including a forged tenant GUC), direct mutations, immutable
  audit/lifecycle mutations, and producer direct access were rejected.
- Focused Django suite (`apps.financial apps.integration`): 51 passed, 3
  skipped (PostgreSQL-only classes on SQLite).
- Full Django suite: 218 passed, 3 skipped.
- Migration drift check, Django system check, and `git diff --check`: passed.

The disposable verifier exit traps removed its temporary PostgreSQL cluster,
database, socket directory, roles, and test data.  No endpoint, provider call,
settlement/recovery operation, deployment, commit, merge, or push occurred.

### Remaining S3 acceptance gaps

This remains `ADMINAPPS_AI_FINANCIAL_S3_PARTIAL`, not PASS.  Evidence is still
absent for the complete requested matrix: same-product race, two independent
tenant concurrent admission, product-only exhaustion, conflicting concurrent
replay under PostgreSQL, policy/entitlement/producer-revocation changes during
admission, observed `40001` retry exhaustion, observed `40P01`, and
deterministic connection-loss/ambiguous-commit reconciliation.  The contract
does not define a policy/entitlement change ordering beyond the transaction
snapshot, so no new ordering rule was invented.  S4 remains out of scope.

The S2 hashed-key check remains in the Django service immediately before the
function call.  PostgreSQL cannot independently verify the existing Django
password-hash format, so a database client already holding the runtime
connection credential could invoke the function with an active registration
UUID.  This is not a session-variable authorization bypass, but it is not a
cryptographic producer-to-function binding either.  Closing that residual
database-client threat would require a contract-approved producer-bound
database identity or a database-verifiable signed/capability assertion; neither
is defined by V1.1.  No such authority model was introduced in this batch.
