# Pruebas negativas de seguridad

Todas ejecutan el código real. ORM/transporte son dobles offline; RSA, serializers, vistas y verificadores son reales. No prueba HTTP/E2E. Los logs no guardan las pruebas JWT completas ni claves privadas.

| Caso | Resultado final | Evidencia (método) |
| --- | --- | --- |
| Cliente ISO solicita MedSupplier | DENY | AdminApps test_impersonation_both_directions |
| Cliente MedSupplier solicita ISO | DENY | AdminApps test_impersonation_both_directions |
| Principal válido declara otro client_id | DENY | AdminApps test_impersonation_both_directions |
| Credencial de otro principal/producto | DENY | AdminApps test_wrong_credential_binding |
| Audience incorrecta, múltiple o de forma incorrecta | DENY | test_claim_matrix / consumer test_foreign_product_audience_tenant_and_issuer |
| Audience ausente | DENY | test_claim_matrix |
| Issuer desconocido | DENY | test_claim_matrix |
| Firma alterada o clave equivocada | DENY | test_signature_algorithm_and_kid / consumer test_tampered_signature_denied_before_transport |
| Algoritmo none o HS256 | DENY | test_signature_algorithm_and_kid / consumer test_alg_none_hmac_unknown_kid |
| kid desconocido/ausente/no autorizado | DENY | test_signature_algorithm_and_kid / test_registry_rejects_unapproved_crypto |
| LOCAL presentado como CENTRAL | DENY | consumer test_local_as_central_and_central_as_local + coordinación |
| CENTRAL presentado como LOCAL | DENY | consumer test_local_as_central_and_central_as_local |
| Cliente deshabilitado/no registrado | DENY | test_unknown_disabled_revoked_clients |
| Principal deshabilitado/revocado/rotado | DENY | test_unknown_disabled_revoked_clients |
| Tenant incorrecto/deshabilitado/no permitido | DENY | test_tenant_user_membership_revocation / consumer test_tenant_switch_and_uuid_binding |
| Identidad sin vínculo UUID | DENY | consumer test_tenant_switch_and_uuid_binding / test_no_email_takeover_without_subject_binding |
| MFA requerido pero incompleto/generación anterior | DENY | test_mfa_live_generation / consumer test_challenge_and_verify_flow; REC-2FA-04 |
| Prueba central vencida | DENY | test_claim_matrix / consumer test_expired_central_never_mints_local |
| Configuración incompleta | DENY | test_unconfigured_or_database_down_sanitized / consumer test_missing_config_credentials_or_key_material |
| Cliente/tenant/MFA correctos | ALLOW, viewer conservado | test_mfa_live_generation + test_valid_contract_least_privilege + coordinación |
| Producto/audience/firma válidos | ALLOW, sin is_superuser ni producto ajeno | consumer test_local_pair_is_tenant_subject_and_expiry_bound + coordinación |
| Mismo material RSA central/local bajo kids diferentes | DENY | consumer test_central_and_local_keys_must_be_distinct |
| Introspección contradice claims firmadas | DENY | consumer test_introspection_disagreement_and_revocation |
| Refresh local vigente con prueba central vencida | DENY | consumer test_refresh_with_expired_embedded_proof_is_denied |
| Rotación de refresh | ALLOW limitado por exp central | consumer test_refresh_live_authority_and_revocation |
| Challenge de otro principal/producto/cliente | DENY antes del consumo | test_challenge_binding_before_irreversible_consume |
| Emisión falla después del consumo MFA | DENY, sin restauración del factor | test_verify_valid_and_postconsume_failure_no_restoration; servicio transaccional intacto |
| Lista de organizaciones ajenas en respuesta de login | EXCLUIDA | test_login_response_does_not_disclose_other_tenants |
| Bearer o sesión Django local para navegador ISO | DENY | ISO test_session_transport_preserved |
| Cookie ISO sin CSRF en escritura | DENY | ISO test_session_transport_preserved |

Logs finales: ch-adminapps.log (18 métodos), ch-isosmart.log (28), ch-medsupplier.log (28), mfa.log (21). Las filas no son conteos independientes de métodos: varios casos usan subtests. test-results.json conserva conteos y fallos históricos, sin convertirlos a verdes.
