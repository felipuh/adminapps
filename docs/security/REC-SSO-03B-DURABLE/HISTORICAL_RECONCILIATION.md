# Reconciliación por método

69 métodos con fallo/error heredado, preservados. Tracebacks originales completos en historical-reconciliation.json y historical/*.log.

| Suite | Método | Clase | Sucesor / pendiente |
|---|---|---|---|
| historical-02 | test_api_key_required_and_invalid_denied | Fallo del entorno o fixture | LifecycleTests.test_missing_contract_fields_and_credentials |
| historical-02 | test_bad_signature_expiry_and_refresh_rejected | Fallo del entorno o fixture | LifecycleTests.test_signature_algorithm_and_kid; test_claim_matrix |
| historical-02 | test_deleted_membership | Fallo del entorno o fixture | LifecycleTests.test_deleted_identity_and_membership_denied |
| historical-02 | test_deleted_user | Fallo del entorno o fixture | LifecycleTests.test_deleted_identity_and_membership_denied |
| historical-02 | test_foreign_subscription_denies_candidate | Requisito pendiente de scopes o políticas comerciales | NONE / política comercial |
| historical-02 | test_foreign_tenant | Fallo del entorno o fixture | LifecycleTests.test_generation_authority_session_and_time_binding; test_tenant_user_membership_revocation |
| historical-02 | test_future_start_denies_candidate | Requisito pendiente de scopes o políticas comerciales | NONE / política comercial |
| historical-02 | test_invalid_identifiers | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix; test_generation_authority_session_and_time_binding |
| historical-02 | test_live_membership_revocation | Fallo del entorno o fixture | LifecycleTests.test_tenant_user_membership_revocation; test_aba_revocation_cannot_be_undone_by_role_restore |
| historical-02 | test_live_organization_revocation | Fallo del entorno o fixture | LifecycleTests.test_tenant_user_membership_revocation |
| historical-02 | test_live_user_revocation | Fallo del entorno o fixture | LifecycleTests.test_tenant_user_membership_revocation |
| historical-02 | test_missing_audience_is_rejected | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-02 | test_missing_issuer | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-02 | test_missing_subject | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-02 | test_missing_tenant | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-02 | test_trial_requires_subscription_candidate | Requisito pendiente de scopes o políticas comerciales | NONE / política comercial |
| historical-02 | test_valid_response_contract | Fallo del entorno o fixture | LifecycleTests.test_valid_contract_least_privilege |
| historical-02 | test_wrong_audience_is_rejected | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-02 | test_wrong_issuer | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-02 | test_entitlement_denial_and_allowed_products | Fallo del entorno o fixture | LifecycleTests.test_product_revocation_reloaded; test_valid_contract_least_privilege |
| historical-02 | test_product_revocation_reloaded | Fallo del entorno o fixture | LifecycleTests.test_product_revocation_reloaded |
| historical-02 | test_sso_2fa_enabled_never_issues_without_factor | Fallo del entorno o fixture | LifecycleTests.test_login_mfa_challenge_mints_no_session |
| historical-02 | test_viewer_and_auditor_never_receive_write_scope | Expectativa histórica sustituida | LifecycleTests.test_valid_contract_least_privilege (solo ausencia de scope genérico); autorización D NOT_EVIDENCED |
| historical-02 | test_write_scope_requires_entitlement | Expectativa histórica sustituida | LifecycleTests.test_valid_contract_least_privilege (solo ausencia de scope genérico); autorización D NOT_EVIDENCED |
| historical-03a-adminapps | test_api_key_required_and_invalid_denied | Fallo del entorno o fixture | LifecycleTests.test_missing_contract_fields_and_credentials |
| historical-03a-adminapps | test_bad_signature_expiry_and_refresh_rejected | Fallo del entorno o fixture | LifecycleTests.test_signature_algorithm_and_kid; test_claim_matrix |
| historical-03a-adminapps | test_deleted_membership | Fallo del entorno o fixture | LifecycleTests.test_deleted_identity_and_membership_denied |
| historical-03a-adminapps | test_deleted_user | Fallo del entorno o fixture | LifecycleTests.test_deleted_identity_and_membership_denied |
| historical-03a-adminapps | test_foreign_tenant | Fallo del entorno o fixture | LifecycleTests.test_generation_authority_session_and_time_binding; test_tenant_user_membership_revocation |
| historical-03a-adminapps | test_invalid_identifiers | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix; test_generation_authority_session_and_time_binding |
| historical-03a-adminapps | test_live_membership_revocation | Fallo del entorno o fixture | LifecycleTests.test_tenant_user_membership_revocation; test_aba_revocation_cannot_be_undone_by_role_restore |
| historical-03a-adminapps | test_live_organization_revocation | Fallo del entorno o fixture | LifecycleTests.test_tenant_user_membership_revocation |
| historical-03a-adminapps | test_live_user_revocation | Fallo del entorno o fixture | LifecycleTests.test_tenant_user_membership_revocation |
| historical-03a-adminapps | test_mfa_enrollment_invalidates_password_only_proof | Fallo del entorno o fixture | LifecycleTests.test_mfa_live_generation |
| historical-03a-adminapps | test_missing_issuer | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-03a-adminapps | test_missing_subject | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-03a-adminapps | test_missing_tenant | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-03a-adminapps | test_old_token_requires_new_auth | Fallo del entorno o fixture | LifecycleTests.test_signed_legacy_ch_proof_without_session_denied |
| historical-03a-adminapps | test_reset_disabled_or_foreign_generation_denied | Fallo del entorno o fixture | LifecycleTests.test_mfa_live_generation; test_mfa_disabled_and_missing_configuration_denied |
| historical-03a-adminapps | test_valid_mfa_proof | Fallo del entorno o fixture | LifecycleTests.test_mfa_live_generation; test_verify_valid_and_postconsume_failure_no_restoration |
| historical-03a-adminapps | test_valid_response_contract | Fallo del entorno o fixture | LifecycleTests.test_valid_contract_least_privilege |
| historical-03a-adminapps | test_verify_complete_contract_and_generation | Fallo del entorno o fixture | LifecycleTests.test_verify_valid_and_postconsume_failure_no_restoration |
| historical-03a-adminapps | test_verify_foreign_context_does_not_consume | Fallo del entorno o fixture | LifecycleTests.test_challenge_binding_before_irreversible_consume |
| historical-03a-adminapps | test_wrong_issuer | Fallo del entorno o fixture | LifecycleTests.test_claim_matrix |
| historical-03a-adminapps | test_entitlement_denial_and_allowed_products | Fallo del entorno o fixture | LifecycleTests.test_product_revocation_reloaded; test_valid_contract_least_privilege |
| historical-03a-adminapps | test_product_revocation_reloaded | Fallo del entorno o fixture | LifecycleTests.test_product_revocation_reloaded |
| historical-03a-adminapps | test_sso_2fa_enabled_never_issues_without_factor | Fallo del entorno o fixture | LifecycleTests.test_login_mfa_challenge_mints_no_session |
| historical-03a-isosmart | test_challenge_is_not_session | Fallo del entorno o fixture | ConsumerBTests.test_challenge_and_verify_flow |
| historical-03a-isosmart | test_complete_central_login | Fallo del entorno o fixture | ConsumerBTests.test_valid_login_real_signature_before_projection |
| historical-03a-isosmart | test_cross_tenant_binding_rejected | Fallo del entorno o fixture | ConsumerBTests.test_tenant_switch_and_uuid_binding |
| historical-03a-isosmart | test_current_session_live_revocation_and_role | Fallo del entorno o fixture | ConsumerBTests.test_session_profile_role_tenant_and_subject; test_denial_does_not_allow_reuse_cached_authority |
| historical-03a-isosmart | test_failed_binding_mints_no_local_token | Fallo del entorno o fixture | ConsumerBTests.test_tenant_switch_and_uuid_binding; test_expired_central_never_mints_local |
| historical-03a-isosmart | test_missing_profile_or_schema_fails_sanitized | Fallo del entorno o fixture | ConsumerBTests.test_schema_failure_sanitized |
| historical-03a-isosmart | test_old_refresh_never_issues_access | Fallo del entorno o fixture | ConsumerBTests.test_old_generic_tokens_never_become_local; test_central_generation_binding_and_legacy_rejection |
| historical-03a-isosmart | test_owner_policy_cannot_be_bypassed | Fallo del entorno o fixture | ConsumerBTests.test_owner_policy |
| historical-03a-isosmart | test_refresh_bound_by_central_expiry | Fallo del entorno o fixture | ConsumerBTests.test_local_pair_is_tenant_subject_and_expiry_bound; test_refresh_live_authority_and_revocation |
| historical-03a-isosmart | test_transport_and_json_errors_are_sanitized | Fallo del entorno o fixture | ConsumerBTests.test_transport_and_json_errors_are_sanitized |
| historical-03a-isosmart | test_verify_totp_or_backup_through_central | Fallo del entorno o fixture | ConsumerBTests.test_challenge_and_verify_flow |
| historical-03a-medsupplier | test_challenge_is_not_session | Fallo del entorno o fixture | ConsumerBTests.test_challenge_and_verify_flow |
| historical-03a-medsupplier | test_complete_central_login | Fallo del entorno o fixture | ConsumerBTests.test_valid_login_real_signature_before_projection |
| historical-03a-medsupplier | test_cross_tenant_binding_rejected | Fallo del entorno o fixture | ConsumerBTests.test_tenant_switch_and_uuid_binding |
| historical-03a-medsupplier | test_current_session_live_revocation_and_role | Fallo del entorno o fixture | ConsumerBTests.test_session_profile_role_tenant_and_subject; test_denial_does_not_allow_reuse_cached_authority |
| historical-03a-medsupplier | test_failed_binding_mints_no_local_token | Fallo del entorno o fixture | ConsumerBTests.test_tenant_switch_and_uuid_binding; test_expired_central_never_mints_local |
| historical-03a-medsupplier | test_missing_profile_or_schema_fails_sanitized | Fallo del entorno o fixture | ConsumerBTests.test_schema_failure_sanitized |
| historical-03a-medsupplier | test_old_refresh_never_issues_access | Fallo del entorno o fixture | ConsumerBTests.test_old_generic_tokens_never_become_local; test_central_generation_binding_and_legacy_rejection |
| historical-03a-medsupplier | test_owner_policy_cannot_be_bypassed | Fallo del entorno o fixture | ConsumerBTests.test_owner_policy |
| historical-03a-medsupplier | test_refresh_bound_by_central_expiry | Fallo del entorno o fixture | ConsumerBTests.test_local_pair_is_tenant_subject_and_expiry_bound; test_refresh_live_authority_and_revocation |
| historical-03a-medsupplier | test_transport_and_json_errors_are_sanitized | Fallo del entorno o fixture | ConsumerBTests.test_transport_and_json_errors_are_sanitized |
| historical-03a-medsupplier | test_verify_totp_or_backup_through_central | Fallo del entorno o fixture | ConsumerBTests.test_challenge_and_verify_flow |

Los fixtures A centrales no proporcionan el principal/contrato C/H; los de consumidores carecen de keyrings RSA. El rechazo previo no prueba por sí solo el invariante original. Los sucesores ejecutan endpoints/codec y autoridad simulada con el contrato vigente.

Los tres candidatos comerciales permanecen FAIL: trial sin suscripción, starts_at futuro, vinculación de suscripción ajena. Subscription no tiene propietario tenant inequívoco; Organization y Entitlement lo referencian. No se cambió política comercial ni se adjudicó compatibilidad. Severidad HIGH y bloqueo de autorización comercial/producción; no impide implementar revocación local. Scopes D sigue abierto.

Regresiones funcionales reales del alcance B corregidas: logout sin revocación central; replay de refresh MedSupplier; carrera check-then-write en refresh ISO. Pruebas: LifecycleTests.test_logout_idempotent_and_old_signed_proof_denied, test_rotation_single_use_and_no_extension, test_serialized_concurrent_rotation_logic; ConsumerBTests.test_refresh_live_authority_and_revocation. La concurrencia SQL real sigue pendiente.

C/H intacta después de B: sus fixtures carecen ahora de fence/sesión/generación. Se ejecuta íntegra y se preservan FAIL/ERROR. ConsumerBTests hereda las pruebas C/H; añade los campos B al fixture, y sustituye únicamente el contrato de refresh por rotación central. LifecycleTests hereda C/H y añade ORM simulado B. Cambios de expectativas en sucesores se limitan a JWT compacto (proyección viva), emisión con registro durable y MFA enlazado; ninguna suite histórica fue editada.

## C/H intacta contra implementación B: mapa por método

| Suite | Método | Causa | Sucesor |
|---|---|---|---|
| ch-adminapps | test_challenge_binding_before_irreversible_consume | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_challenge_binding_before_irreversible_consume |
| ch-adminapps | test_login_real_emission_and_tenant | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_login_real_emission_and_tenant |
| ch-adminapps | test_login_response_does_not_disclose_other_tenants | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_login_response_does_not_disclose_other_tenants |
| ch-adminapps | test_verify_valid_and_postconsume_failure_no_restoration | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_verify_valid_and_postconsume_failure_no_restoration |
| ch-adminapps | test_claim_matrix | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_claim_matrix |
| ch-adminapps | test_coordinated_cross_product_consumers | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_coordinated_cross_product_consumers |
| ch-adminapps | test_impersonation_both_directions | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_impersonation_both_directions |
| ch-adminapps | test_mfa_live_generation | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_mfa_live_generation |
| ch-adminapps | test_missing_contract_fields_and_credentials | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_missing_contract_fields_and_credentials |
| ch-adminapps | test_registry_rejects_unapproved_crypto | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_registry_rejects_unapproved_crypto |
| ch-adminapps | test_signature_algorithm_and_kid | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_signature_algorithm_and_kid |
| ch-adminapps | test_tenant_user_membership_revocation | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_tenant_user_membership_revocation |
| ch-adminapps | test_unconfigured_or_database_down_sanitized | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_unconfigured_or_database_down_sanitized |
| ch-adminapps | test_unknown_disabled_revoked_clients | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_unknown_disabled_revoked_clients |
| ch-adminapps | test_valid_contract_least_privilege | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_valid_contract_least_privilege |
| ch-adminapps | test_wrong_credential_binding | Fixture C/H no tiene fence/epoch/sesión persistente; emisión y cliente fallan cerrados. | LifecycleTests.test_wrong_credential_binding |
| ch-isosmart | test_challenge_and_verify_flow | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_challenge_and_verify_flow |
| ch-isosmart | test_local_as_central_and_central_as_local | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_local_as_central_and_central_as_local |
| ch-isosmart | test_local_header_algorithm_and_key_restrictions | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_local_header_algorithm_and_key_restrictions |
| ch-isosmart | test_local_pair_is_tenant_subject_and_expiry_bound | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_local_pair_is_tenant_subject_and_expiry_bound |
| ch-isosmart | test_middleware_uses_verified_local_family | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_middleware_uses_verified_local_family |
| ch-isosmart | test_refresh_live_authority_and_revocation | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_refresh_live_authority_and_revocation |
| ch-isosmart | test_refresh_with_expired_embedded_proof_is_denied | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_refresh_with_expired_embedded_proof_is_denied |
| ch-isosmart | test_schema_failure_sanitized | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_schema_failure_sanitized |
| ch-isosmart | test_session_profile_role_tenant_and_subject | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_session_profile_role_tenant_and_subject |
| ch-isosmart | test_session_transport_preserved | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_session_transport_preserved |
| ch-isosmart | test_valid_login_real_signature_before_projection | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_valid_login_real_signature_before_projection |
| ch-medsupplier | test_challenge_and_verify_flow | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_challenge_and_verify_flow |
| ch-medsupplier | test_local_as_central_and_central_as_local | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_local_as_central_and_central_as_local |
| ch-medsupplier | test_local_header_algorithm_and_key_restrictions | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_local_header_algorithm_and_key_restrictions |
| ch-medsupplier | test_local_pair_is_tenant_subject_and_expiry_bound | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_local_pair_is_tenant_subject_and_expiry_bound |
| ch-medsupplier | test_middleware_uses_verified_local_family | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_middleware_uses_verified_local_family |
| ch-medsupplier | test_refresh_live_authority_and_revocation | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_refresh_live_authority_and_revocation |
| ch-medsupplier | test_refresh_with_expired_embedded_proof_is_denied | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_refresh_with_expired_embedded_proof_is_denied |
| ch-medsupplier | test_schema_failure_sanitized | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_schema_failure_sanitized |
| ch-medsupplier | test_session_profile_role_tenant_and_subject | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_session_profile_role_tenant_and_subject |
| ch-medsupplier | test_session_transport_preserved | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_session_transport_preserved |
| ch-medsupplier | test_valid_login_real_signature_before_projection | Prueba C/H firmada sin lifecycle/sid/sg/av/auth_time; refresh anterior no consume autoridad central. | ConsumerBTests.test_valid_login_real_signature_before_projection |
