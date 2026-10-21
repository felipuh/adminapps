# AdminApps AI Financial S3 — Decision 02-A Execution Report

## Executive verdict

`ADMINAPPS_AI_FINANCIAL_S3_PARTIAL`

The reproduced cross-tenant direct SQL reservation is blocked in a disposable
PostgreSQL run: `adminapps_financial_runtime` has no execute privilege on the
privileged admission functions and produces no tenant-B decision, reservation,
audit event, or budget movement.  A separately authenticated executor identity
successfully reserves only through a valid Ed25519 capability and live grant.

The required production-like operating-system/process separation of issuer
private key, executor credentials, and authenticated IPC has not been
implemented or evidenced.  The complete mandatory race/fault matrix was also
not executed.  These facts prohibit `ADMINAPPS_AI_FINANCIAL_S3_PASS`.

## Human authority and starting state

The supplied 2026-10-09 authorization explicitly approved Decision 02-A and
S3 remediation, while forbidding S4–S6, production credentials, deployments,
provider calls and git mutation.  Starting branch was
`hardening/p0-p1-enterprise-readiness`, ahead by two commits, with pre-existing
uncommitted S1–S3 financial work.  No commit, merge, push, deployment,
credential rotation, provider request or ISO Smart modification was made.

## Implemented remediation

- `capabilities.py`: deterministic domain-separated Ed25519 capability format
  using `cryptography`; strict algorithm/key/version/audience/time/binding
  rejection.
- `issuer.py`: registered-producer and live grant validation before signing;
  no key persistence or settings-based signing key.
- `executor.py`: independently verifies the signed capability and recomputes
  material request hash before using an executor-only PostgreSQL connection.
- Migrations `0006` and `0007`: producer-to-tenant grants, immutable replay
  ledger, forced RLS/append-only evidence, executor role precondition, runtime
  function revocation and executor-only capability function.
- PostgreSQL boundary rechecks and locks the grant inside the admission
  transaction.  Capability/invocation ledger and existing immutable admission
  identity prevent duplicate financial exposure.

## Executed evidence

| Command | Outcome |
| --- | --- |
| `USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py makemigrations --check --dry-run` | PASS — no changes detected |
| `USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test apps.financial --verbosity 1` | PASS — 21 run, 17 passed, 4 PostgreSQL-only skipped |
| `bash backend/scripts/verify_financial_s3_postgres.sh` | PASS — 4/4 PostgreSQL tests, migrations through `0007`, temporary cluster/roles removed by exit trap |

The PostgreSQL tests cover cross-product global-budget contention and exact
replay, runtime direct invocation denial, no cross-tenant persistence after the
original exploit attempt, executor role ACLs, and a valid capability/grant
admission with modified material rejection.

## Not executed / remaining blockers

- No real isolated issuer/executor processes, OS identities, protected IPC or
  private-key/credential store exist in this environment.
- Grant/producers revocation racing an executor admission, policy/tariff and
  entitlement races, independent tenant contention, conflicting concurrent
  replay, observed `40001`/`40P01`, retry exhaustion, lost-response and
  ambiguous-commit reconciliation remain unexecuted.
- The full Django suite, migration/system checks after the final changes, and
  final diff check remain required before any future verdict.

S4 prerequisites remain unchanged: only after S3 is fully evidenced may a
separate authority consider settlement/recovery/evidence transitions.  None is
implemented here.
