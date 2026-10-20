# AdminApps AI Financial S3 — Transactional Security Evidence

## A. Executive verdict

`ADMINAPPS_AI_FINANCIAL_S3_PARTIAL`

The restricted-role `SECURITY DEFINER` boundary has new real PostgreSQL evidence. S3 cannot be marked PASS because the required policy/entitlement race matrix, observed `40001`/`40P01`, and ambiguous-commit reconciliation matrix have not been demonstrated. The source-defined reconciliation status lookup is also absent; it must not be added as an unauthorized S4 operation.

## B. Starting Git state

The AdminApps branch was `hardening/p0-p1-enterprise-readiness` at the existing S3 worktree. `backend/config/settings.py`, the financial app, financial scripts, and financial documentation were already uncommitted. ISO Smart was not inspected for modification and was not changed.

## C-D. SECURITY DEFINER audit and runtime effective privileges

`apps.financial.tests.FinancialAdmissionPostgresRuntimeRoleTests.test_runtime_role_can_only_use_the_reviewed_admission_function` passed against a disposable PostgreSQL 18.6 cluster.

- Function: `public.financial_admit_reserve(...)`, `prosecdef=true`, owner `adminapps_financial_admission`.
- Owner and runtime flags: `NOSUPERUSER`, `NOBYPASSRLS`, `NOLOGIN`, `NOINHERIT`; the owner has no role membership edge.
- Function configuration: `search_path=pg_catalog, public`; financial object references are schema-qualified and the implementation contains no dynamic SQL or caller-controlled schema selection.
- ACL inspection found EXECUTE only for the owner and `adminapps_financial_runtime`; no PUBLIC or other explicit execute grantee.
- The runtime role owns no `financial_%` table. The test denied direct budget update, audit insertion, and admission-decision read. S1 separately proved FORCE RLS, no-context/forged-tenant-GUC denial, immutable audit protection, and the absence of producer-table grants.
- The verifier connected as the disposable, non-superuser `adminapps_financial_runtime_evidence` login, then activated the NOINHERIT runtime role. Observed identities were `current_user=adminapps_financial_runtime` and `session_user=adminapps_financial_runtime_evidence`.

The evidence login is created only inside the disposable verifier and removed with its cluster. It is not a production principal or a new application authority.

## E-F. Django-to-PostgreSQL boundary and forged parameters

Django's existing `hashed_v1` integration-key verifier authenticates the producer before the function call and the service rejects a missing tenant assertion with `TENANT_ASSERTION_UNTRUSTED`. The database independently rechecks registration lifecycle, registration product/operation scope, organization/product/entitlement, policy, tariff, bounds, budgets, and the immutable invocation identity.

| Test | Actual result | Invariant |
| --- | --- | --- |
| Restricted session, valid authoritative identifiers | `reserved` | Function can write only through its reviewed boundary. |
| Restricted session, existing product outside registration scope | `denied`, `PRODUCER_INACTIVE`, no reservation | PostgreSQL independently rejects the product-scope mismatch. |
| Direct budget update/audit insert/decision select | privilege errors | Runtime has no direct financial mutation/read path. |

The valid direct invocation also confirms the documented trust dependency: PostgreSQL does not validate the Django password hash and does not bind the function call cryptographically to an API key. An untrusted party that already obtained a database session able to activate the runtime role and knows a valid registration ID could invoke the function. This does not bypass the approved application trust boundary, but it prevents a claim that PostgreSQL itself authenticates producers. No duplicate credential mechanism was added.

## G-I. Concurrent tenant, budget, policy, entitlement, and revocation state

`FinancialAdmissionPostgresConcurrencyTests.test_cross_product_global_budget_and_duplicate_replay_are_atomic` passed using two independent PostgreSQL backends. Two 20.00 requests for different products sharing a 30.00 tenant-global budget produced one `reserved` and one `denied`, one reservation, and exactly 20.0000000000 global reserved exposure. Concurrent identical replay returned the same decision and created no second reservation. Observed backend PIDs were `13003` and `13004`.

This is evidence only for the cross-product shared-global-budget case and concurrent exact replay. Same-product contention, separate-tenant contention, policy change, entitlement change, producer revocation, tariff transition, period rollover, product disablement, and tenant-identity mismatch races are `NOT_EXECUTED`. V1.1 defines serializable admission and live rechecks but does not supply an explicit concurrent policy/revocation linearization rule beyond the transaction snapshot; no rule was invented.

## J. Observed serialization and deadlock behavior

`40001`: `NOT_EXECUTED`; retry handling exists but an observed serialization conflict, retry count, original-identity reuse, and exhaustion fail-closed behavior are not evidenced.

`40P01`: `NOT_EXECUTED`; no deadlock was induced and no deadlock retry policy was added. The canonical lock order in the function is global scope then product scope, followed by immutable UUID, but this is implementation review, not observed deadlock coverage.

## K. Ambiguous commit evidence

All connection-loss/commit-ack-loss scenarios are `NOT_EXECUTED`. There is no production endpoint and no source-defined internal status lookup to recover a committed decision by immutable identity. The V1.1 protocol requires this lookup before dispatch after an unknown outcome. It is an S4 prerequisite and was not implemented.

## L. Idempotency and financial consistency

Observed PostgreSQL concurrent replay: one logical reservation and one original decision. Observed conflicting replay and full ambiguous-outcome reconciliation are not part of the new PostgreSQL run. The SQLite focused suite continues to cover identical/conflicting replay, decimal amount calculation, scope counters, denials without reservations, and failed bounds/quota admissions.

## M-O. Exact test and check results

| Command | Result |
| --- | --- |
| `bash backend/scripts/verify_financial_s3_postgres.sh` | PASS; 2 PostgreSQL tests, 1.403s |
| `bash backend/scripts/verify_financial_s1_postgres.sh` | PASS; FORCE RLS and immutable/RBAC negative checks |
| `USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test apps.financial apps.integration --verbosity 1` | PASS; 51 tests, 3 skipped |
| `USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py makemigrations --check --dry-run` | PASS; no changes detected |
| `USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py check` | PASS; no issues |
| `git diff --check` | PASS |
| Full Django suite | `NOT_EXECUTED`; no production behavior was changed |

The three SQLite skips are PostgreSQL-only classes: concurrency and restricted-role tests are covered by the two executed PostgreSQL tests; no equivalent coverage exists yet for the unexecuted conflict/failure matrix.

## P. Cleanup evidence

Both PostgreSQL verifier scripts use an exit trap to stop the isolated cluster and remove its temporary socket directory, data directory, database, roles, and evidence login. Both completed successfully. No persistent database, role, volume, credential, process, endpoint, provider call, or deployment was created.

## Q. Modified files and final Git status

New evidence-only changes in this continuation:

- `backend/apps/financial/tests.py`
- `backend/scripts/verify_financial_s3_postgres.sh`
- this report

All other uncommitted S1/S2/S3 files remain preserved. No commit, merge, or push was performed.

## R-S. Remaining blockers and S4 prerequisites

PASS is blocked by the unexecuted G2-G4 scenarios above and by the missing identity status/reconciliation lookup after an ambiguous admission outcome. Before a separately authorized S4, define and implement only the contract's identity lookup/recovery behavior plus its access controls; do not release or settle unresolved exposure. No S4 behavior was implemented in this work.

