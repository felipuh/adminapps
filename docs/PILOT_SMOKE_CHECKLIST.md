# Pilot Smoke Checklist - ISO Smart Ecosystem

Date: 2026-07-03

## Required Configuration

- `ADMINAPPS_BASE_URL` points to the target AdminApps integration API.
- `ADMIN_APPS_API_KEY` is configured in ISO Smart and MedSupplier.
- Pilot organization slug is known and active.
- Product entitlements for ISO Smart and MedSupplier are active.
- Production/staging fallback flags are disabled: `ALLOW_LOCAL_AUTH_FALLBACK=False` and `ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS=False`.

## Smoke Steps

| Step | Command or URL | Expected Result |
| --- | --- | --- |
| AdminApps health | `curl -fsS "$ADMINAPPS_BASE_URL/health/" -H "X-API-Key: $ADMIN_APPS_API_KEY"` | HTTP 200 JSON health response. |
| Pilot organization active | Query AdminApps organization endpoint for the pilot slug | Organization exists and `is_active=true`. |
| ISO Smart entitlement active | Query AdminApps product/entitlement endpoint for pilot organization and ISO Smart product | Active entitlement is returned. |
| MedSupplier entitlement active | Query AdminApps product/entitlement endpoint for pilot organization and MedSupplier product | Active entitlement is returned. |
| ISO Smart access validation | Log in as pilot user and open ISO Smart dashboard | Access allowed only when AdminApps validates user and entitlement. |
| MedSupplier access validation | Log in as pilot user and open MedSupplier dashboard | Access allowed only when AdminApps validates user and entitlement. |
| AdminApps outage behavior | Stop or block AdminApps in staging, then retry ISO Smart/MedSupplier access | Staging/production rejects access with no silent local fallback. |
| Explicit demo fallback | In local demo only, enable the documented fallback flag and repeat outage behavior | Fallback works only with explicit local/demo flag. |
| Invalid API key | Retry integration request with a known invalid key | Request is rejected. |
| Missing entitlement | Use a pilot user or org without product entitlement | Access is denied. |

## GO/NO GO

GO for kickoff requires all smoke steps to pass in the target pilot environment, with evidence captured in the release notes. Any silent fallback in staging/production, invalid API key acceptance, or entitlement bypass is NO GO for the pilot.

