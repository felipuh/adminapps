-- Dedicated IAM database only. No role names, passwords or connection defaults.
-- Run via psql -X -v ON_ERROR_STOP=1 -v runtime_role=... -v maintenance_role=...
-- as the maintenance owner, after migrations, with runtime connections stopped.
-- This is a restrictive authentication-service profile, not a grant policy for
-- every admin/product/financial endpoint. See SQL-RUNTIME-CONTRACT.md.
\set ON_ERROR_STOP on
\if :{?runtime_role}
\else
  \echo 'runtime_role is required'
  \quit 3
\endif
\if :{?maintenance_role}
\else
  \echo 'maintenance_role is required'
  \quit 3
\endif
BEGIN;
SELECT pg_catalog.set_config('adminapps.runtime_role', :'runtime_role', true),
       pg_catalog.set_config('adminapps.maintenance_role', :'maintenance_role', true);
SET LOCAL search_path = pg_catalog, public, pg_temp;
DO $policy$
DECLARE
  runtime_name text := current_setting('adminapps.runtime_role');
  maintenance_name text := current_setting('adminapps.maintenance_role');
  runtime_id oid; maintenance_id oid; item record; col record; name text;
  writable text[] := ARRAY[
    'users','user_sessions','two_factor_auth','two_factor_challenges',
    'user_organizations','sso_sessions'
  ];
  readable text[] := ARRAY[
    'organizations','organization_invitations','organization_settings',
    'organization_feature_flags','auth_permission','auth_group',
    'auth_group_permissions','users_groups','users_user_permissions',
    'django_content_type','integration_sso_clients',
    'integration_sso_clients_tenants','integration_api_keys','product_systems',
    'organization_product_entitlements','plans','subscriptions'
  ];
BEGIN
  SELECT oid INTO STRICT runtime_id FROM pg_roles WHERE rolname=runtime_name;
  SELECT oid INTO STRICT maintenance_id FROM pg_roles WHERE rolname=maintenance_name;
  IF current_user <> maintenance_name OR runtime_id=maintenance_id THEN
    RAISE EXCEPTION 'Connect as the separate maintenance owner';
  END IF;
  IF EXISTS (SELECT FROM pg_roles WHERE oid IN (runtime_id,maintenance_id)
      AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls))
     OR EXISTS (SELECT FROM pg_roles WHERE oid=maintenance_id AND rolcanlogin)
     OR NOT EXISTS (SELECT FROM pg_roles WHERE oid=runtime_id AND rolcanlogin)
     OR EXISTS (SELECT FROM pg_auth_members WHERE member=runtime_id OR roleid=runtime_id) THEN
    RAISE EXCEPTION 'Unsafe role attributes or runtime memberships (including SET ROLE)';
  END IF;
  IF EXISTS (SELECT FROM pg_stat_activity WHERE usesysid=runtime_id) THEN
    RAISE EXCEPTION 'Disconnect runtime sessions before provisioning (including old temporary namespaces)';
  END IF;
  IF EXISTS (SELECT FROM pg_class WHERE relowner=runtime_id)
     OR EXISTS (SELECT FROM pg_proc WHERE proowner=runtime_id)
     OR EXISTS (SELECT FROM pg_namespace WHERE nspowner=runtime_id)
     OR EXISTS (SELECT FROM pg_type WHERE typowner=runtime_id)
     OR EXISTS (SELECT FROM pg_database WHERE datdba=runtime_id) THEN
    RAISE EXCEPTION 'Runtime must not own database objects';
  END IF;
  IF (SELECT datdba FROM pg_database WHERE datname=current_database()) <> maintenance_id
     OR EXISTS (SELECT FROM pg_namespace
       WHERE nspname !~ '^pg_' AND nspname <> 'information_schema'
       AND (nspname <> 'public' OR nspowner NOT IN
           (maintenance_id, (SELECT oid FROM pg_roles WHERE rolname='pg_database_owner'))))
     OR EXISTS (SELECT FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
       WHERE n.nspname='public' AND c.relowner<>maintenance_id)
     OR EXISTS (SELECT FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
       WHERE n.nspname='public' AND (p.proowner<>maintenance_id OR p.prosecdef)) THEN
    RAISE EXCEPTION 'Requires dedicated public-schema IAM database owned by maintenance; no definer routines';
  END IF;
  IF EXISTS (SELECT FROM pg_class WHERE relnamespace='public'::regnamespace
       AND (relname LIKE 'financial_%' OR relkind IN ('v','m','f','p')))
     OR NOT EXISTS (SELECT FROM public.django_migrations m
       WHERE m.app='users' AND m.name='0006_sql_revocation_boundary') THEN
    RAISE EXCEPTION 'Unexpected schema or missing authority-retention migration';
  END IF;
  IF EXISTS (SELECT FROM pg_parameter_acl a, LATERAL aclexplode(a.paracl) x
       WHERE x.grantee IN (0,runtime_id)) THEN
    RAISE EXCEPTION 'Runtime/PUBLIC has explicit parameter privileges';
  END IF;
  IF (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
        WHERE c.relnamespace='public'::regnamespace
          AND c.relname IN ('user_sessions','sso_sessions','sso_security_fence','sso_revocation_outbox')
          AND t.tgname IN ('adminapps_retain_authority_delete','adminapps_retain_authority_truncate')
          AND t.tgenabled IN ('O','A')) <> 8 THEN
    RAISE EXCEPTION 'Authority-retention triggers missing or disabled';
  END IF;
  -- Rebuild privileges, including column ACLs (table REVOKE does not remove them).
  EXECUTE format('REVOKE ALL ON DATABASE %I FROM PUBLIC, %I',current_database(),runtime_name);
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO %I',current_database(),runtime_name);
  EXECUTE format('REVOKE ALL ON SCHEMA public FROM PUBLIC, %I',runtime_name);
  EXECUTE format('GRANT USAGE ON SCHEMA public TO %I',runtime_name);
  EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC, %I',runtime_name);
  FOR item IN SELECT c.oid,c.relname FROM pg_class c
      WHERE c.relnamespace='public'::regnamespace AND c.relkind='r' LOOP
    FOR col IN SELECT attname FROM pg_attribute
        WHERE attrelid=item.oid AND attnum>0 AND NOT attisdropped LOOP
      EXECUTE format('REVOKE ALL (%I) ON public.%I FROM PUBLIC, %I',
                     col.attname,item.relname,runtime_name);
    END LOOP;
  END LOOP;
  EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC, %I',runtime_name);
  EXECUTE format('REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM PUBLIC, %I',runtime_name);
  -- Future objects get no implicit runtime privileges. Reapply/review after DDL.
  FOREACH name IN ARRAY ARRAY['TABLES','SEQUENCES','FUNCTIONS'] LOOP
    EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I REVOKE ALL ON %s FROM PUBLIC, %I',
                   maintenance_name,name,runtime_name);
    EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public REVOKE ALL ON %s FROM PUBLIC, %I',
                   maintenance_name,name,runtime_name);
  END LOOP;
  FOREACH name IN ARRAY writable LOOP
    EXECUTE format('GRANT SELECT, INSERT, UPDATE ON public.%I TO %I',name,runtime_name);
  END LOOP;
  FOREACH name IN ARRAY readable LOOP
    EXECUTE format('GRANT SELECT ON public.%I TO %I',name,runtime_name);
  END LOOP;
  EXECUTE format('GRANT UPDATE ON public.organization_invitations TO %I',runtime_name);
  EXECUTE format('GRANT SELECT, INSERT ON public.user_activity_logs, public.two_factor_auth_logs, public.sso_revocation_outbox TO %I',runtime_name);
  EXECUTE format('GRANT SELECT ON public.sso_security_fence TO %I',runtime_name);
  EXECUTE format('GRANT UPDATE (generation, authority_epoch) ON public.sso_security_fence TO %I',runtime_name);
  EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON public.django_session TO %I',runtime_name);
  -- Only sequences backing a table with legitimate runtime INSERT.
  FOR item IN SELECT c.relname,a.attname FROM pg_class c
      JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
      WHERE c.relnamespace='public'::regnamespace AND c.relkind='r'
      AND has_table_privilege(runtime_id,c.oid,'INSERT') LOOP
    name := pg_get_serial_sequence(format('public.%I',item.relname),item.attname);
    IF name IS NOT NULL THEN
      EXECUTE format('GRANT USAGE ON SEQUENCE %s TO %I',name,runtime_name);
    END IF;
  END LOOP;
  IF has_database_privilege(runtime_id,current_database(),'CREATE')
     OR has_database_privilege(runtime_id,current_database(),'TEMP')
     OR has_schema_privilege(runtime_id,'public','CREATE') THEN
    RAISE EXCEPTION 'Unsafe effective namespace privileges';
  END IF;
END
$policy$;
COMMIT;
