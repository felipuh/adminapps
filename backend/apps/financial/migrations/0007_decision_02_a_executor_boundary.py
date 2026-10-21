"""Remove runtime admission access; expose only the executor capability boundary."""
from django.db import migrations


def install_executor_boundary(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            REVOKE ALL ON FUNCTION public.financial_admit_reserve(uuid, uuid, uuid, uuid, uuid, text, text, text, text, bigint, bigint, uuid, uuid)
              FROM PUBLIC, adminapps_financial_runtime, adminapps_financial_executor;
            GRANT USAGE ON SCHEMA public TO adminapps_financial_executor;

            CREATE OR REPLACE FUNCTION public.financial_admit_reserve_capability(
              p_capability_id uuid, p_issuer_id text, p_key_id text, p_capability_version smallint,
              p_grant_id uuid, p_grant_version integer, p_registration_id uuid,
              p_organization_id uuid, p_product_id uuid, p_invocation_id uuid,
              p_material_hash text, p_environment text, p_operation text,
              p_correlation_id uuid, p_provider text, p_model_identifier text,
              p_max_input_tokens bigint, p_max_output_tokens bigint
            ) RETURNS TABLE (
              decision_id uuid, decision_state text, denial_code text,
              reservation_id uuid, currency text, reserved_amount numeric, replayed boolean
            ) LANGUAGE plpgsql SECURITY DEFINER
              SET search_path = pg_catalog, public AS $$
            DECLARE
              v_grant public.financial_producer_tenant_grants%ROWTYPE;
              v_now timestamptz := clock_timestamp();
            BEGIN
              IF p_capability_version <> 1 OR p_operation <> 'admit_reserve' THEN
                RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'unsupported financial capability';
              END IF;
              SELECT * INTO v_grant FROM public.financial_producer_tenant_grants
               WHERE id = p_grant_id FOR UPDATE;
              IF NOT FOUND OR v_grant.state <> 'active' OR v_grant.version <> p_grant_version
                 OR v_grant.producer_registration_id <> p_registration_id
                 OR v_grant.organization_id <> p_organization_id OR v_grant.product_id <> p_product_id
                 OR v_grant.operation <> p_operation OR v_grant.environment <> p_environment
                 OR v_grant.effective_from > v_now
                 OR (v_grant.effective_until IS NOT NULL AND v_grant.effective_until <= v_now) THEN
                RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'producer tenant grant denied';
              END IF;
              INSERT INTO public.financial_invocation_ledger
                (id, capability_id, producer_registration_id, organization_id, product_id, grant_id,
                 invocation_id, material_request_hash, issuer_id, key_id, capability_version, created_at)
              VALUES
                (p_capability_id, p_capability_id, p_registration_id, p_organization_id, p_product_id, p_grant_id,
                 p_invocation_id, p_material_hash, p_issuer_id, p_key_id, p_capability_version, v_now)
              ON CONFLICT (producer_registration_id, organization_id, product_id, invocation_id) DO NOTHING;
              RETURN QUERY SELECT * FROM public.financial_admit_reserve(
                p_registration_id, p_organization_id, p_product_id, p_invocation_id, p_correlation_id,
                p_material_hash, p_environment, p_provider, p_model_identifier, p_max_input_tokens,
                p_max_output_tokens, md5(p_capability_id::text || ':decision')::uuid,
                md5(p_capability_id::text || ':reservation')::uuid
              );
            END;
            $$;
            ALTER FUNCTION public.financial_admit_reserve_capability(uuid, text, text, smallint, uuid, integer, uuid, uuid, uuid, uuid, text, text, text, uuid, text, text, bigint, bigint)
              OWNER TO adminapps_financial_admission;
            REVOKE ALL ON FUNCTION public.financial_admit_reserve_capability(uuid, text, text, smallint, uuid, integer, uuid, uuid, uuid, uuid, text, text, text, uuid, text, text, bigint, bigint)
              FROM PUBLIC, adminapps_financial_runtime;
            GRANT EXECUTE ON FUNCTION public.financial_admit_reserve_capability(uuid, text, text, smallint, uuid, integer, uuid, uuid, uuid, uuid, text, text, text, uuid, text, text, bigint, bigint)
              TO adminapps_financial_executor;
        """)


class Migration(migrations.Migration):
    dependencies = [('financial', '0006_decision_02_a_grants_and_ledger')]
    operations = [migrations.RunPython(install_executor_boundary, migrations.RunPython.noop)]
