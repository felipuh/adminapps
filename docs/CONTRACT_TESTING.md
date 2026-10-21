# Contract Testing

Date: 2026-07-03

## Contract Surface

AdminApps is the authority for:

- Active organizations
- Active users
- Active product systems
- Active organization product entitlements
- Integration API key authentication

Product systems consume the following AdminApps contract:

- `GET /api/integration/health/`
- `GET /api/integration/organizations/`
- `GET /api/integration/organizations/{organization_id}/`
- `GET /api/integration/organizations/{organization_id}/users/`
- `GET /api/integration/organizations/{organization_id}/products/`
- `GET /api/integration/organizations/{organization_id}/products/{product_code}/validate/`

## Automated Coverage

AdminApps:

- `backend/apps/integration/tests.py::IntegrationAPIKeyUsageTests`
- `backend/apps/integration/tests.py::IntegrationContractTests`
- `backend/apps/integration/tests.py::SSOProductClaimsTests`

ISO Smart:

- `backend/core/tests_security_guardrails.py::LocalBypassGuardrailTests`

MedSupplier:

- `backend/medsupplier/tests.py::MedSupplierAdminAppsClientTests`

## Contract Assertions

- Valid API key is required.
- Invalid API key is rejected.
- Active entitlement allows product access.
- Missing entitlement denies product access.
- Suspended entitlement denies product access.
- Tenant A cannot consume Tenant B entitlement through an invalid key or local bypass.
- If AdminApps is unavailable, production fails closed.
- Development/demo fallback requires an explicit flag and is scoped to local records.

## ISO Smart entitlement pre-kickoff evidence

Required result before kickoff:

- Organization: `SMART3AI` / Smart3AI
- Product: `ISO_SMART`
- Access allowed: `true`
- Source: AdminApps
- Fallback: `false`
- Billing/subscription configured: `true`
- Evidence captured at: 2026-07-03, local controlled AdminApps Django client smoke

Contract evidence:

```text
GET /api/integration/organizations/<SMART3AI_ID>/products/ISO_SMART/validate/
HTTP 200
allowed=true
reason=ok
product.access_allowed=true
product.billing_status=active
```

Negative controls:

```text
invalid API key -> HTTP 401 invalid_api_key
organization without ISO_SMART entitlement -> HTTP 403 product_not_enabled
billing-blocked fixture -> HTTP 403 billing_blocked
```

## Remaining E2E Gap

The current contract suite uses strict Django/APIClient tests and mocked AdminApps outages for fail-closed behavior. A full live E2E run with all three services listening on their target ports remains a production-readiness task, not a controlled pilot blocker.
