# AdminApps AI Financial S3 — Host-Lab Administrative Gate

**Date:** 2026-10-09
**Scope:** pre-root correction and review of the Decision 02-A test-only process/secret-isolation lab
**Host-lab verdict:** `S3_HOST_LAB_READY_FOR_HUMAN_ROOT_EXECUTION`
**Financial S3 verdict:** `ADMINAPPS_AI_FINANCIAL_S3_BLOCKED_BY_SECURITY_CONTRACT`

## 1. Adjudication and boundary

This correction authorizes neither host setup nor financial implementation. No privileged setup command, account/group creation, service restart, PostgreSQL connection, shared-database operation, SELinux change, Git commit, merge, or push was performed. The repository script is review input and is rejected if executed as root. The sole next action is owner execution of the protected, checksum-matched copy in section 6.

The script validates Linux DAC and transient-systemd identity/restriction properties only. It creates no IPC endpoint and opens no database connection; it reports IPC and PostgreSQL validation as **not implemented**, never passing. It does not alter S1/S2/S3, Phase 31.5, the S3 security amendment, or production-admission governance.

## 2. Corrected artifact and nonprivileged evidence

Reviewed source: `/home/felipe/proyectos/adminapps/backend/scripts/s3_isolation_host_lab.sh`

Corrected SHA-256: `4588e38a8b49f32502854c2da2cc085656a6be7600f06a9ee40788792006c9c5`

| Check | Result |
| --- | --- |
| `bash -n backend/scripts/s3_isolation_host_lab.sh` | Passed. |
| Invocation with no operation | Printed usage and exited `64`; no changes. |
| Repository-copy `preflight` | Exited `1` with “must run as root from the reviewed copy”; intended protected-copy rejection. |
| Repository-copy `cleanup` | Exited `1` with the same protected-copy rejection; no cleanup action occurred. |
| Positive and denial helper fixtures | Positive read and real DAC denial both passed (`0`). |
| Failed executor fixture | Stubbed `runuser` exit `127` failed both allowed and denied checks; no false PASS. |
| Missing-file fixture | Failed closed before invocation; no false PASS. |
| Cleanup recovery fixtures | Manifest-only, complete no-mutation-plan, and recorded-created-directory states each reached `CLEANUP_COMPLETE`. Individually simulated directory, IPC-group, user, supplementary-membership, issuer-key, and executor-fixture operations with only `planned` evidence all stopped `1` with `manual adjudication required`. |
| Manifest integrity fixture | An unauthorized manifest entry was rejected before cleanup. |
| Interrupted-setup handler, isolated function harness | Emitted the root-journal recovery location and exited `7`; no setup action was invoked. |
| Documented staging transaction | Extracted command passed `bash -n`; it is one `set -euo pipefail` root transaction with source/destination symlink, ownership/mode, and SHA gates. |
| `git diff --check -- backend/scripts/s3_isolation_host_lab.sh` | Passed. |
| ShellCheck | Not installed; no substitute is represented as ShellCheck. |
| Static side-effect review | No PostgreSQL client/connection, database command, package-manager, SELinux-mode/policy, or shared-service restart command exists. |
| Host SELinux check | `getenforce` returned `Enforcing`; `sestatus` reported enabled/enforcing targeted policy. |
| Current Codex process context | `unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023`. |

Actual lab file labels and transient-process labels cannot be inspected until owner-approved setup/validation creates them. The corrected script captures them with `ls -Zd` and `ps -o label=` during that run. It does not claim that the current unconfined process label or Enforcing status supplies a dedicated lab SELinux domain.

## 3. Remediations applied

| Finding | Corrected control |
| --- | --- |
| Lab root `0700` blocked intended account traversal. | Both roots are root-owned `0711`: known-child traversal only, no listing. Secret directories remain owner-only `0700`; the root-only manifest is outside the traversal trees. IPC-placeholder directories are non-listable `0710`. |
| `expect_denied` accepted any nonzero exit. | Denial tests require an existing regular non-symlink file, existing identity, installed `runuser`/`head`, a DAC calculation proving no read bit, and a real `Permission denied`/`Operation not permitted` read failure. Owner reads are positive controls. Missing files/users/binaries, execution failures, and unexpected SELinux AVCs fail. |
| Interrupted setup could leave weak evidence. | A root-only, fsynced journal records the complete planned inventory before its first lab mutation. A resource is removable only after its own `created` record exists. `ERR`, `HUP`, `INT`, and `TERM` stop setup and name the recovery journal. A present `planned`-only resource is never promoted or guessed: cleanup stops for manual adjudication. |
| Cleanup deleted its manifest too early. | The external root-owned journal remains until all created lab files, directories, memberships, users, primary groups, and IPC group are safely removed or proven absent. Each completed removal is journaled, making recorded-state cleanup resumable. |
| Preflight collisions were informational. | `preflight` emits each collision and exits nonzero with `PREFLIGHT_BLOCKED_BY_RESOURCE_COLLISION`; `setup` repeats the blocking check. |
| systemd probe could exit before inspection. | Probe runs `/usr/bin/sleep 25`, then must be `ActiveState=active`, have a live `MainPID`, match the requested effective UID in `/proc/<pid>/status`, expose requested properties, and report its live process context. |
| Earlier gate said SELinux Disabled. | Current host observation is Enforcing. Script reports status, `sestatus`, file labels, and live process labels; it does not alter SELinux. |
| Root could execute a mutable checkout. | Every operation requires exact `/root/adminapps-s3-isolation-host-lab-2026-10-09.sh`, root:root `0700`, in root:root `0700` `/root`, with no symlink. The root:root `0600` one-line sidecar is path-bound and strict-SHA verified. Staging rejects all existing/dangling artifact symlinks and revalidates source and staged bytes before preflight. |

## 4. Exact privileged resource inventory

Setup refuses if any named account, primary group, IPC group, path, or manifest already exists.

| Type | Exact resource | Metadata/effect |
| --- | --- | --- |
| Protected artifact | `/root/adminapps-s3-isolation-host-lab-2026-10-09.sh` | Root-owned `0700`; copied only after checksum review. Remove manually after successful lab cleanup. |
| Checksum sidecar | `/root/adminapps-s3-isolation-host-lab-2026-10-09.sha256` | Root-owned `0600`, one absolute-path SHA-256 entry. Remove manually after successful lab cleanup. |
| Recovery journal | `/root/adminapps-s3-isolation-host-lab-2026-10-09.run-manifest.tsv` | Root-owned `0600`, fsynced plan/create/remove evidence. Created by setup and deleted only as cleanup’s final operation. |
| System group | `s3labipc` | New system group only. |
| System users/groups | `s3runtime`, `s3issuer`, `s3executor` | New system user and primary group each; no home creation, home `/nonexistent`, shell `/sbin/nologin`. Each is supplementary `s3labipc`; no sudo membership or service unit. |
| Lab roots | `/var/lib/smart3ai-s3-lab`, `/run/smart3ai-s3-lab` | `root:root`, `0711`; permits known-name traversal but no listing. |
| Private directories | `/var/lib/smart3ai-s3-lab/issuer`, `/var/lib/smart3ai-s3-lab/executor` | Respectively `s3issuer:s3issuer` and `s3executor:s3executor`, `0700`. |
| IPC placeholders | `/run/smart3ai-s3-lab/issuer`, `/run/smart3ai-s3-lab/executor` | Respectively issuer/executor owner, group `s3labipc`, `0710`. No socket is created. |
| Issuer key | `/var/lib/smart3ai-s3-lab/issuer/issuer-ed25519.pem` | Disposable locally generated Ed25519 private key, `s3issuer:s3issuer`, `0600`. |
| Executor fixture | `/var/lib/smart3ai-s3-lab/executor/postgres-credential.fixture` | Fixed non-credential test text, `s3executor:s3executor`, `0600`; no connection string, secret, or database command. |
| Transient probes | `adminapps-s3-lab-<script-pid>-s3issuer` and `...-s3executor` | Short-lived `systemd-run` units only; no existing unit is started, stopped, restarted, or modified. |

The manifest is outside `LAB_ROOT`: otherwise it must be deleted before the parent can be removed. This retains the root-owned journal through every lab-resource removal while lab accounts cannot access it.

## 5. Scope exclusions

The approved validation performs two positive owner-read controls, four cross-identity DAC denial controls, metadata checks, SELinux status/file/live-process context reporting, and two live systemd probes with `User`, `Group`, `NoNewPrivileges=yes`, empty `CapabilityBoundingSet`, `PrivateTmp=yes`, `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateDevices=yes`, `RestrictNamespaces=yes`, and `SystemCallFilter=@system-service`.

It deliberately leaves the following **NOT_TESTED**: authenticated Unix IPC or
`SO_PEERCRED`; FAI/signing/HSM isolation, grants, or replay; real PostgreSQL
executor credentials, PostgreSQL roles/RLS/migrations/shared database, and the
cross-tenant regression; a distinct SELinux lab domain; deployed AdminApps
process isolation; and full S3 concurrency. No unavailable validation is a
pass.

## 6. Explicit human root-approval command

Only after reviewing the exact checksum and confirming all inventory names are
unused, run this from the AdminApps repository root in an interactive terminal.
The single `sudo` transaction uses `set -euo pipefail`: a failed staging,
preflight, setup, or validation prerequisite prevents every later stage.

```bash
expected_sha='4588e38a8b49f32502854c2da2cc085656a6be7600f06a9ee40788792006c9c5'
source_script="$PWD/backend/scripts/s3_isolation_host_lab.sh"
reviewed_script='/root/adminapps-s3-isolation-host-lab-2026-10-09.sh'
reviewed_sum='/root/adminapps-s3-isolation-host-lab-2026-10-09.sha256'
reviewed_manifest='/root/adminapps-s3-isolation-host-lab-2026-10-09.run-manifest.tsv'

sudo -v
sudo /usr/bin/env bash -euo pipefail -c '
  expected_sha="$1"
  source_script="$2"
  reviewed_script="$3"
  reviewed_sum="$4"
  reviewed_manifest="$5"

  [ "$(readlink -f -- /root)" = "/root" ] || exit 1
  [ "$(stat -c "%U:%G:%a" /root)" = "root:root:700" ] || exit 1
  [ -f "$source_script" ] || exit 1
  [ ! -L "$source_script" ] || exit 1
  [ "$(readlink -f -- "$source_script")" = "$source_script" ] || exit 1
  [ "$(sha256sum "$source_script" | awk "{print \$1}")" = "$expected_sha" ] || exit 1
  for artifact in "$reviewed_script" "$reviewed_sum" "$reviewed_manifest"; do
    if [ -e "$artifact" ] || [ -L "$artifact" ]; then exit 1; fi
  done

  install -T -o root -g root -m 0700 "$source_script" "$reviewed_script"
  [ -f "$reviewed_script" ] || exit 1
  [ ! -L "$reviewed_script" ] || exit 1
  [ "$(stat -c "%U:%G:%a" "$reviewed_script")" = "root:root:700" ] || exit 1
  [ "$(sha256sum "$reviewed_script" | awk "{print \$1}")" = "$expected_sha" ] || exit 1
  printf "%s  %s\n" "$expected_sha" "$reviewed_script" > "$reviewed_sum"
  chown root:root "$reviewed_sum"
  chmod 0600 "$reviewed_sum"
  [ -f "$reviewed_sum" ] || exit 1
  [ ! -L "$reviewed_sum" ] || exit 1
  [ "$(stat -c "%U:%G:%a" "$reviewed_sum")" = "root:root:600" ] || exit 1
  sha256sum --strict -c "$reviewed_sum"

  "$reviewed_script" preflight
  "$reviewed_script" setup
  "$reviewed_script" validate
' bash "$expected_sha" "$source_script" "$reviewed_script" "$reviewed_sum" "$reviewed_manifest"
```

The script independently repeats reviewed-path, ownership/mode, sidecar,
checksum, and collision checks. Return complete non-sensitive output before
further assessment. A collision or validation failure is blocking; do not
rename, overwrite, or manually alter resources to force a pass.

## 7. Exact cleanup command

After evidence capture, use only the same protected copy:

```bash
sudo /root/adminapps-s3-isolation-host-lab-2026-10-09.sh cleanup && \
  sudo rm -- /root/adminapps-s3-isolation-host-lab-2026-10-09.sh /root/adminapps-s3-isolation-host-lab-2026-10-09.sha256
```

If setup or cleanup is interrupted, do not remove the manifest or remaining
object manually. Re-run cleanup only when every remaining resource has
`created` evidence. If a present resource has only `planned` evidence, cleanup
will safely stop for manual adjudication and retain the journal. Remove reviewed
artifacts only after `CLEANUP_COMPLETE` confirms the manifest was last.

## 8. Remaining risks and stop condition

This is DAC/systemd evidence only. SELinux is Enforcing but no dedicated lab domain/policy is reviewed. Executor/issuer processes, real IPC authentication, PostgreSQL boundary enforcement, and S3 concurrency/rollback evidence remain absent. Root/DBA compromise and ordinary host trust remain outside this test.

Stop at this human approval gate. This document does not authorize setup,
production financial admission, deployment, credential rotation, migrations,
provider calls, commits, merges, or pushes. The governing state remains:

```text
ADMINAPPS_AI_FINANCIAL_S3 = PARTIAL
S4_TO_S6 = NOT_AUTHORIZED
REAL_OPENAI_INFERENCE = NOT_AUTHORIZED
DEPLOYMENT = NOT_AUTHORIZED
GIT_COMMIT_PUSH_MERGE = NOT_AUTHORIZED
PHASE31_5 = EXECUTION_HELD
```
