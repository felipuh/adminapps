"""PostgreSQL authority-write fence + transactional revocation outbox.

Prepared only: not applied by offline runners. Global IAM tables, restricted
central DB role only; consumers must have no direct table access.
"""
from django.db import migrations

# Relevant changes include both directions, so disable/enable and role A/B/A
# cannot restore an old session. High-volume telemetry is deliberately excluded.
WATCHES = [
    ('users', 'user', 'password,email,role,is_active,is_staff,is_superuser,organization_id,locked_until,must_change_password,password_changed_at,metadata'),
    ('user_organizations', 'membership', 'user_id,organization_id,role,is_active'),
    ('organizations', 'tenant', 'status,subscription_id'),
    ('users_groups', 'user', 'user_id,group_id'),
    ('users_user_permissions', 'user', 'user_id,permission_id'),
    ('auth_group_permissions', 'all', '*'),
    ('two_factor_auth', 'user', 'user_id,is_enabled,generation,secret_encrypted'),
    ('integration_sso_clients', 'client', 'client_id,audience,issuer,enabled,product_id,principal_id,token_family,algorithm,allowed_kids,credential_policy,contract_version'),
    ('integration_sso_clients_tenants', 'client_tenant', 'ssoclient_id,organization_id'),
    ('integration_api_keys', 'credential', 'status,is_active,credential_hash,credential_format,credential_id'),
    ('product_systems', 'product', 'code,status,billing_enabled,default_plan_id'),
    ('organization_product_entitlements', 'entitlement', 'organization_id,product_id,enabled,status,starts_at,ends_at,plan_id,subscription_id,scopes,modules_enabled'),
    ('subscriptions', 'all', '*'),
    ('plans', 'all', '*'),
]

FUNCTION = r"""
INSERT INTO sso_security_fence (id, enabled, generation, authority_epoch) VALUES (1, false, 0, 0) ON CONFLICT (id) DO NOTHING;
CREATE FUNCTION sso_revoke_authority() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE oldrow jsonb := '{}'::jsonb; newrow jsonb := '{}'::jsonb;
        changed boolean := false; field text; s record; version bigint;
        reason text := 'authority_' || TG_ARGV[0];
BEGIN
  IF TG_OP <> 'INSERT' THEN oldrow := to_jsonb(OLD); END IF;
  IF TG_OP <> 'DELETE' THEN newrow := to_jsonb(NEW); END IF;
  IF TG_OP <> 'UPDATE' OR TG_ARGV[1] = '*' THEN changed := true;
  ELSE
    FOREACH field IN ARRAY string_to_array(TG_ARGV[1], ',') LOOP
      IF oldrow->field IS DISTINCT FROM newrow->field THEN changed := true; END IF;
    END LOOP;
  END IF;
  IF NOT changed THEN RETURN NEW; END IF;
  -- Held until the authority mutation and its revocations/outbox all commit.
  UPDATE sso_security_fence SET authority_epoch = authority_epoch + 1 WHERE id = 1;
  IF NOT FOUND THEN RAISE EXCEPTION 'SSO authority unavailable'; END IF;
  FOR s IN SELECT x.*, c.client_id AS client_name FROM sso_sessions x
           JOIN integration_sso_clients c ON c.id = x.client_id
           WHERE x.state = 'active' AND CASE TG_ARGV[0]
      WHEN 'user' THEN x.user_id::text IN
          (COALESCE(oldrow->>'user_id',oldrow->>'id'), COALESCE(newrow->>'user_id',newrow->>'id'))
      WHEN 'membership' THEN (x.user_id::text = oldrow->>'user_id' AND x.tenant_id::text = oldrow->>'organization_id')
                            OR (x.user_id::text = newrow->>'user_id' AND x.tenant_id::text = newrow->>'organization_id')
      WHEN 'tenant' THEN x.tenant_id::text IN (oldrow->>'id',newrow->>'id')
      WHEN 'client' THEN x.client_id::text IN (oldrow->>'id',newrow->>'id')
      WHEN 'client_tenant' THEN (x.client_id::text = oldrow->>'ssoclient_id' AND x.tenant_id::text = oldrow->>'organization_id')
                            OR (x.client_id::text = newrow->>'ssoclient_id' AND x.tenant_id::text = newrow->>'organization_id')
      WHEN 'credential' THEN c.principal_id::text IN (oldrow->>'id',newrow->>'id')
      WHEN 'product' THEN c.product_id::text IN (oldrow->>'id',newrow->>'id')
      WHEN 'entitlement' THEN (x.tenant_id::text = oldrow->>'organization_id' AND c.product_id::text = oldrow->>'product_id')
                            OR (x.tenant_id::text = newrow->>'organization_id' AND c.product_id::text = newrow->>'product_id')
      ELSE true END
      ORDER BY x.id FOR UPDATE OF x
  LOOP
    UPDATE sso_security_fence SET generation = generation + 1 WHERE id = 1 RETURNING generation INTO version;
    UPDATE sso_sessions SET state = 'revoked', revoked_at = clock_timestamp(),
           revocation_reason = reason, generation = version, authority_version = version WHERE id = s.id;
    INSERT INTO sso_revocation_outbox
       (id, session_id, generation, client_id_snapshot, product, tenant_id_snapshot,
        reason, correlation_id, created_at, delivered_at, attempts, next_attempt_at)
    VALUES (md5(s.id::text || ':' || version::text)::uuid, s.id, version, s.client_name,
            s.product, s.tenant_id, reason, s.correlation_id, clock_timestamp(), NULL, 0, NULL)
    ON CONFLICT (session_id, generation) DO NOTHING;
  END LOOP;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION sso_session_monotonic() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Session history is immutable'; END IF;
  IF OLD.state = 'revoked' OR NEW.generation <= OLD.generation
     OR NEW.authority_version < OLD.authority_version
     OR ROW(NEW.id,NEW.user_id,NEW.client_id,NEW.tenant_id,NEW.product,NEW.authenticated_at,NEW.expires_at,
            NEW.role,NEW.authentication_methods,NEW.mfa_generation,NEW.mfa_challenge_digest,NEW.correlation_id)
       IS DISTINCT FROM
        ROW(OLD.id,OLD.user_id,OLD.client_id,OLD.tenant_id,OLD.product,OLD.authenticated_at,OLD.expires_at,
            OLD.role,OLD.authentication_methods,OLD.mfa_generation,OLD.mfa_challenge_digest,OLD.correlation_id)
  THEN RAISE EXCEPTION 'Invalid session transition'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER sso_session_monotonic BEFORE UPDATE OR DELETE ON sso_sessions
FOR EACH ROW EXECUTE FUNCTION sso_session_monotonic();
CREATE FUNCTION sso_fence_monotonic() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Security fence is permanent'; END IF;
  IF NEW.id <> OLD.id OR NEW.generation < OLD.generation OR NEW.authority_epoch < OLD.authority_epoch
  THEN RAISE EXCEPTION 'Invalid security fence transition'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER sso_fence_monotonic BEFORE UPDATE OR DELETE ON sso_security_fence
FOR EACH ROW EXECUTE FUNCTION sso_fence_monotonic();
"""

RESET = r"""
CREATE FUNCTION sso_activation_reset() RETURNS void LANGUAGE plpgsql AS $$
DECLARE s record; version bigint;
BEGIN
  UPDATE sso_security_fence SET authority_epoch = authority_epoch + 1 WHERE id = 1;
  FOR s IN SELECT x.*, c.client_id AS client_name FROM sso_sessions x
           JOIN integration_sso_clients c ON c.id = x.client_id WHERE x.state = 'active' ORDER BY x.id FOR UPDATE OF x
  LOOP
    UPDATE sso_security_fence SET generation = generation + 1 WHERE id = 1 RETURNING generation INTO version;
    UPDATE sso_sessions SET state='revoked', generation=version, authority_version=version,
           revoked_at=clock_timestamp(), revocation_reason='activation_reset' WHERE id=s.id;
    INSERT INTO sso_revocation_outbox
       (id,session_id,generation,client_id_snapshot,product,tenant_id_snapshot,reason,correlation_id,created_at,attempts)
    VALUES (md5(s.id::text || ':' || version::text)::uuid,s.id,version,s.client_name,s.product,s.tenant_id,
            'activation_reset',s.correlation_id,clock_timestamp(),0);
  END LOOP;
END $$;
SELECT sso_activation_reset();
UPDATE sso_security_fence SET enabled=true WHERE id=1;
"""

FORWARD = FUNCTION + '\n'.join(
    f"CREATE TRIGGER sso_authority_{table} BEFORE INSERT OR UPDATE OR DELETE ON {table} "
    f"FOR EACH ROW EXECUTE FUNCTION sso_revoke_authority('{scope}', '{fields}');"
    for table, scope, fields in WATCHES
) + RESET
REVERSE = 'SELECT sso_activation_reset(); UPDATE sso_security_fence SET enabled=false WHERE id=1; DROP FUNCTION sso_activation_reset();\n' + '\n'.join(f'DROP TRIGGER sso_authority_{table} ON {table};' for table, _, _ in WATCHES) + """
DROP FUNCTION sso_revoke_authority();
DROP TRIGGER sso_session_monotonic ON sso_sessions;
DROP FUNCTION sso_session_monotonic();
DROP TRIGGER sso_fence_monotonic ON sso_security_fence;
DROP FUNCTION sso_fence_monotonic();
"""


class Migration(migrations.Migration):
    dependencies = [('integration', '0009_ssorevocationoutbox_ssosecurityfence_ssosession_and_more'),
                    ('users', '0004_transactional_2fa'), ('products', '0003_productentitlementauditlog'),
                    ('subscriptions', '0002_alter_plan_modules_included')]
    operations = [migrations.RunSQL(FORWARD, REVERSE)]
