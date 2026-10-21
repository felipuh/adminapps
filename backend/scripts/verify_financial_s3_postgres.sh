#!/usr/bin/env bash
# Disposable S3 PostgreSQL race proof.  It creates no production data or role.
set -euo pipefail

financial_s3_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
financial_s3_tmpdir="$(mktemp -d /tmp/adminapps-financial-s3.XXXXXX)"
financial_s3_pgdata="$financial_s3_tmpdir/postgres"
financial_s3_socket="$financial_s3_tmpdir/socket"
financial_s3_port="55440"

cleanup() {
  if [ -f "$financial_s3_pgdata/postmaster.pid" ]; then
    pg_ctl -D "$financial_s3_pgdata" -m immediate stop >/dev/null 2>&1 || true
  fi
  rm -rf "$financial_s3_tmpdir"
}
trap cleanup EXIT

mkdir -p "$financial_s3_socket"
initdb -D "$financial_s3_pgdata" --auth=trust --no-locale >/dev/null
financial_s3_log="$financial_s3_tmpdir/postgres.log"
if ! pg_ctl -D "$financial_s3_pgdata" -o "-k $financial_s3_socket -p $financial_s3_port -c listen_addresses='' -c logging_collector=off" -l "$financial_s3_log" -w start >/dev/null; then
  cat "$financial_s3_log" >&2
  exit 1
fi

psql -h "$financial_s3_socket" -p "$financial_s3_port" -d postgres -v ON_ERROR_STOP=1 <<'SQL' >/dev/null
CREATE ROLE adminapps_financial_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_producer NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_audit NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_reconciliation NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_admission NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
-- Disposable executor-only login.  The isolated executor process is the only
-- component given this identity; it disappears with this cluster.
CREATE ROLE adminapps_financial_executor LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
-- This disposable login has no inherited table privileges.  It exists solely
-- so the verifier can prove the runtime role from a non-administrator
-- database session; production role provisioning remains out of scope.
CREATE ROLE adminapps_financial_runtime_evidence LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
GRANT adminapps_financial_runtime TO adminapps_financial_runtime_evidence;
SQL

cd "$financial_s3_root"
USE_POSTGRES_FOR_TESTS=true DB_NAME="adminapps_financial_s3" DB_USER="$(id -un)" DB_HOST="$financial_s3_socket" DB_PORT="$financial_s3_port" \
  .venv312/bin/python manage.py test \
    apps.financial.tests.FinancialAdmissionPostgresConcurrencyTests \
    apps.financial.tests.FinancialAdmissionPostgresRuntimeRoleTests --verbosity 2

echo 'ADMINAPPS_FINANCIAL_S3_POSTGRES_DECISION_02_A_BOUNDARY_EVIDENCE_COMPLETE'
echo 'Cleanup: temporary PostgreSQL cluster will be removed by the exit trap.'
