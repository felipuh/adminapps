#!/usr/bin/env bash
# Non-privileged regression tests for the pure parsing/evidence predicates.
set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../s3_isolation_host_lab.sh"

passed=0
failed=0

expect_pass() {
  local name="$1"
  shift
  if "$@"; then
    printf 'PASS %s\n' "$name"
    passed=$((passed + 1))
  else
    printf 'FAIL %s (unexpected rejection)\n' "$name" >&2
    failed=$((failed + 1))
  fi
}

expect_fail() {
  local name="$1"
  shift
  if "$@"; then
    printf 'FAIL %s (unexpected acceptance)\n' "$name" >&2
    failed=$((failed + 1))
  else
    printf 'PASS %s\n' "$name"
    passed=$((passed + 1))
  fi
}

# Controlled systemd-analyze fixture.  It covers a nested group because the
# production parser must compare the fully expanded, version-local allow list.
systemd_filter_group_members() {
  case "$1" in
    @system-service) printf '%s\n' '@base' gamma ;;
    @base) printf '%s\n' alpha beta ;;
    *) return 1 ;;
  esac
}

expect_fail 'symbolic SystemCallFilter' system_call_filter_matches_system_service '@system-service'
expect_pass 'expanded SystemCallFilter' system_call_filter_matches_system_service 'gamma alpha beta'
expect_fail 'empty SystemCallFilter' system_call_filter_matches_system_service ''
expect_fail 'different SystemCallFilter' system_call_filter_matches_system_service 'alpha gamma'
expect_fail 'deny-list SystemCallFilter' system_call_filter_matches_system_service '~alpha beta gamma'
expect_fail 'duplicate expanded syscall' system_call_filter_matches_system_service 'alpha beta beta gamma'

systemd_filter_group_members() { return 1; }
expect_fail 'unavailable SystemCallFilter expansion evidence' system_call_filter_matches_system_service 'alpha beta gamma'

show_response=$'ActiveState=active\nMainPID=123\nSystemCallFilter=alpha beta gamma'
expect_pass 'well-formed selected systemctl response' validate_systemd_show_response "$show_response" ActiveState MainPID SystemCallFilter
expect_fail 'empty systemctl response (query error)' validate_systemd_show_response '' ActiveState MainPID SystemCallFilter
expect_fail 'malformed systemctl response' validate_systemd_show_response $'ActiveState=active\nnot-a-property' ActiveState MainPID SystemCallFilter
expect_fail 'incomplete systemctl response' validate_systemd_show_response $'ActiveState=active\nMainPID=123' ActiveState MainPID SystemCallFilter
expect_fail 'duplicate systemctl property' validate_systemd_show_response $'ActiveState=active\nMainPID=123\nMainPID=124\nSystemCallFilter=alpha beta gamma' ActiveState MainPID SystemCallFilter

status=$'Uid:\t42\t42\t42\t42\nGid:\t43\t43\t43\t43\nNoNewPrivs:\t1\nSeccomp:\t2\nSeccomp_filters:\t1'
expect_pass 'process identity and active seccomp evidence' process_status_matches_identity_and_seccomp "$status" 42 43
expect_fail 'nonexistent or exited PID has no status evidence' process_status_matches_identity_and_seccomp '' 42 43
expect_fail 'wrong process identity' process_status_matches_identity_and_seccomp "$status" 99 43
expect_fail 'seccomp inactive' process_status_matches_identity_and_seccomp "${status/Seccomp:$'\t'2/Seccomp:$'\t'0}" 42 43
expect_fail 'missing seccomp filter count' process_status_matches_identity_and_seccomp "${status/Seccomp_filters:$'\t'1/Seccomp_filters:$'\t'0}" 42 43

expect_pass 'process belongs to reported unit cgroup' process_cgroup_matches '0::/system.slice/adminapps-s3-lab-1-s3issuer.service' '/system.slice/adminapps-s3-lab-1-s3issuer.service'
expect_fail 'process does not belong to reported unit cgroup' process_cgroup_matches '0::/system.slice/other.service' '/system.slice/adminapps-s3-lab-1-s3issuer.service'

printf 'tests_passed=%s tests_failed=%s\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
