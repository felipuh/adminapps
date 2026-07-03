# Pilot Readiness Package - ISO Smart Ecosystem

Date: 2026-07-03

## 1. Pilot Scope

- Limited paid pilot.
- Known users only.
- Defined pilot tenant/organization.
- No regulated production.
- No WORM guarantee.
- No 21 CFR Part 11/GxP validated claim.
- No massive multi-client operation yet.

## 2. Included Systems

- AdminApps.
- ISO Smart.
- ISO Smart MedSupplier.

## 3. Entry Conditions

- AdminApps migrations applied in the controlled/local database.
- Django checks pass.
- Deployment checks pass with safe simulated production variables.
- Official backend test gates pass.
- Frontend lint/build pass.
- AdminApps/no-fallback smoke passes before kickoff.
- Backups and restore owner are defined.
- Pilot users are defined.
- Product entitlements are configured.

## 4. Commercial Restrictions

- Controlled use only.
- Non-critical data or explicitly authorized pilot data only.
- No promise of regulated production readiness.
- No promise of WORM storage.
- JWT in `localStorage` accepted temporarily with disclosure.
- Manual support during the pilot.

## 5. Accepted Risks

| Risk | Severity | Mitigation | Accepted By |
| --- | --- | --- | --- |
| JWT stored in `localStorage` | High | Trusted users, CSP, logout clears tokens, no token logging, future HttpOnly cookie migration | Pilot owner |
| Default tests require DB create permissions in ISO Smart/MedSupplier | Medium | Official `settings_test` gate uses SQLite; CI/staging DBA fix documented | Engineering owner |
| AdminApps unavailable during pilot | High | Smoke verifies no silent fallback in staging/production; operational escalation before kickoff | Release owner |
| No regulated validation package | High | Explicit scope exclusion; regulated production remains NO GO | Product owner |

## 6. GO/NO GO Criteria

GO requires all official QA gates, frontend builds, and the pilot smoke checklist to pass in the target pilot environment. NO GO applies if entitlement enforcement fails, invalid API keys are accepted, backups are undefined, or production-like fallback behavior is unsafe.

## 7. Pre-Kickoff Checklist

- Confirm target URLs and TLS.
- Confirm AdminApps health endpoint.
- Confirm pilot organization and entitlements.
- Confirm users, roles, and support contacts.
- Run `docs/PILOT_SMOKE_CHECKLIST.md`.
- Capture evidence and owner sign-off.

## 8. Daily/Weekly Pilot Checklist

- Review application errors and integration failures.
- Review suspicious auth failures.
- Confirm AdminApps availability.
- Confirm backups completed.
- Review pilot feedback and support tickets.

## 9. Pilot Closure Checklist

- Export agreed pilot evidence.
- Revoke test users and temporary credentials.
- Review incidents and accepted risks.
- Decide continue, extend, or stop.
- Convert pilot findings into MVP enterprise backlog.

## 10. MVP Enterprise Recommendation

Before MVP enterprise, complete target-environment validation, monitoring, backup/restore drill, HttpOnly cookie migration plan, CI/staging DB permission fix, and live AdminApps integration smoke evidence.

## 11. Production And Regulated Status

Controlled production remains NO GO. Regulated/formal production remains NO GO until WORM, SOPs, validation evidence, audit controls, restore drills, and regulated operational governance are complete.

