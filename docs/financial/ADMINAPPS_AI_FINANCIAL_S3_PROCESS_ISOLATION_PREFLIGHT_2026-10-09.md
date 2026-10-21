# AdminApps AI Financial S3 — Process-Isolation Preflight

**Date:** 2026-10-09  
**Scope:** read-only preflight for the approved Decision 02-A, test-only process-isolation lab  
**Verdict:** `ADMINAPPS_S3_PROCESS_ISOLATION_BLOCKED_BY_ENVIRONMENT`

## Executive finding

The existing Rocky Linux VM satisfies the operating-system requirement, but it
does **not** satisfy the mandatory SELinux requirement: SELinux is currently
disabled.  The approved lab must keep SELinux enforcing and may not use
permissive or disabled SELinux as a shortcut.  Therefore no test identities,
keys, sockets, database resources, systemd units, or policy changes were
created.

Changing this state is an out-of-scope host security change: it requires
privileged host administration and, when SELinux was disabled at boot, a
controlled boot-configuration change and reboot.  It must be planned so that
the existing ISO Smart, MedSupplier, AdminApps, PostgreSQL, Nginx, and other
services are not affected.  This preflight does not attempt to enable SELinux,
authenticate with sudo, bypass authentication, or alter any host setting.

## Read-only inventory

| Check | Result |
| --- | --- |
| Operating system | Rocky Linux 9.8 (Blue Onyx), kernel `5.14.0-687.48.1.el9_8.x86_64` |
| Effective identity | `felipe`, UID/GID `1000/1000` |
| Existing lab identities | None: only `felipe` has a regular non-system UID; `s3runtime`, `s3issuer`, and `s3executor` do not exist |
| Sudo binary | Present at `/usr/bin/sudo`; non-interactive credential check was not authorized (`sudo -n -v` returned 1) |
| SELinux | `getenforce`: `Disabled`; `sestatus`: `SELinux status: disabled` |
| systemd binary | systemd 252 is installed, but this execution context cannot connect to its D-Bus manager (`Operation not permitted`) |
| PostgreSQL tools | `psql` and `postgres` are installed; no PostgreSQL listener or server process was visible in the preflight context |
| Relevant services/ports | No AdminApps, ISO Smart, MedSupplier, Nginx, Gunicorn, or PostgreSQL services/listeners were visible in the preflight context |
| System Python | Python 3.9.25; its global environment does not contain `cryptography` |
| Project Python | The AdminApps backend contains `.venv` and `.venv312`; the existing S3 source imports `cryptography` from its project environment |

No passwords, database connection strings, private keys, or production
credentials were read or recorded.

## Existing S3 implementation inventory

The repository already contains the Decision 02-A S3 implementation and its
disposable PostgreSQL evidence harness:

- `backend/apps/financial/capabilities.py` provides the domain-separated
  Ed25519 capability format.
- `backend/apps/financial/issuer.py` expects private signing material to be
  injected by an isolated issuer process; it does not persist a key itself.
- `backend/apps/financial/executor.py` verifies a capability and invokes only
  the executor-granted PostgreSQL admission function.
- `backend/scripts/verify_financial_s3_postgres.sh` creates a disposable local
  PostgreSQL cluster on a private Unix socket and removes it through an exit
  trap.

Those source-level and database controls do not prove the mandatory
operating-system process boundary.  In particular, the present environment
cannot truthfully evidence SELinux confinement, systemd security properties,
or access denial across distinct host identities.

## Required condition to resume

An administrator must first make the already-owned VM boot with SELinux
**enforcing**, using the owner’s normal interactive administrative procedure
and a maintenance window appropriate for the services on the VM.  After the
host is back in its normal service state, rerun this read-only preflight and
confirm all of the following before creating the bounded lab:

1. `getenforce` returns `Enforcing`.
2. A systemd manager is reachable from the authorized administration context.
3. Interactive sudo can create only the three test identities and their
   protected test-owned directories.
4. The disposable PostgreSQL socket, port, names, and service identities do
   not conflict with the existing host services.

Only then may the approved test-only issuer, runtime, and executor processes,
their narrow Unix-domain IPC boundary, and their evidence collection be
created.  The resulting validation must include all mandatory A–L isolation
tests and the preserved original-exploit regression; none was claimed or run
by this preflight.

## Preservation statement

This batch made no host configuration, service, account, SELinux, firewall,
database, dependency, credential, key, commit, merge, push, or deployment
changes.  It did not start or stop any service and did not execute the
disposable PostgreSQL harness.  This preflight report is the sole new
workspace evidence artifact.
