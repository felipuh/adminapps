#!/usr/bin/env bash
# Test-only host lab for the approved AdminApps S3 Decision 02-A boundary.
#
# This script never starts an application service or connects to PostgreSQL.
# setup, validate, and cleanup may run only from the protected reviewed copy
# named below. The repository checkout is review input, never a root target.
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

readonly LAB_ROOT='/var/lib/smart3ai-s3-lab'
readonly RUN_ROOT='/run/smart3ai-s3-lab'
readonly REVIEWED_SCRIPT='/root/adminapps-s3-isolation-host-lab-2026-10-09.sh'
readonly REVIEWED_SUM='/root/adminapps-s3-isolation-host-lab-2026-10-09.sha256'
readonly MANIFEST='/root/adminapps-s3-isolation-host-lab-2026-10-09.run-manifest.tsv'
readonly RUNTIME_USER='s3runtime'
readonly ISSUER_USER='s3issuer'
readonly EXECUTOR_USER='s3executor'
readonly IPC_GROUP='s3labipc'
readonly ISSUER_DIR="$LAB_ROOT/issuer"
readonly EXECUTOR_DIR="$LAB_ROOT/executor"
readonly ISSUER_KEY="$ISSUER_DIR/issuer-ed25519.pem"
readonly EXECUTOR_FIXTURE="$EXECUTOR_DIR/postgres-credential.fixture"
readonly RUN_ID="adminapps-s3-lab-${$}"

usage() {
  cat <<'USAGE'
Usage: s3_isolation_host_lab.sh {preflight|setup|validate|cleanup}

All operations require the root-owned, SHA-256-verified reviewed copy. preflight
is read-only and returns non-zero on any lab-name collision. setup creates only
the declared synthetic resources. validate performs DAC and transient-systemd
checks only. cleanup removes only resources journaled in the root-owned manifest.
USAGE
}

die() {
  printf 'S3 lab error: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command is unavailable: $1"
}

assert_safe_paths() {
  [ "$LAB_ROOT" = '/var/lib/smart3ai-s3-lab' ] || die 'internal lab path invariant failed'
  [ "$RUN_ROOT" = '/run/smart3ai-s3-lab' ] || die 'internal run path invariant failed'
  [ "$MANIFEST" = '/root/adminapps-s3-isolation-host-lab-2026-10-09.run-manifest.tsv' ] || die 'internal manifest path invariant failed'
}

require_reviewed_root_execution() {
  local invoked sum_line
  [ "$(id -u)" -eq 0 ] || die 'this operation must run as root from the reviewed copy'
  [ "$(stat -c '%U:%G:%a' -- /root)" = 'root:root:700' ] || die '/root is not a root-controlled mode-0700 directory'
  invoked="${BASH_SOURCE[0]}"
  [ "$invoked" = "$REVIEWED_SCRIPT" ] || die "refusing mutable or unreviewed script path: $invoked"
  [ -f "$REVIEWED_SCRIPT" ] && [ ! -L "$REVIEWED_SCRIPT" ] || die 'reviewed script is missing or unsafe'
  [ "$(stat -c '%U:%G:%a' -- "$REVIEWED_SCRIPT")" = 'root:root:700' ] || die 'reviewed script must be root:root mode 0700'
  [ -f "$REVIEWED_SUM" ] && [ ! -L "$REVIEWED_SUM" ] || die 'reviewed checksum file is missing or unsafe'
  [ "$(stat -c '%U:%G:%a' -- "$REVIEWED_SUM")" = 'root:root:600' ] || die 'reviewed checksum file must be root:root mode 0600'
  [ "$(wc -l < "$REVIEWED_SUM")" -eq 1 ] || die 'reviewed checksum file must contain exactly one entry'
  sum_line="$(<"$REVIEWED_SUM")"
  grep -Eq "^[[:xdigit:]]{64}  ${REVIEWED_SCRIPT}$" <<<"$sum_line" || die 'reviewed checksum file does not bind this exact script'
  sha256sum --strict -c --status "$REVIEWED_SUM" || die 'reviewed script SHA-256 verification failed'
}

collision_present=0
report_collision() {
  printf 'collision_%s=%s\n' "$1" "$2"
  collision_present=1
}

preflight_collisions() {
  local account path
  for account in "$RUNTIME_USER" "$ISSUER_USER" "$EXECUTOR_USER"; do
    getent passwd "$account" >/dev/null && report_collision "account_$account" present
    getent group "$account" >/dev/null && report_collision "primary_group_$account" present
  done
  getent group "$IPC_GROUP" >/dev/null && report_collision "group_$IPC_GROUP" present
  for path in "$LAB_ROOT" "$RUN_ROOT" "$MANIFEST"; do
    { [ -e "$path" ] || [ -L "$path" ]; } && report_collision "path_${path//\//_}" present
  done
  return 0
}

assert_no_lab_collision() {
  collision_present=0
  preflight_collisions
  [ "$collision_present" -eq 0 ] || die 'lab resource collision; cleanup or owner investigation is required'
}

manifest_init() {
  [ ! -e "$MANIFEST" ] && [ ! -L "$MANIFEST" ] || die 'refusing to overwrite an existing manifest'
  install -o root -g root -m 0600 /dev/null "$MANIFEST"
  manifest_add planned manifest "$MANIFEST" root:root:600
  manifest_add created manifest "$MANIFEST" root:root:600
}

manifest_add() {
  # Fields are constants or locally observed numeric IDs; no caller input is used.
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$MANIFEST"
  sync -f "$MANIFEST"
}

manifest_has() {
  grep -Fqx -- "$1" "$MANIFEST"
}

manifest_require_plan() {
  local expected
  expected="$(printf 'planned\t%s\t%s\t%s' "$1" "$2" "$3")"
  manifest_has "$expected" || die "manifest does not authorize $1 $2"
}

manifest_count() {
  local state="$1" type="$2" resource="$3"
  awk -F '\t' -v state="$state" -v type="$type" -v resource="$resource" '$1 == state && $2 == type && $3 == resource { count++ } END { print count + 0 }' "$MANIFEST"
}

manifest_state() {
  local type="$1" resource="$2" expected="$3" planned created removed
  manifest_require_plan "$type" "$resource" "$expected"
  planned="$(manifest_count planned "$type" "$resource")"
  created="$(manifest_count created "$type" "$resource")"
  removed="$(manifest_count removed "$type" "$resource")"
  [ "$planned" -eq 1 ] || die "manifest has duplicate plan evidence for $type $resource"
  [ "$created" -le 1 ] || die "manifest has duplicate create evidence for $type $resource"
  [ "$removed" -le 1 ] || die "manifest has duplicate removal evidence for $type $resource"
  if [ "$removed" -eq 1 ]; then
    printf 'removed\n'
  elif [ "$created" -eq 1 ]; then
    printf 'created\n'
  else
    printf 'planned\n'
  fi
}

manifest_verify() {
  local state type resource detail
  assert_regular_metadata "$MANIFEST" root:root:600
  awk -F '\t' 'NF != 4 || ($1 != "planned" && $1 != "created" && $1 != "removed") { exit 1 }' "$MANIFEST" || die 'manifest structure is malformed'
  while IFS=$'\t' read -r state type resource detail; do
    case "$type:$resource" in
      "manifest:$MANIFEST"|\
      "directory:$LAB_ROOT"|"directory:$RUN_ROOT"|\
      "directory:$ISSUER_DIR"|"directory:$EXECUTOR_DIR"|\
      "directory:$RUN_ROOT/issuer"|"directory:$RUN_ROOT/executor"|\
      "file:$ISSUER_KEY"|"file:$EXECUTOR_FIXTURE"|\
      "group:$IPC_GROUP"|"group:$RUNTIME_USER"|"group:$ISSUER_USER"|"group:$EXECUTOR_USER"|\
      "user:$RUNTIME_USER"|"user:$ISSUER_USER"|"user:$EXECUTOR_USER"|\
      "membership:$RUNTIME_USER:$IPC_GROUP"|"membership:$ISSUER_USER:$IPC_GROUP"|"membership:$EXECUTOR_USER:$IPC_GROUP") ;;
      *) die "manifest contains an unauthorized resource entry: $type $resource" ;;
    esac
  done < "$MANIFEST"
  manifest_require_plan manifest "$MANIFEST" root:root:600
  [ "$(manifest_count created manifest "$MANIFEST")" -eq 1 ] || die 'manifest lacks its own create evidence'
}

manifest_require_created() {
  [ "$(manifest_state "$1" "$2" "$3")" = 'created' ] || die "resource is not completely created: $1 $2"
}

record_plan() { manifest_add planned "$1" "$2" "$3"; }

record_created() {
  local type="$1" resource="$2" detail="$3"
  [ "$(manifest_count created "$type" "$resource")" -eq 0 ] || die "duplicate create evidence for $type $resource"
  manifest_add created "$type" "$resource" "$detail"
}

record_removed() {
  local type="$1" resource="$2" detail="$3"
  [ "$(manifest_count removed "$type" "$resource")" -eq 0 ] || die "duplicate removal evidence for $type $resource"
  manifest_add removed "$type" "$resource" "$detail"
}

run_as() {
  local user="$1"
  shift
  getent passwd "$user" >/dev/null || die "required lab identity is missing: $user"
  runuser -u "$user" -- "$@"
}

assert_regular_metadata() {
  local path="$1" expected="$2"
  [ -f "$path" ] && [ ! -L "$path" ] || die "required regular file is missing or unsafe: $path"
  [ "$(stat -c '%U:%G:%a' -- "$path")" = "$expected" ] || die "unsafe metadata on $path"
}

assert_directory_metadata() {
  local path="$1" expected="$2"
  [ -d "$path" ] && [ ! -L "$path" ] || die "required directory is missing or unsafe: $path"
  [ "$(stat -c '%U:%G:%a' -- "$path")" = "$expected" ] || die "unsafe metadata on $path"
}

dac_read_is_denied() {
  local user="$1" path="$2" mode uid gid target_uid groups owner_bits group_bits other_bits
  mode="$(stat -c '%a' -- "$path")"
  uid="$(stat -c '%u' -- "$path")"
  gid="$(stat -c '%g' -- "$path")"
  target_uid="$(id -u "$user")"
  groups=" $(id -G "$user") "
  owner_bits=$(( (10#$mode / 100) % 10 ))
  group_bits=$(( (10#$mode / 10) % 10 ))
  other_bits=$(( 10#$mode % 10 ))
  if [ "$target_uid" = "$uid" ]; then
    (( owner_bits & 4 )) && return 1
  elif [[ "$groups" == *" $gid "* ]]; then
    (( group_bits & 4 )) && return 1
  else
    (( other_bits & 4 )) && return 1
  fi
  return 0
}

unexpected_selinux_denial() {
  local path="$1" avc
  [ "$(getenforce 2>/dev/null || printf unavailable)" = 'Enforcing' ] || return 0
  command -v ausearch >/dev/null 2>&1 || return 0
  avc="$(ausearch -m AVC,USER_AVC -ts recent 2>/dev/null || true)"
  if grep -F -- "$path" <<<"$avc" >/dev/null; then
    die "SELinux AVC references $path; DAC-only result is not acceptable"
  fi
  return 0
}

expect_allowed_read() {
  local label="$1" user="$2" path="$3" stderr_file status
  [ -f "$path" ] && [ ! -L "$path" ] || die "positive control target is missing: $path"
  require_command runuser
  require_command head
  stderr_file="$(mktemp)"
  if run_as "$user" /usr/bin/head -c 1 -- "$path" >/dev/null 2>"$stderr_file"; then
    rm -f -- "$stderr_file"
    printf 'PASS %s (positive control)\n' "$label"
    return
  else
    status=$?
  fi
  sed 's/^/command-stderr: /' "$stderr_file" >&2 || true
  rm -f -- "$stderr_file"
  die "expected allowed read failed (status $status): $label"
}

expect_denied_read() {
  local label="$1" user="$2" path="$3" stderr_file status output
  [ -f "$path" ] && [ ! -L "$path" ] || die "cannot classify denied read; file is missing or unsafe: $path"
  getent passwd "$user" >/dev/null || die "cannot classify denied read; identity is missing: $user"
  require_command runuser
  require_command head
  dac_read_is_denied "$user" "$path" || die "test setup is DAC-readable; denial would be ambiguous: $label"
  stderr_file="$(mktemp)"
  if run_as "$user" /usr/bin/head -c 1 -- "$path" >/dev/null 2>"$stderr_file"; then
    rm -f -- "$stderr_file"
    die "expected denied read succeeded: $label"
  else
    status=$?
  fi
  output="$(<"$stderr_file")"
  rm -f -- "$stderr_file"
  [ "$status" -ne 126 ] && [ "$status" -ne 127 ] || die "command execution failed, not access denial: $label"
  grep -Eiq 'permission denied|operation not permitted' <<<"$output" || die "denial was not an access-control denial: $label ($output)"
  unexpected_selinux_denial "$path"
  printf 'PASS %s (DAC denial; file, identity, and command positive controls verified)\n' "$label"
}

selinux_report() {
  local status path
  if command -v getenforce >/dev/null 2>&1; then
    status="$(getenforce)"
  elif [ -r /sys/fs/selinux/enforce ]; then
    case "$(cat /sys/fs/selinux/enforce)" in 1) status='Enforcing' ;; 0) status='Permissive' ;; *) status='unknown' ;; esac
  else
    status='Disabled-or-tool-unavailable'
  fi
  printf 'selinux_status=%s\n' "$status"
  command -v sestatus >/dev/null 2>&1 && sestatus | sed 's/^/selinux_sestatus: /' || true
  for path in "$LAB_ROOT" "$RUN_ROOT" "$ISSUER_DIR" "$EXECUTOR_DIR" "$ISSUER_KEY" "$EXECUTOR_FIXTURE"; do
    if [ -e "$path" ] || [ -L "$path" ]; then
      ls -Zd -- "$path" | sed 's/^/selinux_file_context: /'
    else
      printf 'selinux_file_context=%s:absent\n' "$path"
    fi
  done
}

preflight() {
  require_reviewed_root_execution
  assert_safe_paths
  printf 'host=%s\n' "$(hostname)"
  printf 'boot_id=%s\n' "$(cat /proc/sys/kernel/random/boot_id)"
  printf 'kernel=%s\n' "$(uname -r)"
  printf 'uid_gid=%s:%s\n' "$(id -u)" "$(id -g)"
  selinux_report
  if command -v systemctl >/dev/null 2>&1 && systemctl show --property=Version --value >/dev/null 2>&1; then
    printf 'systemd_manager=reachable\n'
  else
    printf 'systemd_manager=unreachable\n'
  fi
  collision_present=0
  preflight_collisions
  [ "$collision_present" -eq 0 ] || die 'PREFLIGHT_BLOCKED_BY_RESOURCE_COLLISION'
  printf 'preflight_collision_check=clear\n'
  printf 'postgresql_validation=not-implemented (no PostgreSQL command, connection, role, or database is touched)\n'
  printf 'ipc_validation=not-implemented (no IPC endpoint is created or tested)\n'
  printf 'shared_services_changed=no\n'
}

plan_all_resources() {
  record_plan directory "$LAB_ROOT" root:root:711
  record_plan directory "$RUN_ROOT" root:root:711
  record_plan group "$IPC_GROUP" new-system-group
  local user
  for user in "$RUNTIME_USER" "$ISSUER_USER" "$EXECUTOR_USER"; do
    record_plan group "$user" new-primary-system-group
    record_plan user "$user" system:nologin:no-home
    record_plan membership "$user:$IPC_GROUP" supplementary
  done
  record_plan directory "$ISSUER_DIR" "$ISSUER_USER:$ISSUER_USER:700"
  record_plan directory "$EXECUTOR_DIR" "$EXECUTOR_USER:$EXECUTOR_USER:700"
  record_plan directory "$RUN_ROOT/issuer" "$ISSUER_USER:$IPC_GROUP:710"
  record_plan directory "$RUN_ROOT/executor" "$EXECUTOR_USER:$IPC_GROUP:710"
  record_plan file "$ISSUER_KEY" "$ISSUER_USER:$ISSUER_USER:600"
  record_plan file "$EXECUTOR_FIXTURE" "$EXECUTOR_USER:$EXECUTOR_USER:600"
}

create_directory() {
  local path="$1" owner="$2" group="$3" mode="$4" expected="$5"
  install -d -o "$owner" -g "$group" -m "$mode" "$path"
  assert_directory_metadata "$path" "$expected"
  record_created directory "$path" "$expected"
}

assert_lab_user_shape() {
  local user="$1" shell home
  shell="$(getent passwd "$user" | cut -d: -f7)"
  home="$(getent passwd "$user" | cut -d: -f6)"
  [ "$shell" = '/sbin/nologin' ] && [ "$home" = '/nonexistent' ] || die "unsafe account attributes for $user"
  [ "$(id -g "$user")" = "$(getent group "$user" | cut -d: -f3)" ] || die "primary group does not match $user"
}

create_lab_user() {
  local user="$1" actual_group
  useradd --system --user-group --no-create-home --home-dir /nonexistent --shell /sbin/nologin "$user"
  assert_lab_user_shape "$user"
  record_created user "$user" "uid=$(id -u "$user"):gid=$(id -g "$user")"
  actual_group="gid=$(getent group "$user" | cut -d: -f3)"
  record_created group "$user" "$actual_group"
}

add_ipc_membership() {
  local user="$1" ipc_gid
  usermod -a -G "$IPC_GROUP" "$user"
  ipc_gid="$(getent group "$IPC_GROUP" | cut -d: -f3)"
  [[ " $(id -G "$user") " == *" $ipc_gid "* ]] || die "IPC membership was not applied to $user"
  record_created membership "$user:$IPC_GROUP" supplementary
}

setup() {
  require_reviewed_root_execution
  assert_safe_paths
  require_command useradd
  require_command userdel
  require_command groupadd
  require_command groupdel
  require_command install
  require_command openssl
  require_command runuser
  require_command usermod
  require_command sync
  assert_no_lab_collision
  manifest_init
  trap 'setup_interrupted "$?"' ERR HUP INT TERM
  # Journal the complete intended inventory before the first lab mutation.
  # A planned-only resource is never safe for automatic deletion.
  plan_all_resources

  create_directory "$LAB_ROOT" root root 0711 root:root:711
  create_directory "$RUN_ROOT" root root 0711 root:root:711
  groupadd --system "$IPC_GROUP"
  record_created group "$IPC_GROUP" "gid=$(getent group "$IPC_GROUP" | cut -d: -f3)"
  local user
  for user in "$RUNTIME_USER" "$ISSUER_USER" "$EXECUTOR_USER"; do
    create_lab_user "$user"
    add_ipc_membership "$user"
  done
  create_directory "$ISSUER_DIR" "$ISSUER_USER" "$ISSUER_USER" 0700 "$ISSUER_USER:$ISSUER_USER:700"
  create_directory "$EXECUTOR_DIR" "$EXECUTOR_USER" "$EXECUTOR_USER" 0700 "$EXECUTOR_USER:$EXECUTOR_USER:700"
  create_directory "$RUN_ROOT/issuer" "$ISSUER_USER" "$IPC_GROUP" 0710 "$ISSUER_USER:$IPC_GROUP:710"
  create_directory "$RUN_ROOT/executor" "$EXECUTOR_USER" "$IPC_GROUP" 0710 "$EXECUTOR_USER:$IPC_GROUP:710"
  run_as "$ISSUER_USER" openssl genpkey -algorithm ED25519 -out "$ISSUER_KEY"
  chown "$ISSUER_USER:$ISSUER_USER" "$ISSUER_KEY"
  chmod 0600 "$ISSUER_KEY"
  assert_regular_metadata "$ISSUER_KEY" "$ISSUER_USER:$ISSUER_USER:600"
  record_created file "$ISSUER_KEY" "$ISSUER_USER:$ISSUER_USER:600"
  run_as "$EXECUTOR_USER" /usr/bin/sh -c "umask 077; printf '%s\\n' s3-lab-disposable-executor-fixture > '$EXECUTOR_FIXTURE'"
  chown "$EXECUTOR_USER:$EXECUTOR_USER" "$EXECUTOR_FIXTURE"
  chmod 0600 "$EXECUTOR_FIXTURE"
  assert_regular_metadata "$EXECUTOR_FIXTURE" "$EXECUTOR_USER:$EXECUTOR_USER:600"
  record_created file "$EXECUTOR_FIXTURE" "$EXECUTOR_USER:$EXECUTOR_USER:600"
  trap - ERR HUP INT TERM
  printf 'SETUP_COMPLETE manifest=%s\n' "$MANIFEST"
}

setup_interrupted() {
  local status="$1"
  trap - ERR HUP INT TERM
  [ "$status" -ne 0 ] || status=1
  printf 'SETUP_INTERRUPTED manifest=%s; run reviewed cleanup after inspection\n' "$MANIFEST" >&2
  exit "$status"
}

validate_systemd_probe() {
  local user="$1" unit="${RUN_ID}-${1}" actual pid expected_uid expected_gid process_context process_status process_cgroup control_group current_pid
  local -a systemd_properties=(
    ActiveState SubState MainPID User Group NoNewPrivileges PrivateTmp
    ProtectSystem ProtectHome PrivateDevices RestrictNamespaces
    CapabilityBoundingSet SystemCallFilter Id ControlGroup
  )
  require_command systemd-run
  require_command systemctl
  require_command ps
  require_command sleep
  require_command systemd-analyze
  require_command sort
  systemctl show --property=Version --value >/dev/null 2>&1 || die 'systemd manager is unreachable; no systemd hardening claim is possible'
  systemd-run --unit="$unit" --quiet --service-type=exec \
    --property="User=$user" --property="Group=$user" \
    --property='NoNewPrivileges=yes' --property='CapabilityBoundingSet=' \
    --property='PrivateTmp=yes' --property='ProtectSystem=strict' \
    --property='ProtectHome=yes' --property='PrivateDevices=yes' \
    --property='RestrictNamespaces=yes' --property='SystemCallFilter=@system-service' \
    --property='RuntimeMaxSec=30s' /usr/bin/sleep 25
  trap 'systemctl stop "'$unit'" >/dev/null 2>&1 || true' RETURN
  sleep 1
  actual="$(systemctl show "$unit" --property=ActiveState,SubState,MainPID,User,Group,NoNewPrivileges,PrivateTmp,ProtectSystem,ProtectHome,PrivateDevices,RestrictNamespaces,CapabilityBoundingSet,SystemCallFilter,Id,ControlGroup --no-pager)" || die "cannot query transient probe properties for $user"
  validate_systemd_show_response "$actual" "${systemd_properties[@]}" || die "systemd returned malformed or incomplete properties for $user"
  printf '%s\n' "$actual"
  [ "$(systemd_show_property "$actual" ActiveState)" = 'active' ] || die "transient probe is not alive for $user"
  [ "$(systemd_show_property "$actual" SubState)" = 'running' ] || die "transient probe is not running for $user"
  [ "$(systemd_show_property "$actual" Id)" = "${unit}.service" ] || die "transient probe identity does not match requested unit for $user"
  control_group="$(systemd_show_property "$actual" ControlGroup)"
  [ "$control_group" = "/system.slice/${unit}.service" ] || die "transient probe control group does not match requested unit for $user"
  pid="$(systemd_show_property "$actual" MainPID)"
  [[ "$pid" =~ ^[1-9][0-9]*$ ]] && kill -0 "$pid" || die "transient probe has no live main PID for $user"
  expected_uid="$(id -u "$user")"
  expected_gid="$(id -g "$user")"
  [ -r "/proc/$pid/status" ] || die "transient probe status disappeared for $user"
  process_status="$(<"/proc/$pid/status")" || die "cannot read transient probe status for $user"
  process_status_matches_identity_and_seccomp "$process_status" "$expected_uid" "$expected_gid" || die "transient probe identity or seccomp evidence is absent for $user"
  [ -r "/proc/$pid/cgroup" ] || die "transient probe cgroup evidence disappeared for $user"
  process_cgroup="$(<"/proc/$pid/cgroup")" || die "cannot read transient probe cgroup evidence for $user"
  process_cgroup_matches "$process_cgroup" "$control_group" || die "transient probe PID does not belong to its reported control group for $user"
  [ "$(systemd_show_property "$actual" User)" = "$user" ] || die "systemd User property not applied for $user"
  [ "$(systemd_show_property "$actual" Group)" = "$user" ] || die "systemd Group property not applied for $user"
  local property
  for property in NoNewPrivileges=yes PrivateTmp=yes ProtectSystem=strict ProtectHome=yes PrivateDevices=yes RestrictNamespaces=yes; do
    [ "$(systemd_show_property "$actual" "${property%%=*}")" = "${property#*=}" ] || die "systemd property $property not applied for $user"
  done
  [ -z "$(systemd_show_property "$actual" CapabilityBoundingSet)" ] || die "empty CapabilityBoundingSet not applied for $user"
  system_call_filter_matches_system_service "$(systemd_show_property "$actual" SystemCallFilter)" || die "SystemCallFilter does not semantically match @system-service for $user"
  current_pid="$(systemctl show "$unit" --property=MainPID --value --no-pager)" || die "cannot recheck transient probe PID for $user"
  [ "$current_pid" = "$pid" ] && kill -0 "$pid" || die "transient probe PID changed or exited during validation for $user"
  process_context="$(ps -o label= -p "$pid" | xargs)"
  printf 'systemd_process_context_%s=%s\n' "$user" "${process_context:-unavailable}"
  systemctl stop "$unit" >/dev/null
  trap - RETURN
}

# systemctl show renders SystemCallFilter as the effective expanded syscall
# list on systemd 252.  Do not compare that output to the source token
# @system-service: derive the same version-local expansion and compare exact
# allow-list membership instead.  A deny-list marker (~), an unexpanded group,
# an empty list, duplicate list item, or parser ambiguity is rejected.
systemd_show_property() {
  local response="$1" requested="$2" line key value count=0 result=''
  while IFS= read -r line; do
    key="${line%%=*}"
    value="${line#*=}"
    [ "$key" != "$line" ] || return 1
    if [ "$key" = "$requested" ]; then
      count=$((count + 1))
      result="$value"
    fi
  done <<<"$response"
  [ "$count" -eq 1 ] || return 1
  printf '%s\n' "$result"
}

validate_systemd_show_response() {
  local response="$1" line key expected
  shift
  [ -n "$response" ] || return 1
  declare -A expected_properties=() seen_properties=()
  for expected in "$@"; do
    expected_properties["$expected"]=1
  done
  while IFS= read -r line; do
    key="${line%%=*}"
    [ "$key" != "$line" ] || return 1
    [ -n "${expected_properties[$key]+present}" ] || return 1
    [ -z "${seen_properties[$key]+present}" ] || return 1
    seen_properties["$key"]=1
  done <<<"$response"
  for expected in "$@"; do
    [ -n "${seen_properties[$expected]+present}" ] || return 1
  done
}

systemd_filter_group_members() {
  local group="$1" output first_line
  output="$(systemd-analyze syscall-filter "$group")" || return 1
  first_line="${output%%$'\n'*}"
  [ "$first_line" = "$group" ] || return 1
  awk '
    NR == 1 { next }
    /^[[:space:]]*$/ || /^[[:space:]]*#/ { next }
    /^[[:space:]]+[^[:space:]]+[[:space:]]*$/ {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      print
      next
    }
    { exit 1 }
  ' <<<"$output"
}

systemd_system_service_syscalls() {
  local group member members
  local -a pending_groups=('@system-service')
  declare -A seen_groups=()
  while [ "${#pending_groups[@]}" -gt 0 ]; do
    group="${pending_groups[0]}"
    pending_groups=("${pending_groups[@]:1}")
    [ -z "${seen_groups[$group]+present}" ] || continue
    seen_groups["$group"]=1
    members="$(systemd_filter_group_members "$group")" || return 1
    while IFS= read -r member; do
      case "$member" in
        @*) [[ "$member" =~ ^@[a-z0-9-]+$ ]] || return 1; pending_groups+=("$member") ;;
        *) [[ "$member" =~ ^[a-zA-Z0-9_]+$ ]] || return 1; printf '%s\n' "$member" ;;
      esac
    done <<<"$members"
  done
}

canonical_syscall_set() {
  local list="$1" duplicate_policy="${2:-reject}" token
  local -A seen=()
  [ "$duplicate_policy" = 'reject' ] || [ "$duplicate_policy" = 'allow' ] || return 1
  [ -n "$list" ] || return 1
  while IFS= read -r token; do
    [ -n "$token" ] || continue
    [[ "$token" =~ ^[a-zA-Z0-9_]+$ ]] || return 1
    if [ -n "${seen[$token]+present}" ]; then
      [ "$duplicate_policy" = 'allow' ] || return 1
      continue
    fi
    seen["$token"]=1
  done < <(tr '[:space:]' '\n' <<<"$list")
  [ "${#seen[@]}" -gt 0 ] || return 1
  printf '%s\n' "${!seen[@]}" | LC_ALL=C sort
}

system_call_filter_matches_system_service() {
  local reported="$1" expected_members expected actual
  [ "$reported" = '@system-service' ] && return 1
  expected_members="$(systemd_system_service_syscalls)" || return 1
  expected="$(canonical_syscall_set "$expected_members" allow)" || return 1
  actual="$(canonical_syscall_set "$reported")" || return 1
  [ "$actual" = "$expected" ]
}

proc_status_field() {
  local status="$1" requested="$2"
  awk -F: -v requested="$requested" '
    $1 == requested {
      if (++count != 1) exit 1
      value = $2
      sub(/^[[:space:]]+/, "", value)
    }
    END {
      if (count != 1) exit 1
      print value
    }
  ' <<<"$status"
}

process_status_matches_identity_and_seccomp() {
  local status="$1" expected_uid="$2" expected_gid="$3" uid gid no_new_privs seccomp filters
  uid="$(proc_status_field "$status" Uid)" || return 1
  gid="$(proc_status_field "$status" Gid)" || return 1
  no_new_privs="$(proc_status_field "$status" NoNewPrivs)" || return 1
  seccomp="$(proc_status_field "$status" Seccomp)" || return 1
  filters="$(proc_status_field "$status" Seccomp_filters)" || return 1
  [ "$uid" = "$expected_uid"$'\t'"$expected_uid"$'\t'"$expected_uid"$'\t'"$expected_uid" ] || return 1
  [ "$gid" = "$expected_gid"$'\t'"$expected_gid"$'\t'"$expected_gid"$'\t'"$expected_gid" ] || return 1
  [ "$no_new_privs" = '1' ] || return 1
  [ "$seccomp" = '2' ] || return 1
  [[ "$filters" =~ ^[1-9][0-9]*$ ]]
}

process_cgroup_matches() {
  local cgroup_data="$1" expected_control_group="$2"
  awk -F: -v expected="$expected_control_group" '$3 == expected { found = 1 } END { exit !found }' <<<"$cgroup_data"
}

validate() {
  require_reviewed_root_execution
  assert_safe_paths
  manifest_verify
  manifest_require_created directory "$LAB_ROOT" root:root:711
  manifest_require_created directory "$RUN_ROOT" root:root:711
  manifest_require_created file "$ISSUER_KEY" "$ISSUER_USER:$ISSUER_USER:600"
  manifest_require_created file "$EXECUTOR_FIXTURE" "$EXECUTOR_USER:$EXECUTOR_USER:600"
  assert_directory_metadata "$LAB_ROOT" root:root:711
  assert_directory_metadata "$RUN_ROOT" root:root:711
  assert_regular_metadata "$ISSUER_KEY" "$ISSUER_USER:$ISSUER_USER:600"
  assert_regular_metadata "$EXECUTOR_FIXTURE" "$EXECUTOR_USER:$EXECUTOR_USER:600"
  selinux_report
  expect_allowed_read 'issuer reads issuer key' "$ISSUER_USER" "$ISSUER_KEY"
  expect_denied_read 'runtime denied issuer key' "$RUNTIME_USER" "$ISSUER_KEY"
  expect_denied_read 'executor denied issuer key' "$EXECUTOR_USER" "$ISSUER_KEY"
  expect_allowed_read 'executor reads executor fixture' "$EXECUTOR_USER" "$EXECUTOR_FIXTURE"
  expect_denied_read 'runtime denied executor fixture' "$RUNTIME_USER" "$EXECUTOR_FIXTURE"
  expect_denied_read 'issuer denied executor fixture' "$ISSUER_USER" "$EXECUTOR_FIXTURE"
  printf 'uid_runtime=%s\n' "$(id -u "$RUNTIME_USER")"
  printf 'uid_issuer=%s\n' "$(id -u "$ISSUER_USER")"
  printf 'uid_executor=%s\n' "$(id -u "$EXECUTOR_USER")"
  validate_systemd_probe "$ISSUER_USER"
  validate_systemd_probe "$EXECUTOR_USER"
  printf 'ipc_validation=not-implemented (DAC/systemd checks are not IPC evidence)\n'
  printf 'postgresql_validation=not-implemented (DAC/systemd checks are not PostgreSQL evidence)\n'
  printf 'VALIDATION_COMPLETE\n'
}

manifest_has_plan() {
  [ "$(manifest_count planned "$1" "$2")" -eq 1 ]
}

manifest_created_detail() {
  awk -F '\t' -v type="$1" -v resource="$2" '$1 == "created" && $2 == type && $3 == resource { print $4 }' "$MANIFEST"
}

assert_user_matches_manifest() {
  local user="$1" expected actual
  expected="$(manifest_created_detail user "$user")"
  [ -n "$expected" ] || die "missing create evidence for account $user"
  assert_lab_user_shape "$user"
  actual="uid=$(id -u "$user"):gid=$(id -g "$user")"
  [ "$actual" = "$expected" ] || die "identity mismatch for $user"
}

assert_group_matches_manifest() {
  local group="$1" expected actual
  expected="$(manifest_created_detail group "$group")"
  [ -n "$expected" ] || die "missing create evidence for group $group"
  actual="gid=$(getent group "$group" | cut -d: -f3)"
  [ "$actual" = "$expected" ] || die "group mismatch for $group"
}

resource_exists() {
  case "$1" in
    path) [ -e "$2" ] || [ -L "$2" ] ;;
    user) getent passwd "$2" >/dev/null ;;
    group) getent group "$2" >/dev/null ;;
    *) die "internal resource-presence invariant failed: $1" ;;
  esac
}

assert_planned_only_absent() {
  local type="$1" resource="$2" presence_kind="$3" expected="$4"
  if manifest_has_plan "$type" "$resource"; then
    [ "$(manifest_state "$type" "$resource" "$expected")" = 'planned' ] || return 0
    resource_exists "$presence_kind" "$resource" && die "planned-only $type exists; manual adjudication required: $resource"
  else
    resource_exists "$presence_kind" "$resource" && die "unplanned lab-named resource exists; manual adjudication required: $resource"
  fi
  return 0
}

cleanup_file() {
  local path="$1" metadata="$2" state
  assert_planned_only_absent file "$path" path "$metadata"
  manifest_has_plan file "$path" || return 0
  state="$(manifest_state file "$path" "$metadata")"
  [ "$state" = 'removed' ] && { [ ! -e "$path" ] && [ ! -L "$path" ] || die "removed file reappeared: $path"; return; }
  [ "$state" = 'created' ] || return 0
  if [ -e "$path" ] || [ -L "$path" ]; then
    assert_regular_metadata "$path" "$metadata"
    rm -f -- "$path"
  fi
  record_removed file "$path" "$metadata"
}

cleanup_directory() {
  local path="$1" metadata="$2" state
  assert_planned_only_absent directory "$path" path "$metadata"
  manifest_has_plan directory "$path" || return 0
  state="$(manifest_state directory "$path" "$metadata")"
  [ "$state" = 'removed' ] && { [ ! -e "$path" ] && [ ! -L "$path" ] || die "removed directory reappeared: $path"; return; }
  [ "$state" = 'created' ] || return 0
  if [ -e "$path" ] || [ -L "$path" ]; then
    assert_directory_metadata "$path" "$metadata"
    rmdir -- "$path"
  fi
  record_removed directory "$path" "$metadata"
}

cleanup_membership() {
  local user="$1" resource="$user:$IPC_GROUP" state ipc_gid
  manifest_has_plan membership "$resource" || return 0
  state="$(manifest_state membership "$resource" supplementary)"
  [ "$state" = 'removed' ] && return
  ipc_gid="$(getent group "$IPC_GROUP" 2>/dev/null | cut -d: -f3 || true)"
  if [ "$state" = 'planned' ]; then
    if getent passwd "$user" >/dev/null && [ -n "$ipc_gid" ] && [[ " $(id -G "$user") " == *" $ipc_gid "* ]]; then
      die "planned-only IPC membership exists; manual adjudication required: $resource"
    fi
    return
  fi
  if ! getent passwd "$user" >/dev/null; then
    record_removed membership "$resource" supplementary
    return
  fi
  [ -n "$ipc_gid" ] || die "recorded IPC group is missing for $user"
  [[ " $(id -G "$user") " == *" $ipc_gid "* ]] || die "recorded IPC membership is missing for $user"
  gpasswd -d "$user" "$IPC_GROUP" >/dev/null
  record_removed membership "$resource" supplementary
}

cleanup_user() {
  local user="$1" state
  assert_planned_only_absent user "$user" user system:nologin:no-home
  manifest_has_plan user "$user" || return 0
  state="$(manifest_state user "$user" system:nologin:no-home)"
  [ "$state" = 'removed' ] && { getent passwd "$user" >/dev/null && die "removed account reappeared: $user"; return; }
  [ "$state" = 'created' ] || return 0
  if getent passwd "$user" >/dev/null; then
    pgrep -u "$user" >/dev/null 2>&1 && die "refusing cleanup: active process still uses $user"
    assert_user_matches_manifest "$user"
    userdel "$user"
  fi
  record_removed user "$user" removed-or-absent
}

cleanup_group() {
  local group="$1" expected="$2" state
  assert_planned_only_absent group "$group" group "$expected"
  manifest_has_plan group "$group" || return 0
  state="$(manifest_state group "$group" "$expected")"
  [ "$state" = 'removed' ] && { getent group "$group" >/dev/null && die "removed group reappeared: $group"; return; }
  [ "$state" = 'created' ] || return 0
  if getent group "$group" >/dev/null; then
    assert_group_matches_manifest "$group"
    groupdel "$group"
  fi
  record_removed group "$group" removed-or-absent
}

cleanup() {
  require_reviewed_root_execution
  assert_safe_paths
  require_command pgrep
  require_command gpasswd
  manifest_verify
  # Planned-only state is intentionally non-destructive: a signal could have
  # landed after a kernel/account operation but before create evidence was
  # fsynced. Such a resource requires human adjudication, never a guess.
  cleanup_file "$ISSUER_KEY" "$ISSUER_USER:$ISSUER_USER:600"
  cleanup_file "$EXECUTOR_FIXTURE" "$EXECUTOR_USER:$EXECUTOR_USER:600"
  cleanup_directory "$RUN_ROOT/issuer" "$ISSUER_USER:$IPC_GROUP:710"
  cleanup_directory "$RUN_ROOT/executor" "$EXECUTOR_USER:$IPC_GROUP:710"
  cleanup_directory "$ISSUER_DIR" "$ISSUER_USER:$ISSUER_USER:700"
  cleanup_directory "$EXECUTOR_DIR" "$EXECUTOR_USER:$EXECUTOR_USER:700"
  cleanup_directory "$RUN_ROOT" root:root:711
  local user
  for user in "$RUNTIME_USER" "$ISSUER_USER" "$EXECUTOR_USER"; do
    cleanup_membership "$user"
  done
  for user in "$RUNTIME_USER" "$ISSUER_USER" "$EXECUTOR_USER"; do
    cleanup_user "$user"
  done
  for user in "$RUNTIME_USER" "$ISSUER_USER" "$EXECUTOR_USER"; do
    cleanup_group "$user" new-primary-system-group
  done
  cleanup_group "$IPC_GROUP" new-system-group
  cleanup_directory "$LAB_ROOT" root:root:711
  # Deliberately last: every created lab identity, file, and directory must
  # be removed or proven absent. A planned-only existing resource leaves this
  # journal intact and blocks for manual adjudication.
  rm -f -- "$MANIFEST"
  printf 'CLEANUP_COMPLETE\n'
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  case "${1:-}" in
    preflight) preflight ;;
    setup) setup ;;
    validate) validate ;;
    cleanup) cleanup ;;
    *) usage; exit 64 ;;
  esac
fi
