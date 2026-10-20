# AdminApps S3 Host Isolation Lab — SystemCallFilter Validation Remediation

**Date:** 2026-10-09
**Status:** `REVIEWED_SOURCE_ONLY — ROOT_EXECUTION_NOT_AUTHORIZED`
**Scope:** the test-only `S3 Isolation Host Lab` validator and its non-privileged regression tests.

## Authorization packet

### Demonstrated root cause

The protected historical source is identified in the supplied execution record
by SHA-256
`ffe57b21a86fc1c3765c577bdb502fbe9367bdf27a1cb9d47591c5a3501d0b5f`.
The repository source matched that checksum before this remediation.

The reviewed corrected repository source is SHA-256
`14df0b29e45b5fa9de5c8b8c548bd58d58c641349141b55c1e7c735bf640d0df`.

`systemd-run` configures the probe with
`SystemCallFilter=@system-service`. On Rocky Linux 9's systemd 252,
`systemctl show` renders this property as a space-separated, expanded syscall
allow-list rather than retaining the symbolic `@system-service` token. The
previous predicate required that literal token to occur in the returned value:

```bash
grep -q '^SystemCallFilter=.*@system-service' <<<"$actual"
```

Therefore a configured expanded allow-list was rejected deterministically. It
was a representation error in the validator, not evidence that the filter was
absent. The local `systemd-analyze syscall-filter @system-service` inspection
on systemd 252 confirmed that the profile expands through nested syscall
groups; its de-duplicated local expansion contains 370 syscall names.

### Exact correction

The policy passed to `systemd-run` remains exactly
`SystemCallFilter=@system-service`; no hardening property was removed or made
permissive.

The validator now:

1. rejects an empty, malformed, incomplete, duplicate, or otherwise unexpected
   `systemctl show` response;
2. accepts the literal token only as a valid symbolic representation, otherwise
   derives the recursive `@system-service` expansion from the installed
   `systemd-analyze` and compares canonical syscall sets exactly;
3. rejects deny-list markers, unexpanded groups, invalid tokens, duplicate
   effective-list tokens, unavailable expansion evidence, and every differing
   profile;
4. binds `MainPID` to the requested `<unit>.service`, its exact
   `/system.slice/<unit>.service` cgroup, and a second unchanged-PID query;
5. verifies the process's real/effective/saved/filesystem UID and GID, plus
   `NoNewPrivs: 1`, `Seccomp: 2`, and a positive `Seccomp_filters` count in
   `/proc/<pid>/status`.

This uses the two already-designed transient probes only. It does not require
an additional transient unit.

### Diff review

The source is intentionally untracked, so Git has no committed parent from
which to render a normal tracked-file diff. The complete source-level change
is confined to:

* `validate_systemd_probe()` and its new fail-closed parser/evidence helpers
  in `backend/scripts/s3_isolation_host_lab.sh`;
* `backend/scripts/tests/test_s3_isolation_host_lab_validation.sh`, a new
  non-privileged regression harness.

Before root staging, render the complete reviewed-file diff against the
root-owned historical artifact, from an authorized administrative shell:

```bash
sudo diff -u \
  /root/adminapps-s3-isolation-host-lab-2026-10-09.sh \
  /home/felipe/proyectos/adminapps/backend/scripts/s3_isolation_host_lab.sh
```

That command is read-only. Its expected functional difference is the removal
of the literal-token `grep` predicate, the addition of semantic expansion and
process-evidence checks, the command requirements for `systemd-analyze` and
`sort`, and the source-guard that permits the test harness to load functions
without dispatching an operation.

### Checks run without privilege

| Check | Result |
| --- | --- |
| Historical / corrected source SHA-256 | `ffe57b21a86fc1c3765c577bdb502fbe9367bdf27a1cb9d47591c5a3501d0b5f` / `14df0b29e45b5fa9de5c8b8c548bd58d58c641349141b55c1e7c735bf640d0df`. |
| `bash -n` source and regression harness | Pass. |
| Regression harness | Pass: 19 cases. |
| Local systemd 252 profile parser | Pass: recursive expansion collected and canonicalized to 370 syscall names. |
| ShellCheck | Not installed; not substituted or installed. |
| `git diff --check` source | Pass. |
| Privileged lab actions | Not run: no `preflight`, `setup`, `validate`, `cleanup`, `systemd-run`, or protected-copy write. |

The current unprivileged session cannot read `/root`; consequently it did not
inspect, modify, checksum, or overwrite the protected script, checksum sidecar,
or manifest. The historical SHA above is retained as a reference, not relabeled
as the corrected artifact.

### Residual risks and limits

`Seccomp: 2` and `Seccomp_filters > 0` prove that a seccomp filter is active,
not that its BPF program precisely equals `@system-service`. The validator
combines that live evidence with the manager's exact, version-local effective
configuration; it cannot independently disassemble the kernel BPF program.
It also cannot make claims about a unit that exits before inspection, a missing
manager, a missing `systemd-analyze`, incomplete manager output, or ambiguous
`/proc` evidence: all of those fail closed.

The validation remains DAC/systemd evidence only. It does not establish an
IPC authentication boundary, PostgreSQL authorization, a dedicated SELinux
domain, S3 application isolation, or protection from root/DBA compromise.

## Procedure requiring separate human authorization

Do not run these commands as part of this review. After a human approves the
new SHA and complete diff, an administrator may use the existing protected-copy
governance procedure to preserve the historical artifact, stage the exact new
source at the required reviewed path, regenerate its root-owned checksum
sidecar, and verify both hashes. Only a separately explicit authorization may
then run the reviewed script's `validate`; it will create the already-designed
short-lived transient probes and inspect their process evidence. Do not run
`setup` or `cleanup` under this remediation authorization.

The operator's post-staging package must record the old and new hashes, the
full diff, sidecar mode/ownership, systemd version, `systemctl show` output,
the `/proc/<pid>/status` and cgroup evidence (without sensitive material), and
the final stop/cleanup state. A validation failure remains blocking.
