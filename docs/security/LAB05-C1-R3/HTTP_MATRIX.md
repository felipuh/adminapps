# R3 HTTP acceptance matrix

All successful sessions come from the real ISO login endpoint. Invalid proofs are negative inputs only.

| Scenario | Method | Path | HTTP | No handler / no writes asserted |
|---|---|---|---:|---|
| anonymous_denied | GET | `/api/auth/me/` | 401 | Yes |
| login_without_csrf | POST | `/api/auth/login/` | 403 | Yes |
| legitimate_login_a_csrf | GET | `/api/auth/csrf/` | 200 | — |
| legitimate_login_a | POST | `/api/auth/login/` | 200 | — |
| real_central_introspection | POST | `/api/integration/sso/introspect/` | 200 | — |
| me_a | GET | `/api/auth/me/` | 200 | — |
| authorized_resource_create_a | POST | `/api/resources/` | 201 | — |
| shared_subject_login_b_csrf | GET | `/api/auth/csrf/` | 200 | — |
| shared_subject_login_b | POST | `/api/auth/login/` | 200 | — |
| shared_subject_me_b_no_elevation | GET | `/api/auth/me/` | 200 | — |
| rls_http_b_cannot_list_a | GET | `/api/resources/` | 200 | — |
| cross_tenant_object_not_found | GET | `/api/resources/1/` | 404 | — |
| insufficient_scopes_shared_viewer | POST | `/api/resources/` | 403 | Yes |
| cross_tenant_query | GET | `/api/resources/?organization_id=2` | 403 | Yes |
| cross_tenant_write | POST | `/api/resources/` | 403 | Yes |
| valid_central_foreign_tenant_denied_by_instance_csrf | GET | `/api/auth/csrf/` | 200 | — |
| valid_central_foreign_tenant_denied_by_instance | POST | `/api/auth/login/` | 403 | Yes |
| foreign_cookie_replay_fail_closed | GET | `/api/auth/me/` | 503 | Yes |
| technical_headers_cannot_authenticate | GET | `/api/auth/me/` | 401 | Yes |
| technical_headers_cannot_elevate | POST | `/api/resources/` | 403 | Yes |
| wrong_audience | GET | `/api/auth/me/` | 401 | Yes |
| wrong_issuer | GET | `/api/auth/me/` | 401 | Yes |
| wrong_client_id | GET | `/api/auth/me/` | 401 | Yes |
| wrong_product | GET | `/api/auth/me/` | 401 | Yes |
| invalid_signature | GET | `/api/auth/me/` | 401 | Yes |
| embedded_central_audience_rejected | GET | `/api/auth/me/` | 401 | Yes |
| embedded_central_issuer_rejected | GET | `/api/auth/me/` | 401 | Yes |
| embedded_central_client_rejected | GET | `/api/auth/me/` | 401 | Yes |
| embedded_central_product_rejected | GET | `/api/auth/me/` | 401 | Yes |
| embedded_central_tenant_rejected | GET | `/api/auth/me/` | 401 | Yes |
| embedded_central_role_rejected | GET | `/api/auth/me/` | 401 | Yes |
| embedded_central_signature_rejected | GET | `/api/auth/me/` | 401 | Yes |
| live_central_scope_removal_revokes_session | GET | `/api/resources/` | 401 | Yes |
| scope_restore_does_not_revive_session | GET | `/api/resources/` | 401 | Yes |
| reauthenticate_after_scope_restore_csrf | GET | `/api/auth/csrf/` | 200 | — |
| reauthenticate_after_scope_restore | POST | `/api/auth/login/` | 200 | — |
| live_central_scopes_restored | GET | `/api/resources/` | 200 | — |
| sql_central_tenant_binding_mismatch | GET | `/api/auth/me/` | 503 | Yes |
| central_rejects_client | POST | `/api/integration/sso/login/` | 401 | — |
| central_rejects_audience | POST | `/api/integration/sso/login/` | 401 | — |
| central_rejects_product | POST | `/api/integration/sso/login/` | 401 | — |
| central_rejects_forged_technical_headers | POST | `/api/integration/sso/login/` | 401 | — |
| central_rejects_unregistered_credential | POST | `/api/integration/sso/login/` | 401 | — |
| central_logout | POST | `/api/integration/sso/logout/` | 200 | — |
| revoked_me_reconnect_1 | GET | `/api/auth/me/` | 401 | Yes |
| revoked_write_reconnect_1 | POST | `/api/resources/` | 401 | Yes |
| revoked_me_reconnect_2 | GET | `/api/auth/me/` | 401 | Yes |
| revoked_write_reconnect_2 | POST | `/api/resources/` | 401 | Yes |
| same_proof_revoked | POST | `/api/integration/sso/introspect/` | 401 | — |
| central_outage_protected_get | GET | `/api/auth/me/` | 503 | Yes |
| central_outage_protected_write | POST | `/api/resources/` | 503 | Yes |
| local_password_fallback_forbidden_csrf | GET | `/api/auth/csrf/` | 200 | — |
| local_password_fallback_forbidden | POST | `/api/auth/login/` | 503 | Yes |
| central_outage_login_csrf | GET | `/api/auth/csrf/` | 200 | — |
| central_outage_login | POST | `/api/auth/login/` | 503 | Yes |
| revocation_survives_central_restart | GET | `/api/auth/me/` | 401 | Yes |
| active_session_recovers_after_outage | GET | `/api/auth/me/` | 200 | — |

57 orchestrator cases: 49 consumer HTTP requests and 8 direct central requests.
47 total central HTTP requests observed, including those initiated by ISO; 96 actual HTTP requests overall.
13 explicit SQL permission/RLS denials.
33 denied consumer calls with unchanged complete table snapshots and zero protected-handler calls.
