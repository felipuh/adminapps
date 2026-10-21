# LAB04 — opt-in SQL process boundaries

No deployment or active settings change. `PRODUCTION_READY = FALSE`.

The existing configuration has one `default` PostgreSQL connection populated by
DB environment variables. No service-specific principal is configured there;
we did not inspect operational credentials or connect to that database.

Alternative A is implemented as a shared reviewed schema with separate processes,
credentials and URL surfaces. Each process calls `config.runtime_profiles.configure`
before Django setup, with exactly one PostgreSQL connection. A middleware rejects
identity drift, owner/global privileges, memberships, DDL and authority deletion
privileges before dispatch. No connection router or request-controlled SET ROLE
exists. The laboratory launches independent Python processes authenticated directly
as each role. Maintenance is NOLOGIN and reachable only through the disposable
cluster administrator, never through an application role.

Alternative B (dedicated IAM database/service) would require replacing cross-model
FKs, transactional user/tenant revocation, Decision B triggers and outbox operations
with a new distributed contract. That migration and deployment are not implemented.
Alternative A preserves those single-database transactions without granting DDL,
role inheritance or privileged functions. The event process is read-only; delivery,
retention and external workers remain held.

## Permission matrix

| Principal/process | Required capabilities | Forbidden |
|---|---|---|
| IAM | LAB02 S/I/U users, MFA, memberships, human/SSO sessions; append audit/outbox; S authority context; U fence generation/epoch; cookie session CRUD | Business writes, Admin HTTP, terminal DELETE/TRUNCATE, DDL, role assumption |
| Control plane | IAM lifecycle needed by human authentication and user management; explicit tenant/catalog grants added per verified slice | Admin HTTP, technical integration, migrations, protected deletion, permission M2M writes |
| Django Admin | IAM lifecycle, reviewed human administrative tables and append admin log per verified slice | API HTTP, historical deletion, unreviewed permission changes, governance-held mutations |
| Events | SELECT tenant and SSO outboxes | HTTP endpoints, mutation, delivery, purge, authentication data |
| Maintenance | Owner DDL/migrations; no application credential | Not an application authority; outside attacker model |

The installer resets table AND column ACLs, sequences, routines, defaults and
PUBLIC privileges, then grants only enumerated capabilities. It rejects runtime
memberships, ownership, global flags, definer routines, unknown schemas, unreviewed
financial tables and disabled retention triggers. Only INSERT-backed sequences get
USAGE. Source: [PostgreSQL GRANT](https://www.postgresql.org/docs/current/sql-grant.html).

This increment supports the reviewed non-financial schema. It deliberately cannot
be installed unchanged in the operational full monolith. An operational topology,
reverse proxy routing, credential delivery and financial-schema review remain
external activation dependencies. Shared code is not an OS sandbox: operators must
not provide sibling credentials to a process. Compromise of a runtime may alter
data within its explicit write permissions; the guarantee is durable rejection of
the original revoked credential, not immunity to all arbitrary SQL compromise.

## Reproduction

`backend/.venv312/bin/python backend/lab04/run.py --stage A`

Requires local PostgreSQL executables and Django/psycopg2 dependencies. The runner
creates a new private Unix-socket cluster, rejects root, disables TCP, configures
synthetic SCRAM logins and excludes financial migrations. Settings are constructed
without importing operational settings or dotenv; Python outbound networking is
denied. Raw failure logs stay in a private temporary directory. Only explicitly
reviewed JSON results belong in published evidence. Cleanup verifies its own
cluster identity and removes only the created runtime (including secrets/JWTs).

The copied LAB01/LAB03 harness retains historical assertions; only the selected
17-method successor in `functional.py` is acceptance for this run. Unselected old
methods and prior failures are not reclassified. Fresh lab acceptance additionally
checks exact-token rejection after DELETE/reinsert, reconnect and cluster restart.
