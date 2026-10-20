"""Restricted PostgreSQL admission boundary for the S3 runtime role.

The runtime principal has no direct write grant to financial evidence or budget
tables.  It can only execute this reviewed function.  The function owner is a
NOLOGIN, NOINHERIT, NOBYPASSRLS role with the minimum object grants needed for
one admission transaction; it is neither a table owner nor a runtime member.
"""

from django.db import migrations


FUNCTION_OWNER = 'adminapps_financial_admission'


def install_runtime_admission_boundary(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'adminapps_financial_admission') THEN
                RAISE EXCEPTION 'required S3 admission role adminapps_financial_admission is not provisioned';
              END IF;
              IF EXISTS (
                SELECT 1 FROM pg_roles
                 WHERE rolname = 'adminapps_financial_admission'
                   AND (rolsuper OR rolbypassrls OR rolinherit OR rolcanlogin)
              ) THEN
                RAISE EXCEPTION 'S3 admission role must be NOLOGIN, NOSUPERUSER, NOBYPASSRLS and NOINHERIT';
              END IF;
            END $$;

            REVOKE ALL ON TABLE public.financial_admission_decisions,
                                      public.financial_reservations,
                                      public.financial_audit_events,
                                      public.financial_budget_scopes
              FROM adminapps_financial_runtime;
            REVOKE INSERT ON TABLE public.financial_settlement_evidence,
                                         public.financial_resolution_history,
                                         public.financial_producer_registrations,
                                         public.financial_producer_registration_events,
                                         public.financial_permission_audit_events
              FROM adminapps_financial_runtime;

            GRANT USAGE ON SCHEMA public TO adminapps_financial_admission, adminapps_financial_runtime;
            GRANT SELECT ON TABLE public.financial_producer_registrations,
                                  public.financial_producer_registration_events,
                                  public.financial_policies,
                                  public.financial_policy_versions,
                                  public.financial_verified_tariffs,
                                  public.financial_budget_scopes,
                                  public.financial_admission_decisions,
                                  public.financial_reservations
              TO adminapps_financial_admission;
            GRANT INSERT ON TABLE public.financial_admission_decisions,
                                  public.financial_reservations,
                                  public.financial_audit_events
              TO adminapps_financial_admission;
            GRANT UPDATE (reserved_exposure, reserved_request_count)
              ON TABLE public.financial_budget_scopes TO adminapps_financial_admission;
            -- PostgreSQL requires UPDATE privilege for the reviewed row locks
            -- below.  This NOLOGIN function owner has no direct caller path;
            -- the function itself performs no updates to these evidence and
            -- policy records.
            GRANT UPDATE ON TABLE public.financial_producer_registrations,
                                  public.financial_policy_versions,
                                  public.financial_verified_tariffs
              TO adminapps_financial_admission;
            GRANT SELECT ON TABLE public.organizations,
                                  public.product_systems,
                                  public.organization_product_entitlements,
                                  public.subscriptions
              TO adminapps_financial_admission;

            -- S2 authentication is still performed by the existing hashed-key
            -- verifier.  These central, non-tenant registration reads contain
            -- no financial decision/evidence access.
            GRANT SELECT ON TABLE public.integration_api_keys,
                                  public.financial_producer_registrations,
                                  public.financial_producer_registration_events
              TO adminapps_financial_runtime;

            CREATE POLICY financial_admission_owner_producer_read
              ON public.financial_producer_registrations FOR ALL
              TO adminapps_financial_admission USING (true) WITH CHECK (true);
            CREATE POLICY financial_admission_owner_lifecycle_read
              ON public.financial_producer_registration_events FOR SELECT
              TO adminapps_financial_admission USING (true);
            -- Registration identity is central (not tenant financial data) and
            -- is needed by the existing S2 hashed-key verifier before it can
            -- invoke the admission function.  Runtime receives no policy for
            -- tenant decision, reservation, audit, tariff, or budget rows.
            CREATE POLICY financial_runtime_producer_read
              ON public.financial_producer_registrations FOR SELECT
              TO adminapps_financial_runtime USING (true);
            CREATE POLICY financial_runtime_lifecycle_read
              ON public.financial_producer_registration_events FOR SELECT
              TO adminapps_financial_runtime USING (true);
            CREATE POLICY financial_admission_owner_policy_read
              ON public.financial_policies FOR SELECT
              TO adminapps_financial_admission USING (true);
            CREATE POLICY financial_admission_owner_policy_version_read
              ON public.financial_policy_versions FOR ALL
              TO adminapps_financial_admission USING (true) WITH CHECK (true);
            CREATE POLICY financial_admission_owner_tariff_read
              ON public.financial_verified_tariffs FOR ALL
              TO adminapps_financial_admission USING (true) WITH CHECK (true);
            CREATE POLICY financial_admission_owner_budget_all
              ON public.financial_budget_scopes FOR ALL
              TO adminapps_financial_admission USING (true) WITH CHECK (true);
            CREATE POLICY financial_admission_owner_decision_all
              ON public.financial_admission_decisions FOR ALL
              TO adminapps_financial_admission USING (true) WITH CHECK (true);
            CREATE POLICY financial_admission_owner_reservation_all
              ON public.financial_reservations FOR ALL
              TO adminapps_financial_admission USING (true) WITH CHECK (true);
            CREATE POLICY financial_admission_owner_audit_all
              ON public.financial_audit_events FOR ALL
              TO adminapps_financial_admission USING (true) WITH CHECK (true);

            CREATE OR REPLACE FUNCTION public.financial_guard_budget_scope_update()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
              IF current_user <> 'adminapps_financial_admission' THEN
                RAISE EXCEPTION USING ERRCODE = '42501',
                  MESSAGE = 'financial budget changes require the S3 admission boundary';
              END IF;
              IF (to_jsonb(NEW) - 'reserved_exposure' - 'reserved_request_count')
                   IS DISTINCT FROM (to_jsonb(OLD) - 'reserved_exposure' - 'reserved_request_count') THEN
                RAISE EXCEPTION USING ERRCODE = '55000',
                  MESSAGE = 'only S3 reservation counters may change during admission';
              END IF;
              RETURN NEW;
            END;
            $$;

            CREATE OR REPLACE FUNCTION public.financial_admit_reserve(
              p_registration_id uuid, p_organization_id uuid, p_product_id uuid,
              p_invocation_id uuid, p_correlation_id uuid, p_material_hash text,
              p_environment text, p_provider text, p_model_identifier text,
              p_max_input_tokens bigint, p_max_output_tokens bigint,
              p_decision_id uuid, p_reservation_id uuid
            ) RETURNS TABLE (
              decision_id uuid, decision_state text, denial_code text,
              reservation_id uuid, currency text, reserved_amount numeric, replayed boolean
            ) LANGUAGE plpgsql SECURITY DEFINER
              SET search_path = pg_catalog, public AS $$
            DECLARE
              v_registration public.financial_producer_registrations%ROWTYPE;
              v_policy public.financial_policy_versions%ROWTYPE;
              v_tariff public.financial_verified_tariffs%ROWTYPE;
              v_scope public.financial_budget_scopes%ROWTYPE;
              v_existing public.financial_admission_decisions%ROWTYPE;
              v_amount numeric(20,10);
              v_denial text := NULL;
              v_scope_count integer := 0;
              v_now timestamptz := clock_timestamp();
            BEGIN
              -- A stable identity lock converts concurrent duplicate calls into
              -- a replay, rather than exposing a unique-constraint race.
              PERFORM pg_advisory_xact_lock(hashtext(concat_ws(':', p_registration_id, p_organization_id, p_product_id, p_invocation_id)));

              SELECT * INTO v_existing FROM public.financial_admission_decisions
               WHERE producer_registration_id = p_registration_id
                 AND organization_id = p_organization_id AND product_id = p_product_id
                 AND invocation_id = p_invocation_id;
              IF FOUND THEN
                IF v_existing.material_request_hash <> p_material_hash THEN
                  RETURN QUERY SELECT v_existing.id, 'conflict'::text, 'IDEMPOTENCY_CONFLICT'::text,
                    NULL::uuid, v_existing.currency, v_existing.reserved_amount, false;
                  RETURN;
                END IF;
                RETURN QUERY SELECT v_existing.id, v_existing.decision_state::text, v_existing.denial_code::text,
                  r.id, v_existing.currency::text, v_existing.reserved_amount, true
                  FROM public.financial_reservations r WHERE r.admission_decision_id = v_existing.id
                  UNION ALL
                  SELECT v_existing.id, v_existing.decision_state::text, v_existing.denial_code::text,
                    NULL::uuid, v_existing.currency::text, v_existing.reserved_amount, true
                  WHERE NOT EXISTS (SELECT 1 FROM public.financial_reservations r WHERE r.admission_decision_id = v_existing.id);
                RETURN;
              END IF;

              SELECT * INTO v_registration FROM public.financial_producer_registrations
               WHERE id = p_registration_id FOR UPDATE;
              IF NOT FOUND OR v_registration.environment <> p_environment
                 OR NOT (v_registration.permitted_product_ids ? p_product_id::text)
                 OR NOT (v_registration.permitted_operations ? 'admit_reserve')
                 OR (SELECT lifecycle_state FROM public.financial_producer_registration_events
                       WHERE registration_id = p_registration_id ORDER BY created_at DESC, id DESC LIMIT 1) <> 'active' THEN
                v_denial := 'PRODUCER_INACTIVE';
              ELSIF NOT EXISTS (SELECT 1 FROM public.organizations WHERE id = p_organization_id AND status = 'active')
                 OR NOT EXISTS (SELECT 1 FROM public.product_systems WHERE id = p_product_id AND status IN ('active', 'beta'))
                 OR NOT EXISTS (
                   SELECT 1 FROM public.organization_product_entitlements e
                    JOIN public.product_systems p ON p.id = e.product_id
                    LEFT JOIN public.subscriptions s ON s.id = COALESCE(e.subscription_id, (SELECT subscription_id FROM public.organizations WHERE id = p_organization_id))
                   WHERE e.organization_id = p_organization_id AND e.product_id = p_product_id
                     AND e.enabled AND e.status IN ('active', 'trial')
                     AND (e.ends_at IS NULL OR e.ends_at > v_now)
                     AND (NOT p.billing_enabled OR e.status = 'trial' OR s.status IN ('active', 'trial'))
                 ) THEN
                v_denial := 'ENTITLEMENT_DENIED';
              ELSIF p_max_input_tokens < 0 OR p_max_output_tokens < 0 THEN
                v_denial := 'INPUT_BOUND_INVALID';
              ELSE
                SELECT pv.* INTO v_policy FROM public.financial_policy_versions pv
                  JOIN public.financial_policies fp ON fp.id = pv.policy_id
                 WHERE fp.organization_id = p_organization_id AND pv.state = 'approved'
                   AND pv.effective_from <= v_now AND (pv.effective_until IS NULL OR pv.effective_until > v_now)
                 ORDER BY pv.id LIMIT 2 FOR UPDATE OF pv;
                IF NOT FOUND OR (SELECT count(*) FROM public.financial_policy_versions pv JOIN public.financial_policies fp ON fp.id = pv.policy_id WHERE fp.organization_id = p_organization_id AND pv.state = 'approved' AND pv.effective_from <= v_now AND (pv.effective_until IS NULL OR pv.effective_until > v_now)) <> 1 THEN
                  v_denial := 'FINANCIAL_POLICY_MISSING';
                ELSIF v_policy.allowed_provider <> p_provider OR v_policy.allowed_model <> p_model_identifier THEN
                  v_denial := 'MODEL_NOT_ALLOWED';
                ELSIF v_policy.max_input_tokens IS NULL OR p_max_input_tokens > v_policy.max_input_tokens THEN
                  v_denial := 'INPUT_BOUND_EXCEEDED';
                ELSIF v_policy.max_output_tokens IS NULL OR p_max_output_tokens > v_policy.max_output_tokens THEN
                  v_denial := 'OUTPUT_BOUND_EXCEEDED';
                ELSE
                  SELECT * INTO v_tariff FROM public.financial_verified_tariffs
                   WHERE provider = p_provider AND model_identifier = p_model_identifier AND state = 'verified'
                     AND effective_from IS NOT NULL AND effective_from <= v_now
                     AND (effective_until IS NULL OR effective_until > v_now)
                   ORDER BY id LIMIT 1 FOR UPDATE;
                  IF NOT FOUND OR (SELECT count(*) FROM public.financial_verified_tariffs WHERE provider = p_provider AND model_identifier = p_model_identifier AND state = 'verified' AND effective_from IS NOT NULL AND effective_from <= v_now AND (effective_until IS NULL OR effective_until > v_now)) <> 1 THEN
                    v_denial := 'TARIFF_UNAVAILABLE';
                  ELSIF v_policy.currency <> v_tariff.currency THEN
                    v_denial := 'FX_POLICY_REQUIRED';
                  ELSE
                    v_amount := CASE v_policy.rounding_rule
                      WHEN 'half_up' THEN round((p_max_input_tokens * v_tariff.input_unit_cost / v_tariff.unit_size + p_max_output_tokens * v_tariff.output_unit_cost / v_tariff.unit_size)::numeric, v_policy.amount_precision)
                      WHEN 'down' THEN trunc((p_max_input_tokens * v_tariff.input_unit_cost / v_tariff.unit_size + p_max_output_tokens * v_tariff.output_unit_cost / v_tariff.unit_size)::numeric, v_policy.amount_precision)
                      WHEN 'up' THEN ceil((p_max_input_tokens * v_tariff.input_unit_cost / v_tariff.unit_size + p_max_output_tokens * v_tariff.output_unit_cost / v_tariff.unit_size)::numeric * power(10::numeric, v_policy.amount_precision)) / power(10::numeric, v_policy.amount_precision)
                      -- PostgreSQL has no banker-rounding primitive.  A tie is
                      -- rounded to the nearest even scaled integer.
                      WHEN 'half_even' THEN (
                        WITH x AS (SELECT (p_max_input_tokens * v_tariff.input_unit_cost / v_tariff.unit_size + p_max_output_tokens * v_tariff.output_unit_cost / v_tariff.unit_size)::numeric * power(10::numeric, v_policy.amount_precision) AS n),
                        y AS (SELECT trunc(n) AS base, n - trunc(n) AS fraction FROM x)
                        SELECT CASE WHEN fraction < 0.5 THEN base WHEN fraction > 0.5 THEN base + 1 WHEN mod(base, 2) = 0 THEN base ELSE base + 1 END / power(10::numeric, v_policy.amount_precision) FROM y
                      )
                      ELSE NULL
                    END;
                    IF v_amount IS NULL THEN
                      v_denial := 'POLICY_PRECISION_INVALID';
                    END IF;
                    IF v_denial IS NULL THEN
                    FOR v_scope IN
                      SELECT * FROM public.financial_budget_scopes
                       WHERE organization_id = p_organization_id AND policy_version_id = v_policy.id
                         AND period_start <= v_now AND period_end > v_now
                         AND ((scope_type = 'tenant_global' AND product_id IS NULL) OR (scope_type = 'tenant_product' AND product_id = p_product_id))
                       ORDER BY CASE scope_type WHEN 'tenant_global' THEN 0 ELSE 1 END, id FOR UPDATE
                    LOOP
                      v_scope_count := v_scope_count + 1;
                      IF (v_scope.request_limit IS NOT NULL AND v_scope.reserved_request_count >= v_scope.request_limit)
                         OR v_scope.limit_amount - (v_scope.reserved_exposure + v_scope.settled_exposure + v_scope.unresolved_exposure + v_scope.approved_liability) < v_amount THEN
                        v_denial := CASE WHEN v_scope.request_limit IS NOT NULL AND v_scope.reserved_request_count >= v_scope.request_limit THEN 'REQUEST_QUOTA_EXHAUSTED' ELSE 'BUDGET_EXHAUSTED' END;
                        EXIT;
                      END IF;
                    END LOOP;
                    IF v_scope_count = 0 OR NOT EXISTS (SELECT 1 FROM public.financial_budget_scopes WHERE organization_id = p_organization_id AND policy_version_id = v_policy.id AND scope_type = 'tenant_global' AND product_id IS NULL AND period_start <= v_now AND period_end > v_now) THEN
                      v_denial := 'GLOBAL_BUDGET_MISSING';
                    END IF;
                    END IF;
                  END IF;
                END IF;
              END IF;

              IF v_denial IS NOT NULL THEN
                INSERT INTO public.financial_admission_decisions (id, producer_registration_id, organization_id, product_id, invocation_id, material_request_hash, decision_state, correlation_id, currency, denial_code, created_at)
                VALUES (p_decision_id, p_registration_id, p_organization_id, p_product_id, p_invocation_id, p_material_hash, 'denied', p_correlation_id, '', v_denial, v_now);
                INSERT INTO public.financial_audit_events (id, organization_id, event_type, actor_reference, correlation_id, entity_type, entity_id, payload_hash, metadata, created_at)
                VALUES (p_reservation_id, p_organization_id, 'admission_denied', 'producer_registration:' || p_registration_id::text, p_correlation_id, 'admission_decision', p_decision_id, p_material_hash, jsonb_build_object('denial_code', v_denial), v_now);
                RETURN QUERY SELECT p_decision_id, 'denied'::text, v_denial::text, NULL::uuid, ''::text, NULL::numeric, false;
                RETURN;
              END IF;

              INSERT INTO public.financial_admission_decisions (id, producer_registration_id, organization_id, product_id, invocation_id, material_request_hash, decision_state, correlation_id, policy_version_id, tariff_id, currency, reserved_amount, denial_code, created_at)
              VALUES (p_decision_id, p_registration_id, p_organization_id, p_product_id, p_invocation_id, p_material_hash, 'reserved', p_correlation_id, v_policy.id, v_tariff.id, v_policy.currency, v_amount, '', v_now);
              INSERT INTO public.financial_reservations (id, admission_decision_id, organization_id, product_id, policy_version_id, tariff_id, currency, reserved_amount, state, budget_period_start, budget_period_end, created_at, state_updated_at)
              SELECT p_reservation_id, p_decision_id, p_organization_id, p_product_id, v_policy.id, v_tariff.id, v_policy.currency, v_amount, 'reserved', period_start, period_end, v_now, v_now
                FROM public.financial_budget_scopes WHERE organization_id = p_organization_id AND policy_version_id = v_policy.id AND scope_type = 'tenant_global' AND product_id IS NULL AND period_start <= v_now AND period_end > v_now LIMIT 1;
              UPDATE public.financial_budget_scopes SET reserved_exposure = reserved_exposure + v_amount, reserved_request_count = reserved_request_count + 1
               WHERE organization_id = p_organization_id AND policy_version_id = v_policy.id AND period_start <= v_now AND period_end > v_now
                 AND ((scope_type = 'tenant_global' AND product_id IS NULL) OR (scope_type = 'tenant_product' AND product_id = p_product_id));
              INSERT INTO public.financial_audit_events (id, organization_id, event_type, actor_reference, correlation_id, entity_type, entity_id, payload_hash, metadata, created_at)
              VALUES (md5(p_reservation_id::text || v_now::text)::uuid, p_organization_id, 'admission_reserved', 'producer_registration:' || p_registration_id::text, p_correlation_id, 'financial_reservation', p_reservation_id, p_material_hash, jsonb_build_object('synthetic_only', true), v_now);
              RETURN QUERY SELECT p_decision_id, 'reserved'::text, ''::text, p_reservation_id, v_policy.currency::text, v_amount, false;
            END;
            $$;
            ALTER FUNCTION public.financial_admit_reserve(uuid, uuid, uuid, uuid, uuid, text, text, text, text, bigint, bigint, uuid, uuid) OWNER TO adminapps_financial_admission;
            REVOKE ALL ON FUNCTION public.financial_admit_reserve(uuid, uuid, uuid, uuid, uuid, text, text, text, text, bigint, bigint, uuid, uuid) FROM PUBLIC;
            GRANT EXECUTE ON FUNCTION public.financial_admit_reserve(uuid, uuid, uuid, uuid, uuid, text, text, text, text, bigint, bigint, uuid, uuid) TO adminapps_financial_runtime;
            """
        )


def remove_runtime_admission_boundary(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('DROP FUNCTION IF EXISTS public.financial_admit_reserve(uuid, uuid, uuid, uuid, uuid, text, text, text, text, bigint, bigint, uuid, uuid)')


class Migration(migrations.Migration):
    dependencies = [('financial', '0004_s3_admission_controls')]
    operations = [migrations.RunPython(install_runtime_admission_boundary, remove_runtime_admission_boundary)]
