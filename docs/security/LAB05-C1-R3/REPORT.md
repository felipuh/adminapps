# LAB05-C1-R3 — real ISO Smart HTTP integration

2026-10-28. **LAB05_C1_R3_ISOSMART_HTTP_E2E_PASS**.

R3 adds an opt-in `--http-isosmart <backend-path>` entry to the existing disposable
runner. It reuses R1 provisioning, starts the actual central SSO runtime and runs
ISO's integrated orchestrator. It does not repeat R1/R2 acceptance or start IAM,
control-plane, workers or MedSupplier HTTP processes. Operational settings,
migrations and business handlers remain unchanged.

`lab05/r3_seed.py` registers both synthetic tenants, assigns one subject writer
access in A and viewer access in B, and exports only the CENTRAL public keyring.
`r3_control.py` creates negative proofs using private RSA solely inside AdminApps
and changes synthetic entitlement scopes as maintenance to exercise live
revocation. The HTTP server gains opt-in sanitized request observation and a
fixed-loopback-port restart option. No successful authentication uses a fabricated
proof, mocked client or in-memory persistence.

ISO's actual login, live introspection, ORM projection, cookies, `/api/auth/me/`
and ResourceViewSet run against a separate disposable PostgreSQL cluster. Two ISO
instances use fixed unprivileged SQL principals and forced RLS. Central tenant
authority is checked against an owner-maintained SQL mapping before handlers run.
The first functional defect was ISO's nonexistent `UserProfile.is_primary` lookup;
its separate commit binds `/me/` to the validated session profile instead.

Real central logout rejects reuse of exactly the same ISO cookie/proof, across SQL
reconnections and a central server restart. Central state is revoked with one
logout outbox event. Rejected ISO calls execute no protected handler and change no
consumer table. Central outage and a matching local password both fail closed.
Scope removal revokes existing sessions; restoration does not revive them.

Evidence is in `evidence.json`, `HTTP_MATRIX.md`, `cleanup.json`, and
`consumer-cleanup.json` beside this report. The full A–K report and reproduction
instructions are in ISO Smart's `docs/transformation/LAB05_C1_R3.md` and
`backend/lab05_c1_r3/README.md` on the matching sanitized R3 branch.

```sh
/tmp/adminapps-sec02-20261022/.venv-sec02/bin/python backend/lab04/run.py \
  --http-isosmart /home/felipe/proyectos/isosmart-lab05-c1-r2/backend
```

The existing local R1 Python environment was reused without dependency updates.
AdminApps baseline/upstream is `5190c9b0830fa1f85b8a9ac576e9df3d60383a21`;
ISO baseline/upstream is `1b9a50f92eb4c0c4b0658c0d2dc60225ec63c602`.
Each repository publishes a separate commit on
`lab05/c1-r3-http-sso-sanitized-20261028`; final remote SHA equality and clean
upstream status are recorded in the delivery message after push. No force push or
history merge is used. Complete reachable history and staged-object secret scans
must pass before publication.

No R3 laboratory blocker remains. This is not production readiness: TLS,
production settings/schema, deployment and OS isolation remain outside scope.
The existing generic 503 for a foreign cookie with an RLS-hidden local profile is
recorded explicitly; it fails closed without writes. All cluster data and keys
are removed; retained evidence contains no credentials or raw proofs.

`PRODUCTION_READY = FALSE` · `PHASE31_5 = EXECUTION_HELD` ·
`S3_DECISION_02A_NOT_CLOSED` · `NO_DEPLOYMENT` · `NO_SHARED_DB_MUTATION`.
