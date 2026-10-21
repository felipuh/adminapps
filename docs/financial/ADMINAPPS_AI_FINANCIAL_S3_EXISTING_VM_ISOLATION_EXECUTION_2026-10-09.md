# AdminApps AI Financial S3 — Existing VM Isolation Execution

**Date:** 2026-10-09
**Scope:** bounded, read-only host preflight and safe Django regression on the existing Rocky Linux VM
**Verdict:** `ADMINAPPS_S3_PROCESS_ISOLATION_BLOCKED_BY_ENVIRONMENT`

## A. Executive verdict

The repository and branch matched the authorized scope. The live host is Rocky
Linux 9.8 with SELinux currently Enforcing, and the system systemd manager is
reachable. No host identities, directories, keys, credentials, sockets,
services, databases, or policies were created or changed.

The process-isolation acceptance criteria were not demonstrated. The real
AdminApps backend currently runs as `felipe` (UID/GID 1000), which is also the
MedSupplier backend identity and this execution's user. The proposed
`s3runtime`, `s3issuer`, and `s3executor` accounts do not exist. The financial
application has no UNIX-socket/SO_PEERCRED transport, and its running systemd
unit has no effective hardening among the requested controls. Creating test
identities and transient system services needs a securely authenticated
administrative terminal, which was unavailable to this execution.

The full Django test suite passed using its SQLite test database. Five tests
were skipped; PostgreSQL-specific concurrency and database-role coverage was
not exercised in that run. The existing PostgreSQL verifier was reviewed but
not run: its exit trap recursively deletes a dynamically generated temporary
path, contrary to this batch's cleanup restriction. Historical PostgreSQL
evidence is listed separately below and is not represented as newly executed.

Overall S3 remains `ADMINAPPS_AI_FINANCIAL_S3_PARTIAL`. This report does not
authorize S4–S6, production activity, or a change to Phase31.5.

## B. Repository and Git integrity

| Check | Result |
| --- | --- |
| Repository root | `/home/felipe/proyectos/adminapps` |
| Branch | `hardening/p0-p1-enterprise-readiness` |
| Starting HEAD | `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c` |
| Expected financial source, migrations, verifier and documentation paths | Present |
| Starting tracked change | `backend/config/settings.py` modified |
| Starting untracked work | Existing financial app, migrations `0001`–`0007`, PostgreSQL verifiers, and S1–S3 governance/evidence files; preserved |
| Staged changes | None reported |
| `git diff --check` | PASS |
| Final HEAD/branch | Unchanged |

This report is the only file added by this execution. No existing uncommitted
work was overwritten. No commit, merge, push, reset, checkout, stash, or clean
operation was performed.

## C. Host and execution preflight

| Check | Live observation |
| --- | --- |
| OS/kernel | Rocky Linux 9.8; `5.14.0-687.48.1.el9_8.x86_64` |
| Execution identity | `felipe`, UID/GID `1000/1000`, member of `wheel` |
| Sudo | `/usr/bin/sudo` exists. No sudo authentication or privileged command was attempted; privilege availability is therefore not claimed. |
| SELinux | Enabled; current mode and configured mode both `Enforcing` |
| systemd | Version 252; system manager reports `SystemState=running` |
| PostgreSQL | Service active as `postgres`; listener on loopback port 5432 and PostgreSQL Unix sockets were visible |
| Existing active services observed | `adminapps-backend.service`, `medsupplier-backend.service`, `nginx.service`, `postgresql.service`, and `smart3ai-landing.service` |
| S3 test identities | No `s3runtime`, `s3issuer`, or `s3executor` user or same-named group found |
| Candidate lab paths | `/var/lib/smart3ai-s3-lab` and `/run/smart3ai-s3-lab` absent |
| Existing S3 lab unit | No matching S3 lab or financial issuer/executor unit found |
| Candidate verifier TCP port | No listener on port 55440 |

No secret files, environment variables, credentials, or private keys were read
or recorded.

## D. SELinux requirement traceability

The approved source records were checked for an explicit SELinux mandate:

| Source | Traceability finding |
| --- | --- |
| Financial Authority Contract V1.1, especially §§1 and 10 | Specifies financial authority and separated database roles/RLS. No SELinux or SELinux mode requirement is stated. |
| Financial Authority Amendment 01 decision record | No SELinux requirement stated. |
| Financial Authority Security Amendment 02, §§6.1–6.3 and §10 | Requires an isolated issuer/key boundary and restricted executor identity/credential boundary. It does not require SELinux. |
| Security Decision 02-A | Specifies signed capabilities, live grants, executor database role and residual trust boundaries. It does not require SELinux. |
| S3 Process-Isolation Preflight, 2026-10-09 | Calls Enforcing mandatory for its proposed lab, but does not cite a clause in the approved contract or decision establishing that requirement. |

On the sources reviewed, SELinux Enforcing is not an explicit requirement of
the approved financial contract or Decision 02-A; the earlier preflight's
Enforcing gate is an environment/lab constraint rather than a traceable
contract clause. In any case the live host is now Enforcing, unlike the
Disabled state recorded in that earlier preflight. No SELinux command,
configuration, policy, boot setting, or label was changed.

## E. Linux identities and deployed process limitation

The live systemd properties report `User=felipe`, `Group=felipe` for both
`adminapps-backend.service` and `medsupplier-backend.service`. Their observed
Gunicorn processes also run as UID 1000. Therefore, creating a synthetic
`s3runtime` identity would not prove that the existing deployed AdminApps
runtime is separated from MedSupplier or from the login identity. No service
was modified to change this.

No test identities were created because the session could not safely perform
interactive sudo authentication. No non-root identity switching or simulated
UID test was substituted for real process isolation.

## F. Issuer key, executor credential and IPC

Source review confirmed:

- `backend/apps/financial/issuer.py` expects injected private signing material;
  it does not persist or provision a private key.
- `backend/apps/financial/executor.py` verifies a capability and uses an
  executor-only database configuration passed to the Python object.
- No `SO_PEERCRED`, `AF_UNIX`, `SOCK_STREAM`, or `socket.socket` transport was
  found in `backend/apps/financial`.

There is no running isolated issuer or executor process to test. No signing
key or synthetic executor credential was created. Actual key/credential
access-denial tests and authenticated IPC peer-identity tests are
`NOT_TESTED`. A caller-supplied identity was not used as a substitute for
kernel-authenticated peer identity.

## G. systemd hardening

The active `adminapps-backend.service` was inspected read-only. Its effective
properties include:

| Property | Effective value |
| --- | --- |
| `NoNewPrivileges` | `no` |
| `CapabilityBoundingSet` | Full/default capability set |
| `AmbientCapabilities` | Empty |
| `PrivateTmp` | `no` |
| `ProtectSystem`, `ProtectHome` | `no` |
| `PrivateDevices` | `no` |
| `ProtectKernelTunables`, `ProtectKernelModules`, `ProtectControlGroups` | `no` |
| `RestrictNamespaces` | `no` |
| `SystemCallFilter` | Unrestricted (`~`) |

These are observations of the existing service, not an authorization to
change it. No transient S3 unit was created, and no service was restarted.
Issuer/executor systemd hardening is `NOT_TESTED`; the existing AdminApps unit
does not currently demonstrate the requested hardening.

## H. PostgreSQL verifier safety and evidence

`backend/scripts/verify_financial_s3_postgres.sh` was inspected. It runs
`initdb` into a new `mktemp` directory, uses a private temporary Unix socket,
sets `listen_addresses=''`, creates synthetic roles in that isolated cluster,
and runs PostgreSQL-only Django tests against the disposable database. It does
not specify the active application database or connect to the existing
PostgreSQL service. Its cleanup trap uses:

```sh
rm -rf "$financial_s3_tmpdir"
```

Because this execution's cleanup rules prohibit recursive deletion against a
dynamically generated path, the script was not run. No existing database was
queried or modified. The PostgreSQL runtime/executor role matrix, FORCE RLS
and live database evidence are `NOT_TESTED` in this execution.

The separate 2026-10-09
[Decision 02-A execution report](./ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md)
records an earlier disposable-cluster run, including runtime direct-call
denial, valid Ed25519 capability admission, and verifier cleanup. That is
historical evidence, not a result of this batch.

## I. Original exploit regression and legitimate admission

The required regression
`test_runtime_direct_call_cannot_forge_an_eligible_tenant_identity` remains
present in `backend/apps/financial/tests.py`; it was not deleted, weakened, or
skipped in source. The full SQLite suite does not exercise PostgreSQL roles,
RLS or functions, so the PostgreSQL exploit regression and a valid
executor-role financial admission are `NOT_TESTED` in this execution.

Historical S3 database results remain as documented in the Decision 02-A
execution report. They are not combined with this run's test counts.

## J. Django regression and checks

The project-local Python 3.12 virtual environment was used. The settings
explicitly selected SQLite for test runs, so this suite did not use the live
PostgreSQL database. No production migration was applied.

| Command | Result |
| --- | --- |
| `USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py test --verbosity 1` | PASS — 222 tests run; 217 passed, 5 skipped; 0 failures/errors |
| `USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py check` | PASS — no issues |
| `USE_SQLITE_FOR_TESTS=true .venv312/bin/python manage.py makemigrations --check --dry-run` | PASS — no changes detected |
| `git diff --check` | PASS |

The PostgreSQL concurrency test class explicitly requires PostgreSQL row locks
and isolation; the runtime-role class explicitly requires PostgreSQL roles,
RLS and functions. Those controls were not validated by running against
SQLite.

## K. Ecosystem protection and cleanup

The AdminApps, MedSupplier, Nginx, PostgreSQL, and Smart3AI Landing services
were only inspected. None was stopped, restarted, reconfigured, or connected
to for this task. No users/groups, directories, units, databases, keys,
credentials, sockets, or processes were created. Django destroyed its
SQLite test database after the successful run. Cleanup is `PASS` because no
persistent test resource was provisioned.

## L. Classification

| Category | Status | Evidence |
| --- | --- | --- |
| A. Repository integrity | PASS | Correct root, branch and HEAD; existing work preserved. |
| B. Environment safety | PARTIAL | Read-only preflight passed; active shared services identified; no privileged provisioning. |
| C. Linux identity separation | BLOCKED | Test identities absent; existing AdminApps and MedSupplier services both use UID 1000. |
| D. Issuer private-key isolation | NOT_TESTED | No isolated issuer/key store or real cross-UID access test. |
| E. Executor credential isolation | NOT_TESTED | No isolated executor credential store or real cross-UID access test. |
| F. UNIX IPC peer authentication | BLOCKED | No IPC transport/SO_PEERCRED implementation in the financial app. |
| G. systemd service hardening | BLOCKED | No test units; existing AdminApps unit lacks the inspected hardening. |
| H. PostgreSQL least privilege | NOT_TESTED | No database verifier run in this batch. |
| I. Original exploit regression | NOT_TESTED | Preserved but skipped for PostgreSQL-specific requirements in SQLite run. |
| J. Legitimate financial admission | NOT_TESTED | PostgreSQL executor path not run in this batch. |
| K. Applicable SELinux requirement | PASS | No SELinux mandate found in approved contract/Decision 02-A; live mode is Enforcing. |
| L. Cleanup | PASS | No host or persistent test resources created; SQLite test DB removed by Django. |

## M. Changed files and final Git state

Only this evidence report was added by this execution. The tracked settings
change and pre-existing untracked S1–S3 work remain untouched. Branch and HEAD
remain `hardening/p0-p1-enterprise-readiness` and
`42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`, respectively. No Git history
operation was performed.

## N. Remaining requirements and next bounded execution

Process-isolation closure still requires real, separately effective Linux
identities; private-key and executor-credential access-denial tests; a
reviewed authenticated local IPC boundary with kernel peer credentials and
bounded operations; transient test-only systemd hardening; and rerunning the
PostgreSQL role matrix and preserved exploit regression against disposable
PostgreSQL. The full S3 concurrency/fault matrix remains separately pending.

The next execution should begin from a secure, interactively authenticated
administrator terminal, recheck that the three account and group names and lab
paths are still absent, and provision only test-owned resources after an IPC
entrypoint and cleanup procedure are reviewed. If account creation is
authorized and those checks still pass, the bounded account-only operation is:

```sh
sudo useradd --system --user-group --no-create-home --shell /sbin/nologin s3runtime
sudo useradd --system --user-group --no-create-home --shell /sbin/nologin s3issuer
sudo useradd --system --user-group --no-create-home --shell /sbin/nologin s3executor
```

Expected result: three non-login system accounts with private same-named
primary groups and no home directories. Do not run these commands until the
names are freshly rechecked; do not grant sudo or privileged supplementary
groups. This execution did not run them.

## O. Follow-on Linux identity and secret-isolation batch

**Attempt time:** 2026-10-09 15:03 MDT
**Result:** `ADMINAPPS_S3_LINUX_ISOLATION_BLOCKED`

The follow-on batch revalidated the exact repository root, branch and HEAD:
`/home/felipe/proyectos/adminapps`,
`hardening/p0-p1-enterprise-readiness`, and
`42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`. The pre-existing modified
`backend/config/settings.py` and untracked S1–S3 work remained present.

The required `sudo -n true` probe failed with exit code 1 and
`sudo: a password is required`. No password was requested or handled in chat.
Interactive `sudo -v` could not be obtained in this execution, so no privileged
operation was attempted.

Fresh resource checks found all three proposed test users and same-named
groups absent, and both `/var/lib/smart3ai-s3-lab` and
`/run/smart3ai-s3-lab` absent. Existing AdminApps, MedSupplier, Nginx,
PostgreSQL, and Smart3AI Landing services were running; PostgreSQL listened
on loopback port 5432. No matching S3 lab unit or listener on port 55440 was
found. SELinux was observed as `Enforcing`; this differs from the user's
stated baseline of Disabled and from the historical preflight snapshot, and
was not changed.

No accounts, directories, keys, credential fixtures, sockets, processes,
services, or database objects were created. Linux UID/DAC tests, secret access
tests, IPC, and PostgreSQL tests therefore remain `NOT_TESTED`; no cleanup
was required. This later check supersedes earlier host-state snapshots only
for the values it directly re-observed.

To resume the blocked privileged stage, execute `sudo -v` interactively in
the same terminal that will run the authorized commands, then rerun the
resource checks before any account or directory creation. Do not send the
password through chat.

## P. Authenticated-sudo resume attempt

**Attempt time:** 2026-10-09 15:16 MDT
**Result:** `ADMINAPPS_S3_PROCESS_ISOLATION_BLOCKED`

The repository root, branch and HEAD again matched the authorized scope.
`tty` returned `not a tty`; effective identity was `felipe` UID/GID 1000.
`sudo -n true` again failed with exit code 1 (`sudo: a password is required`).
An interactive `sudo -v` could not be completed in this non-interactive
execution. No password was requested, received, or handled.

The host reported `localhost.localdomain`, SELinux `Enforcing`, and current
and configured SELinux modes both `Enforcing`. The prior host snapshots did
not record a hostname or boot identifier, so continuity of host/boot
environment cannot be established from the available evidence. The current
observation does not establish when or why the earlier report observed
`Disabled`; no SELinux setting was changed.

The three lab users/groups and both named lab paths remained absent. The
previously observed protected services and PostgreSQL listener remained
active. No resources were provisioned and no UID/DAC, secret, IPC, or
PostgreSQL tests were run. All remain `NOT_TESTED`.

Required manual action to resume: run `sudo -v` interactively in the same
terminal session in which the owner intends the bounded privileged commands
to execute. Then rerun this batch's repository, identity, SELinux, account,
path, service, and port checks before any creation. No account-creation
command was run or queued by this attempt.
