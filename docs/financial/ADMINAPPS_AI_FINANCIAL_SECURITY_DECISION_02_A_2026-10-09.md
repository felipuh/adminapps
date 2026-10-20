# AdminApps AI Financial Authority — Security Decision 02-A

**Status:** `SECURITY_DECISION_02_A = HUMAN_APPROVED`  
**Scope:** bounded S3 remediation only; this record does not amend historical contracts.

## Decision

The approved S3 remediation uses a versioned, canonical Ed25519 admission
capability.  It is domain separated as
`adminapps.financial.admission-capability.v1` and binds exactly: issuer, fixed
financial audience, key ID, capability ID, producer registration, canonical
AdminApps organization, product, environment, `admit_reserve` operation,
stable invocation ID, canonical material hash, grant ID/version, `iat`, `nbf`,
`exp`, algorithm and contract version.  The synthetic interval is at most 60
seconds.  JSON serialization is sorted, compact ASCII JSON; no alternative
algorithm, unknown key, missing/extra claim, invalid signature, expired,
future, wrong audience or altered material is accepted.

The issuer first validates the registered hashed producer credential, exact
scope and a live explicit producer-to-tenant/product/operation/environment
grant.  The executor independently verifies the capability with `cryptography`
Ed25519 public material, recomputes the canonical financial material hash, and
uses only the dedicated `adminapps_financial_executor` database identity.  The
general runtime has no execute right on either the legacy admission function or
the capability admission function.  PostgreSQL locks and rechecks the live
grant inside the admission transaction before it delegates to the reviewed S3
atomic boundary.

## Database boundary

`adminapps_financial_executor` is required to be `LOGIN`, `NOINHERIT`,
`NOSUPERUSER`, and `NOBYPASSRLS`.  It receives only schema usage and execute on
`financial_admit_reserve_capability`; it has no direct financial-table grant.
The `SECURITY DEFINER` owner remains the distinct NOLOGIN admission role.
`ProducerTenantGrant`, append-only grant lifecycle evidence, and the immutable
invocation ledger are protected with FORCE RLS and append-only triggers.

The ledger records the signed capability identity, producer, tenant, product,
grant, invocation, material hash, issuer/key/version and admission identity.
The existing admission uniqueness remains authoritative for reconciliation and
conflicting retries.  Grant revocation and admission lock the same grant row;
therefore an admission serialized after revocation fails.

## Threat boundary and residual risk

This decision blocks the reproduced general-runtime direct-SQL attack.  It
does not claim protection from a compromised isolated issuer/executor,
superuser, database administrator or migration control plane.  The S3 source
contains no production signing key, production executor credential, key
rotation, endpoint, provider dispatch, settlement, release, recovery, or ISO
Smart runtime integration.

The current repository provides the issuer/executor interfaces and a
disposable PostgreSQL executor identity, but it does **not** provision an
operating-system service account, authenticated IPC transport, secret store or
production credential.  Those are intentionally outside this authorization.
Consequently, this record must not be read as proof of production process/key
isolation; that evidence is required before an S3 PASS verdict.

## Source traceability (read-only)

- `isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md`
- `isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_AMENDMENT_01_DECISION_RECORD_2026-10-08.md`
- `isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_IMPLEMENTATION_READINESS_2026-10-08.md`
- `docs/financial/ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md`
- S1, S2, S3 implementation reports and the 2026-10-09 S3 final validation.
