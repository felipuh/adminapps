#!/usr/bin/env bash
# Disposable S1 PostgreSQL proof harness.  It uses synthetic data only.
set -euo pipefail

financial_s1_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
financial_s1_tmpdir="$(mktemp -d /tmp/adminapps-financial-s1.XXXXXX)"
financial_s1_pgdata="$financial_s1_tmpdir/postgres"
financial_s1_socket="$financial_s1_tmpdir/socket"
financial_s1_port="55439"
financial_s1_db="adminapps_financial_s1"

cleanup() {
  if [ -f "$financial_s1_pgdata/postmaster.pid" ]; then
    pg_ctl -D "$financial_s1_pgdata" -m immediate stop >/dev/null 2>&1 || true
  fi
  rm -rf "$financial_s1_tmpdir"
}
trap cleanup EXIT

mkdir -p "$financial_s1_socket"
initdb -D "$financial_s1_pgdata" --auth=trust --no-locale >/dev/null
financial_s1_log="$financial_s1_tmpdir/postgres.log"
if ! pg_ctl -D "$financial_s1_pgdata" -o "-k $financial_s1_socket -p $financial_s1_port -c listen_addresses='' -c logging_collector=off" -l "$financial_s1_log" -w start >/dev/null; then
  cat "$financial_s1_log" >&2
  exit 1
fi

psql -h "$financial_s1_socket" -p "$financial_s1_port" -d postgres -v ON_ERROR_STOP=1 <<'SQL'
CREATE DATABASE adminapps_financial_s1;
\connect adminapps_financial_s1
CREATE ROLE adminapps_financial_migration LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_producer NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_audit NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_reconciliation NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE adminapps_financial_admission NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
DO $$
BEGIN
  EXECUTE format('GRANT adminapps_financial_runtime TO %I', current_user);
  EXECUTE format('GRANT adminapps_financial_audit TO %I', current_user);
  EXECUTE format('GRANT adminapps_financial_reconciliation TO %I', current_user);
END $$;
SQL

cd "$financial_s1_root"
DB_NAME="$financial_s1_db" DB_USER="$(id -un)" DB_HOST="$financial_s1_socket" DB_PORT="$financial_s1_port" \
  .venv312/bin/python manage.py migrate financial 0001 --noinput >/dev/null
DB_NAME="$financial_s1_db" DB_USER="$(id -un)" DB_HOST="$financial_s1_socket" DB_PORT="$financial_s1_port" \
  .venv312/bin/python manage.py migrate --noinput >/dev/null

psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO organizations (id, code, name, legal_name, tax_id, email, phone, website, address, city, state, country, postal_code, industry, size, employees_count, primary_color, secondary_color, status, max_users, max_documents, max_storage_mb, iso_standards, notes, metadata, created_at, updated_at)
VALUES
  ('00000000-0000-0000-0000-0000000000a1', 'FINA', 'Tenant A', '', '', 'a@example.test', '', '', '', '', '', 'Test', '', 'services', 'small', 1, '#000000', '#111111', 'active', 1, 1, 1, '[]', '', '{}', now(), now()),
  ('00000000-0000-0000-0000-0000000000a2', 'FINB', 'Tenant B', '', '', 'b@example.test', '', '', '', '', '', 'Test', '', 'services', 'small', 1, '#000000', '#111111', 'active', 1, 1, 1, '[]', '', '{}', now(), now());
INSERT INTO product_systems (id, code, name, slug, description, product_type, status, billing_enabled, launch_url, api_base_url, icon, metadata, created_at, updated_at)
VALUES ('00000000-0000-0000-0000-0000000000a3', 'FINS1', 'Financial S1 test product', 'financial-s1-test', '', 'saas', 'development', true, '', '', '', '{}', now(), now());
INSERT INTO financial_policies (id, policy_code, organization_id, created_at)
VALUES ('00000000-0000-0000-0000-0000000000a4', 'synthetic', '00000000-0000-0000-0000-0000000000a1', now());
INSERT INTO financial_policy_versions (id, version, state, currency, period_timezone, period_boundary, amount_precision, rounding_rule, allowed_provider, allowed_model, approved_evidence_hash, created_at, policy_id)
VALUES ('00000000-0000-0000-0000-0000000000a5', 1, 'draft', 'USD', 'UTC', 'calendar_month', 10, 'half_up', '', '', '', now(), '00000000-0000-0000-0000-0000000000a4');
INSERT INTO financial_verified_tariffs (id, provider, model_identifier, version, state, currency, input_unit_cost, output_unit_cost, unit_size, source_reference, source_hash, created_at)
VALUES ('00000000-0000-0000-0000-0000000000a6', 'synthetic', 'model', 1, 'draft', 'USD', 0.0000000001, 0.0000000002, 1, 'synthetic', repeat('a', 64), now());
INSERT INTO financial_producer_registrations (id, producer_code, credential_fingerprint, environment, permitted_product_ids, permitted_operations, lifecycle_state, creation_evidence_hash, revocation_evidence_hash, audit_owner, created_at)
VALUES ('00000000-0000-0000-0000-0000000000a7', 'SYNTHETIC', '', 'controlled_test', '[]', '[]', 'pending', repeat('b', 64), '', 'S1 harness', now());
INSERT INTO financial_producer_registration_events (id, lifecycle_state, actor_reference, evidence_hash, reason_code, metadata, created_at, registration_id)
VALUES ('00000000-0000-0000-0000-0000000000c1', 'pending', 'S2 harness', repeat('h', 64), 'synthetic_registration', '{}', now(), '00000000-0000-0000-0000-0000000000a7');
INSERT INTO financial_permission_audit_events (id, action, permission_code, actor_reference, subject_reference, reason_code, metadata, created_at)
VALUES ('00000000-0000-0000-0000-0000000000c2', 'denied', 'financial_audit_read', 'S2 harness', '', 'synthetic_denial', '{}', now());
INSERT INTO financial_admission_decisions (id, invocation_id, material_request_hash, decision_state, correlation_id, currency, reserved_amount, denial_code, created_at, organization_id, policy_version_id, producer_registration_id, product_id, tariff_id)
VALUES
 ('00000000-0000-0000-0000-0000000000a8', '10000000-0000-0000-0000-000000000001', repeat('c', 64), 'reserved', '20000000-0000-0000-0000-000000000001', 'USD', 1.0000000000, '', now(), '00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-0000000000a5', '00000000-0000-0000-0000-0000000000a7', '00000000-0000-0000-0000-0000000000a3', '00000000-0000-0000-0000-0000000000a6'),
 ('00000000-0000-0000-0000-0000000000a9', '10000000-0000-0000-0000-000000000002', repeat('d', 64), 'denied', '20000000-0000-0000-0000-000000000002', '', NULL, 'SYNTHETIC', now(), '00000000-0000-0000-0000-0000000000a2', NULL, '00000000-0000-0000-0000-0000000000a7', '00000000-0000-0000-0000-0000000000a3', NULL);
INSERT INTO financial_reservations (id, currency, reserved_amount, state, budget_period_start, budget_period_end, created_at, state_updated_at, admission_decision_id, organization_id, policy_version_id, product_id, tariff_id)
VALUES ('00000000-0000-0000-0000-0000000000b0', 'USD', 1.0000000000, 'reserved', now(), now() + interval '30 days', now(), now(), '00000000-0000-0000-0000-0000000000a8', '00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-0000000000a5', '00000000-0000-0000-0000-0000000000a3', '00000000-0000-0000-0000-0000000000a6');
INSERT INTO financial_settlement_evidence (id, settlement_id, settlement_payload_hash, evidence_id, evidence_class, provider_request_id, source_owner, retention_classification, payload_hash, captured_at, created_at, organization_id, reservation_id)
VALUES ('00000000-0000-0000-0000-0000000000b1', '30000000-0000-0000-0000-000000000001', repeat('e', 64), '40000000-0000-0000-0000-000000000001', 'D', '', 'harness', 'synthetic', repeat('f', 64), now(), now(), '00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-0000000000b0');
INSERT INTO financial_audit_events (id, event_type, actor_reference, correlation_id, entity_type, entity_id, payload_hash, metadata, created_at, organization_id)
VALUES ('00000000-0000-0000-0000-0000000000b2', 'synthetic', 'harness', NULL, 'reservation', '00000000-0000-0000-0000-0000000000b0', repeat('g', 64), '{}', now(), '00000000-0000-0000-0000-0000000000a1');
SQL

# S3 removes the runtime role's former direct decision-read grant.  This is
# stronger than a tenant-filtered result: even a caller-supplied tenant GUC
# cannot retrieve financial decisions outside the reviewed operation path.
if psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 -c "SET ROLE adminapps_financial_runtime; SET app.tenant_id = '00000000-0000-0000-0000-0000000000a1'; SELECT count(*) FROM financial_admission_decisions;" >/dev/null 2>&1; then
  echo 'runtime direct financial decision read unexpectedly succeeded' >&2
  exit 1
fi
if psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 -c "SET ROLE adminapps_financial_runtime; SELECT count(*) FROM financial_admission_decisions;" >/dev/null 2>&1; then
  echo 'runtime no-context financial decision read unexpectedly succeeded' >&2
  exit 1
fi

if psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 -c "SET ROLE adminapps_financial_runtime; SET app.tenant_id = '00000000-0000-0000-0000-0000000000a1'; UPDATE financial_admission_decisions SET denial_code = 'forged' WHERE id = '00000000-0000-0000-0000-0000000000a8';" >/dev/null 2>&1; then
  echo 'runtime UPDATE unexpectedly succeeded' >&2
  exit 1
fi
if psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 -c "DELETE FROM financial_audit_events WHERE id = '00000000-0000-0000-0000-0000000000b2';" >/dev/null 2>&1; then
  echo 'append-only audit DELETE unexpectedly succeeded' >&2
  exit 1
fi
if psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 -c "UPDATE financial_audit_events SET event_type = 'forged' WHERE id = '00000000-0000-0000-0000-0000000000b2';" >/dev/null 2>&1; then
  echo 'append-only audit UPDATE unexpectedly succeeded' >&2
  exit 1
fi
if psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 -c "UPDATE financial_reservations SET currency = 'EUR' WHERE id = '00000000-0000-0000-0000-0000000000b0';" >/dev/null 2>&1; then
  echo 'unguarded reservation mutation unexpectedly succeeded' >&2
  exit 1
fi

role_invariants="$(psql -At -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -c "SELECT count(*) FROM pg_roles WHERE rolname IN ('adminapps_financial_migration', 'adminapps_financial_runtime', 'adminapps_financial_producer', 'adminapps_financial_audit', 'adminapps_financial_reconciliation') AND NOT rolsuper AND NOT rolbypassrls AND NOT rolinherit;")"
if [ "$role_invariants" != '5' ]; then
  echo "role hardening failed: expected 5 roles, got [$role_invariants]" >&2
  exit 1
fi

security_configuration="$(psql -At -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -c "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace JOIN pg_roles r ON r.oid = c.relowner WHERE n.nspname = 'public' AND c.relname LIKE 'financial_%' AND c.relkind = 'r' AND c.relrowsecurity AND c.relforcerowsecurity AND r.rolname = 'adminapps_financial_migration';")"
if [ "$security_configuration" != '12' ]; then
  echo "RLS/ownership configuration failed: expected 12 protected financial tables, got [$security_configuration]" >&2
  exit 1
fi

producer_privileges="$(psql -At -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -c "SELECT count(*) FROM information_schema.role_table_grants WHERE grantee = 'adminapps_financial_producer' AND table_schema = 'public' AND table_name LIKE 'financial_%';")"
if [ "$producer_privileges" != '0' ]; then
  echo "producer role unexpectedly has direct financial table privileges" >&2
  exit 1
fi

if psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 -c "UPDATE financial_producer_registration_events SET reason_code = 'forged' WHERE id = '00000000-0000-0000-0000-0000000000c1';" >/dev/null 2>&1; then
  echo 'producer registration lifecycle evidence UPDATE unexpectedly succeeded' >&2
  exit 1
fi
if psql -h "$financial_s1_socket" -p "$financial_s1_port" -d "$financial_s1_db" -v ON_ERROR_STOP=1 -c "DELETE FROM financial_permission_audit_events WHERE id = '00000000-0000-0000-0000-0000000000c2';" >/dev/null 2>&1; then
  echo 'financial permission audit DELETE unexpectedly succeeded' >&2
  exit 1
fi

echo 'ADMINAPPS_FINANCIAL_S1_POSTGRES_VERIFICATION_PASS'
echo 'RLS: all 12 financial tables are FORCE RLS and owned by the migration role; the runtime role has no direct decision read path, including with a forged tenant GUC; producer has no direct table privileges.'
echo 'Runtime mutation, immutable mutation, lifecycle/audit mutation, and unguarded reservation mutation were denied.'
echo 'Cleanup: temporary PostgreSQL cluster will be removed by the exit trap.'
