# AdminApps AI Financial Authority — Security Amendment 02

**Status:** `SECURITY_AMENDMENT_02 = APPROVAL_PENDING`

**Technical adjudication verdict:**
`ADMINAPPS_S3_SECURITY_AMENDMENT_02_READY_FOR_HUMAN_APPROVAL`

This is an approval-pending security-contract proposal, not an implementation
authorization.  It does not alter V1.1, migrations, database roles, runtime
code, credentials, operational endpoints, or financial records.  In
particular, it does not make S3 pass.

## 1. Governing state and review record

The governing state for this adjudication is:

```text
FINANCIAL_CONTRACT_V1_1 = HUMAN_APPROVED
SECURITY_AMENDMENT_02 = APPROVAL_PENDING
S1 = PASS
S2 = PASS
S3 = BLOCKED_BY_SECURITY_CONTRACT
S4_TO_S6 = NOT_AUTHORIZED
REAL_OPENAI_INFERENCE = NOT_AUTHORIZED
PRODUCTION_FINANCIAL_ADMISSION = NOT_AUTHORIZED
PRODUCTION_DELIVERY = NOT_AUTHORIZED
DEPLOYMENT = NOT_AUTHORIZED
GIT_COMMIT = NOT_AUTHORIZED
GIT_PUSH = NOT_AUTHORIZED
GIT_MERGE = NOT_AUTHORIZED
CREDENTIAL_ROTATION = NOT_AUTHORIZED
PHASE31_5 = EXECUTION_HELD
```

The review examined the V1.1 contract, Amendment 01, implementation-readiness
matrix, S1/S2/S3 reports and final validation, financial source, migrations
`0004` and `0005`, and the disposable PostgreSQL verifiers and tests.  The
authoritative-contract sources are retained in the ISO Smart documentation;
this amendment is deliberately added only to AdminApps financial
documentation.  No ISO Smart runtime or documentation was modified.

## 2. Confirmed defect and reproducible evidence

`public.financial_admit_reserve(...)` is a `SECURITY DEFINER` function owned
by the non-login `adminapps_financial_admission` role.  It has a fixed
`search_path`, no dynamic SQL, no `PUBLIC EXECUTE`, and the runtime role cannot
directly read or mutate protected financial records.  Those are valuable S1/S3
controls, but they do not establish who is invoking the function.

The preserved PostgreSQL test
`FinancialAdmissionPostgresRuntimeRoleTests.test_runtime_direct_call_can_forge_an_eligible_tenant_identity`
connects through a disposable non-superuser evidence login, executes `SET ROLE
adminapps_financial_runtime`, and calls the function with:

* an active producer-registration UUID;
* an eligible, separate Tenant-B organization UUID;
* an in-scope product UUID; and
* fresh caller-selected invocation, correlation, material-hash, decision and
  reservation UUIDs.

The result is `('reserved', '')`, with a persisted reservation owned by Tenant
B.  This is a passing *exploit reproduction*, not a passing control.  The
test, verifier, migrations and all prior work remain unchanged.

The defect is therefore not a bypass of PostgreSQL table privileges or RLS.
It is an authorization-confused privileged interface: a caller that may invoke
the function can choose the security-relevant identity tuple and the function
does not independently prove that this invocation was authorized for that
producer and tenant.

## 3. Source-level trust-boundary adjudication

| Boundary | Independently verified today | Trusted or caller-controlled gap |
| --- | --- | --- |
| A. Django `IntegrationAPIKey` verification | Django verifies an active `hashed_v1` credential and its password hash before its normal service path calls PostgreSQL. | The PostgreSQL function receives no proof of that successful verification and cannot verify the Django password hash. |
| B. `ProducerRegistration` | Django and the function check registration lifecycle, environment, permitted product and `admit_reserve` operation. | Registration has no authoritative producer-to-tenant grant and a UUID is supplied by the caller. |
| C. Canonical organization | The function checks that `organizations.Organization` exists and is active. | Existence/active status is not evidence that the producer may act for that organization. |
| D. Producer-to-tenant authorization | None is represented or checked by the reviewed source. | `p_organization_id` is a function argument; no grant, signed assertion, or trusted execution identity binds it to the registration. |
| E. PostgreSQL runtime identity | Role ACLs prove that the runtime has only the reviewed function path and no direct financial-table path. | A session able to activate that role is not mapped to a producer, tenant, or individual invocation. |
| F. `SECURITY DEFINER` invocation | Owner separation, fixed search path, no dynamic SQL, and narrow execute ACL are demonstrated. | The owner elevates a call whose producer/tenant/invocation arguments are not authenticated at this boundary. |
| G. FORCE RLS and ownership | Financial tables are FORCE RLS, migration-role owned, append-only where required, and the function owner has no membership edge/table ownership. | RLS protects direct table access; it cannot repair an authorized function that writes rows for a caller-selected tenant. |
| H. Reservation persistence | The function atomically rechecks policy, tariff, entitlement, bounds, budgets and idempotency before decision/reservation/audit writes. | These validations apply to the selected tenant. They do not prove selection of that tenant was authorized. |

The current function treats `p_registration_id`, `p_organization_id`,
`p_product_id`, `p_invocation_id`, `p_correlation_id`, `p_material_hash`,
environment, provider/model, bounds and caller-supplied decision/reservation
IDs as inputs.  It independently constrains registration lifecycle and
product/operation scope, organization/product/entitlement, policy, tariff and
budget state.  It does not bind the registration to the organization,
authenticate an invocation, or recompute and authenticate the supplied
material hash at the database boundary.

The S3 function does not consume `app.tenant_id`; changing that GUC cannot
authorize it, but neither does the function rely on a session tenant context.
Consequently, caller-settable GUCs are neither the cause nor an acceptable
remediation.  The Django service checks only that the supplied assertion's
`adminapps_tenant_id` equals the supplied organization argument.  That is
structural consistency, not an independently database-verifiable producer or
invocation authorization.

### Reachability and limits of the finding

There is no S3 HTTP view, URL or provider-dispatch path.  The normal Django
service authenticates the registered credential and requires a structurally
valid tenant assertion before issuing its PostgreSQL call.  This review found
no evidence that an unauthenticated external client can obtain the runtime
database session or cause the Django application to make the reproduced
Tenant-B call.  It must not be represented as an externally reachable exploit
without such evidence.

The demonstrated threat is a principal with arbitrary SQL through the allowed
restricted database interface (or a compromise that obtains that capability).
That is sufficient to fail the requested security property.

## 4. Security requirement and threat model

For V1.1 as amended, a reservation **must not** be created for a
producer/tenant/product/operation/invocation/material combination unless all
of the following are true at its defined authorization linearization point:

1. a live registered producer is authenticated and authorized for the exact
   environment, operation, product and tenant;
2. an AdminApps-controlled authorization service has bound that exact
   invocation ID and canonical material hash to the producer and tenant;
3. the privileged database boundary verifies that authorization evidence and
   rechecks live grant/revocation state; and
4. policy, entitlement, tariff, budget and idempotency checks succeed in the
   same serializable admission transaction.

The design protects against an arbitrary-SQL general runtime role, forged
tenant context/registration/product/invocation/hash, a producer with multiple
tenants, direct use of the admission function, stale authorization, ordinary
replay, and privilege abuse by a function executor without a valid
authorization assertion.  It does not claim to protect against a simultaneous
compromise of the authorization issuer, its signing authority, and the
financial database control plane, nor against a DBA/superuser/BYPASSRLS actor.
Those principals are excluded from all runtime roles and require separate
break-glass governance.

The selected design makes the following separation explicit:

* Django/API-key authentication proves possession of a registered producer
  credential to the trusted issuer; it is not database-verifiable evidence.
* PostgreSQL proves the signed invocation authorization, live grant/revocation
  state, function ACL, RLS, idempotency and financial atomics.  It never
  attempts to validate a Django password hash.
* A compromised general application/runtime database identity cannot mint,
  alter, or use an assertion to create a new reservation.  A compromise of the
  separately trusted issuer/execution component is a higher-order trust-model
  failure; it can request authorized capabilities within its authority and is
  detected/contained through key isolation, grant checks, audit and revocation.

## 5. Options considered

| Option | Strengths | Fails or residual risk | Decision |
| --- | --- | --- | --- |
| A. Database-backed producer/tenant grants | A migration-owned, append-only grant table can independently reject an active registration paired with an unauthorized tenant/product/operation. It is necessary live authorization and supports revocation. | A broad grant alone does not bind an individual invocation. A producer authorized for multiple tenants could still invent a new invocation and material hash for any granted tenant through direct SQL. | Required as a live defense-in-depth control; insufficient alone. |
| B. Asymmetrically signed, invocation-specific capability | Binds issuer, audience, producer, tenant, product, environment, operation, invocation and canonical material hash; permits short expiry and replay control. The database sees evidence the runtime cannot mint. | Needs an approved, maintained asymmetric verification facility at the database boundary, public-key lifecycle, replay state and issuer-key operations. A symmetric secret available to runtime would fail this option. | Required primary authorization evidence. |
| C. Restricted trusted financial execution identity | Removes the general application runtime's execute path and confines financial database access to an isolated component/role. | By itself the execution component can impersonate tenants through caller parameters. If its identity is compromised, that limitation remains. | Required in combination with B, not sufficient alone. |
| Caller UUID, session GUC, generic key or direct Django check | Low implementation effort. | All are forgeable or bypassable by the demonstrated SQL path. | Explicitly rejected. |

## 6. Selected architecture — capability-bound financial execution

Amendment 02 selects the combined B+C model, with A as the authoritative live
grant check.  It introduces the following *approval-pending* trust model for a
future narrow implementation slice:

```text
Producer credential / tenant projection
        -> Financial Authorization Issuer (FAI)
        -> one signed admission capability
        -> isolated Financial Executor database identity
        -> PostgreSQL verifier + live authorization grant + S3 transaction
```

### 6.1 Financial Authorization Issuer (FAI)

FAI is an AdminApps-controlled component, separate from the general Django
runtime.  It authenticates the dedicated registered producer credential,
validates the canonical AdminApps organization and tenant-projection evidence,
evaluates the authoritative producer-to-tenant/product/operation/environment
grant, recomputes the canonical financially material request hash, and issues
at most one short-lived admission capability for the requested immutable
identity.  It records an append-only issuance/audit event without raw
credentials or prompts.

FAI's private signing key is held by an approved isolated key service/HSM (or
equivalent separately controlled signing boundary).  It is unavailable to the
general runtime, the PostgreSQL runtime/executor roles, database functions,
application configuration, and migration role.  A design in which the
runtime can read the signing secret, or in which signer and unrestricted
caller share a symmetric secret, is prohibited.

### 6.2 Capability content and verification

The capability is an asymmetric, versioned and audience-bound assertion.  Its
minimum authenticated claims are:

```text
iss, aud=adminapps-financial-admission, version, kid, jti,
iat, nbf, exp,
producer_registration_id, organization_id, product_id,
environment, operation=admit_reserve, invocation_id,
material_request_hash, correlation_id, authorization_grant_id,
authorization_version
```

The database accepts only a capability verified against a migration-owned,
allow-listed public verification key selected by `kid`, with fixed algorithm,
issuer, audience and clock-skew policy.  It must reject algorithm confusion,
unknown/revoked key IDs, missing/duplicate claims, non-canonical encodings,
expired/not-yet-valid evidence and all verification errors.  The verifier
implementation must be an explicitly approved, reviewable asymmetric-signature
facility; core PostgreSQL/Django password hashing is not silently repurposed as
one.

The replacement admission procedure accepts the verified capability envelope
rather than unauthenticated producer, tenant, product, invocation or material
hash parameters.  After verification it derives those values exclusively from
the authenticated claims.  Any supplied diagnostic fields are ignored or must
exactly equal the claims.  The procedure creates server-side decision and
reservation IDs; caller-selected financial IDs are removed from the privileged
interface.

### 6.3 Database execution, grants and RLS

`adminapps_financial_runtime` loses `EXECUTE` on the replacement admission
function.  Only a new non-login, no-superuser, no-BYPASSRLS,
no-INHERIT `adminapps_financial_executor` role receives that narrow execute
grant.  Its connection authentication is available only to the Financial
Executor.  It has no direct table grants; it is not a table owner, has no
membership edge to the migration or function-owner roles, and cannot set a
privileged session identity.  `PUBLIC EXECUTE` remains revoked.

The function owner remains separate, non-login, no-superuser and no-BYPASSRLS;
keeps its fixed trusted search path and no dynamic SQL; and receives only the
minimum object grants needed for admission.  FORCE RLS, append-only evidence,
budget guards, owner separation and S1/S2 direct-table denials remain required.
No `SUPERUSER`, `BYPASSRLS`, broad application table grant, generic API-key
fallback, caller-settable GUC, or tenant-existence fallback is allowed.

### 6.4 Live authorization, tenant identity and revocation

A migration-owned authorization relation must identify an immutable grant by
`producer_registration_id + organization_id + product_id + operation +
environment`, with active/effective state, version and append-only lifecycle
evidence.  Its creation, suspension and revocation are central financial
governance actions, not producer/runtime writes.  The FAI includes the grant
ID/version in a capability; PostgreSQL locks and rechecks the same live grant
and producer lifecycle row inside the serializable admission transaction.

The canonical tenant remains the AdminApps `organizations.Organization` UUID.
The issuer and procedure must check active organization and live entitlement;
tenant projection remains evidence and never substitutes for this authority.
An authorized producer with multiple tenants requires a distinct live grant
and a distinct invocation capability for every tenant/invocation.  A broad
registration or product scope is never proof of tenant authorization.

Authorization linearizes at the transaction's locked grant/lifecycle check.
The grant-revocation workflow must lock the same rows.  Thus a revocation
committed before that check denies admission; if admission obtains and commits
first, the reservation is recorded/audited and revocation governs later
admissions rather than silently rewriting history.

### 6.5 Replay, idempotency and failure semantics

`jti` is recorded in an append-only/immutable replay ledger bound to the full
admission identity and material hash.  The first valid use may create exactly
one decision.  A second use of the same `jti` may return only that same stored
decision when every bound identity/hash value matches; it can never create a
new decision.  Reuse for a different identity/hash, a different capability for
an already-conflicting invocation, or replay after revocation before a first
use is denied and audited.

Capabilities have short, approved lifetimes and are checked before their first
effect.  An expired unused capability fails closed.  Recovery after an
ambiguous response uses a separately authorized, identity-bound status
capability or issuer-mediated lookup; it does not create a new invocation or
reservation.  Existing immutable identity/hash semantics remain: identical
replay returns the original outcome, conflicting material is
`IDEMPOTENCY_CONFLICT`, and no failed authorization creates a reservation.

If FAI, key service, verifier, grant/lifecycle row, organization/entitlement,
policy/tariff/budget, replay ledger or transaction outcome is unavailable or
ambiguous, admission fails closed.  No caller retry may substitute a new
invocation identity to escape ambiguity.

## 7. Migration and compatibility implications

Approval authorizes design work only; it does not authorize these changes.
The subsequently authorized narrow implementation would require, at minimum,
new migrations for public-key metadata, producer-tenant authorization grants
and immutable lifecycle evidence, capability-replay records, and a replacement
reviewed procedure/ACL.  It must not rewrite existing financial evidence or
weaken existing RLS policies.

S1/S2 remain compatible because the proposal retains their dedicated roles,
append-only audit/lifecycle evidence, registered `hashed_v1` credential as the
FAI authentication input, least privilege and FORCE RLS.  It tightens—not
replaces—the producer mechanism; generic credentials remain prohibited.

S3 remains `SERIALIZABLE`: verification, capability replay state, producer
lifecycle, authorization grant, organization/entitlement, policy/tariff and
budget locks belong in the one admission transaction.  The existing canonical
budget lock order (global then product then UUID) remains.  New lock order and
retry behavior must be specified and demonstrated without deadlock regression.

## 8. Security acceptance matrix after approval

All tests must use a disposable non-superuser, non-BYPASSRLS runtime identity
and prove the actual database rejection path, not only a Django/API result.

| ID | Required test | Required result |
| --- | --- | --- |
| A | Valid registered producer, live grant, valid capability and eligible tenant | One atomic reserved decision/reservation only. |
| B | Valid producer with unauthorized tenant | FAI and procedure deny; no reservation. |
| C | Forged producer-registration ID | Signature/claim/grant mismatch denied; no reservation. |
| D | Forged tenant identity | Signature/claim/grant/entitlement mismatch denied; no reservation. |
| E | Forged product identity | Claim/grant/registration scope mismatch denied. |
| F | Forged PostgreSQL session context/GUC | No effect on authorization; direct path denied without valid capability. |
| G | Replayed admission capability | Exact same effect only; changed identity/hash denied and audited. |
| H | Expired unused capability | Rejected before financial writes. |
| I | Revoked/suspended producer | Rejected by locked live lifecycle check. |
| J | Revocation concurrent with admission | Demonstrate defined grant-lock linearization and no post-revocation unauthorized admission. |
| K | One producer with multiple authorized tenants | Only separately granted, separately capable tenant/invocation pairs succeed. |
| L | Direct SQL under former general runtime role | Cannot execute function; cannot mint capability; no reservation. |
| M | Cross-tenant SQL attempt under executor/general runtime | Forged pair fails at capability/grant check; no cross-tenant row. |
| N | `SECURITY DEFINER` abuse attempts | No public execute, search-path injection, role escalation, direct table mutation or unauthorized procedure use. |
| O | Financial audit immutability | Update/delete/forged audit and lifecycle mutation remain denied. |
| P | Successful atomic reservation | Decision, reservation, scopes, capability use and audit commit together. |
| Q | Failed authorization | No reservation/counter movement; only permitted denial evidence. |
| R | Identical idempotent replay | Same immutable decision, no additional reservation/counter effect. |
| S | Conflicting request | `IDEMPOTENCY_CONFLICT`, no extra effect. |
| T | S1/S2 regression | Role flags, FORCE RLS, lifecycle, credential and financial RBAC tests remain passing. |

Required evidence additionally includes: verifier key rotation/revocation
failure tests; issuer/private-key isolation review; no-signing-secret runtime
access test; concurrent grant/policy/entitlement/revocation races; observed
`40001` and `40P01` handling; lost-response/ambiguous-commit status recovery;
and a source/ACL dump demonstrating exact role/function grants.

## 9. Remaining S3 work deliberately still pending

This amendment does not complete S3.  After approval and implementation of the
new trust boundary, the following remain pending and must not be marked PASS by
this document: multi-tenant concurrency; concurrent policy changes;
entitlement revocation races; observed serialization failures; deadlock
handling; ambiguous commit; recovery using the original idempotency identity;
and rollback/financial-atomicity validation.

The narrow post-approval order is: approve this amendment and named trust
operators; implement only the issuer/key/grant/replay/procedure boundary;
complete the acceptance matrix and preserve the original exploit as a required
negative test; then resume the pending S3 matrix.  S4 settlement/recovery,
S5/S6, production activation, provider calls and ISO Smart modifications are
outside that sequence.

## 10. Explicit approval dependencies

Human approval is required before any remediation implementation for:

1. this amendment's new trust model and the FAI/executor accountability;
2. the approved asymmetric verification facility, algorithm, public-key
   lifecycle, signing-key service/HSM, rotation and emergency revocation;
3. the authoritative producer-to-tenant/product/operation/environment grant
   owner, lifecycle and revocation governance;
4. the executor connection-credential isolation, DBA role/ACL provisioning,
   monitoring and break-glass process;
5. capability retention, replay-ledger retention and audit-data handling; and
6. the separate, narrow S3 remediation implementation/test authorization.

Until those approvals are issued, the only valid final S3 state remains:

```text
ADMINAPPS_AI_FINANCIAL_S3_BLOCKED_BY_SECURITY_CONTRACT
```

## 11. Changed documentation and Git state

This adjudication adds only this approval-pending document:

* `docs/financial/ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md`

No code, migration, test, verifier, credential, commit, merge, push, deploy or
external system was changed.  The pre-existing modified `backend/config/settings.py`
and untracked financial S1–S3 work remain preserved.  The cross-tenant exploit
test remains required evidence.
