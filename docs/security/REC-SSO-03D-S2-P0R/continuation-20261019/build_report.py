from pathlib import Path
import csv,json,shutil
root=Path('/home/felipe/proyectos');d=root/'adminapps/docs/security/REC-SSO-03D-S2-P0R/continuation-20261019'
s=json.loads((d/'test-summary.json').read_text())
rows='\n'.join(f"| {x['suite']} | {x['methods']} | {x['PASS']} | {x['FAIL']} | {x['ERROR']} |" for x in s['suites'])
report=f'''# REC-SSO-03D-S2-P0R — continuation, 2026-10-19

America/Costa_Rica. Local authorized host includes `192.168.56.11` (read-only interface inspection).

## A. Executive Verdict

**DECISION_D_S2_P0R_PARTIAL_WITH_EXPLICIT_BLOCKERS**

**PRODUCTION_READY = FALSE · NO_DEPLOYMENT · NO_COMMIT · NO_PUSH · GOVERNANCE_PRESERVED**

This invocation extends the existing P0R implementation; the [preceding report](../REPORT.md) and its
sealed evidence are preserved. Four existing source files changed, one new test module was added.
**12 new unique methods PASS_OFFLINE**, of which seven reproduce defects before their respective fixes.

Both consumers now reject central 4xx responses without local fallback, including the 404 produced for
a suspended tenant. Server error bodies cannot provide positive authorization. Subscription invoice
payment now uses a real serializer, rejects invalid states/references, preserves completed payment
evidence on retry and rejects conflicting references. No authorization gate was widened.

**Global/local session convergence is still incomplete.** The local registry does not invalidate access
JWTs. PostgreSQL persistence/concurrency and real provisioning/HTTP E2E remain unverified. This report
therefore does not award the expected local-closure verdict.

## B. Baseline and Integrity

Discovery recovered `/tmp/rec-sso-03d-api-p0-20261016`, the API-P0 report revised on October 19, and the
already completed P0R worktree/evidence. Their fixes and 40 P0R methods are inherited work, not new work
of this invocation. The new snapshot covers **45,852 existing files** from git's tracked/unignored lists.
[baseline-summary.json](baseline-summary.json) records the full manifest path/hash, heads and index hashes.
`/tmp/rec-sso-03d-s2-p0r-continuation-20261019/before` contains the four source baselines actually edited.

| Repository | HEAD retained |
|---|---|
| AdminApps | `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` |
| ISO Smart | `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` |
| MedSupplier | `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` |

[code-hashes.json](code-hashes.json) records before/after hashes of the five source paths.
[continuation-only.patch](continuation-only.patch) compares against the initial dirty worktrees, not HEAD.
[integrity-final.json](integrity-final.json) verifies heads/indices, preexisting files and the exact delta.
No settings, secrets, migration, historical suite or unrelated file was edited. The preceding P0R
SHA256SUMS are checked independently; [SHA256SUMS](SHA256SUMS) seals this new evidence directory.

## C. Local/Central Session Reconciliation

| Authority | State owner and verifier | Revocation limit |
|---|---|---|
| AdminApps UserSession | Local registry/listing | Deactivation does not invalidate signed JWTs |
| AdminApps access JWT | SimpleJWT signature/expiry + live user admission | No session-family registry check |
| AdminApps refresh | SimpleJWT blacklist | Owned optional refresh logout, not access/cookie/global logout |
| Django cookie | Django session backend | REST logout does not demonstrate cookie invalidation |
| SSOSession + generations | Central AdminApps lifecycle B/introspection | Owned SID revoke, central logout/rotation/admin revoke under fence |
| SSOSecurityFence/outbox | Central authority ordering | PostgreSQL triggers/durable commit NOT_EVIDENCED |
| ISO/Med local tokens/projections | Each consumer plus live central proof in successor B/D | Not an AdminApps UserSession; central denial must fail closed |
| Technical IntegrationAPIKey/grant | Credential hash and explicit credential_id grant | Separate from human sessions and SSOClient |

[session-authority.csv](session-authority.csv) retains the detailed baseline matrix. New signed-bearer
dispatch tests verify the authenticated JTI and owner filter, and deny an arbitrary keep-ID. They
explicitly assert `access_tokens_revoked=false`; they are not evidence of local JWT revocation.

## D. Revocation Implementation

No central lifecycle contract was changed in this continuation. The six existing P0R central tests
were rerun with real RSA proofs/handlers: owned single/all revocation, foreign/unknown SID denial,
old generations after rotation, inactive actor and retry after a lost response. Original B/D/MFA
regressions were also executed. Repeated revocation never grants authority in those simulations.

The concrete convergence defect remains reproducible in the inherited local-registry test. Installing
a new authenticator in active settings is outside this execution, and a partial check on one endpoint
would not provide universal revocation. The safe action is to preserve the truthful registry contract
and keep P0R-02 FAIL pending session binding/access+refresh+cookie implementation. Password changes,
disable/re-enable and administrative central persistence still depend on the prepared B triggers.

Consumer handling of tenant suspension is corrected: all three legacy organization wrappers now
observe the central 404 rejection instead of restoring local authority from a demo fallback.

## E. Service Grants Security

The existing strict grants implementation is unchanged and was rerun: hashed authenticated credential,
activity/status/revoked_at, explicit operation/tenant/product lists, unknown/incomplete grants denied,
no credential borrowing, no implicit human permissions or SSOClient grant. Authentication uses a
synthetic fixture in the actual credential format/hash path; no real credential was invented/provisioned.

Seven original operations remain the only recognized service grants. Product filtering and tenant
membership restrictions remain intact. Central 4xx errors now remain denials through both consumers;
5xx authorization-shaped JSON is discarded. [CONTRACT.md](CONTRACT.md) gives the precise amendments
and links the unchanged non-secret provisioning template.

## F. Consumer Compatibility

The 34-method inherited P0R suite executes both actual `integration/client.py` adapters against all
seven central handlers using the real resolver, credential hash/decorators and simulated transport/ORM.
The new suite starts with an active tenant ALLOW, suspends it, reaches the central handlers' 404, and
checks organization/users/modules wrappers: negative authority and zero fallback calls in both products.
It also checks 400/401/403/404/405/409/410/422/429 with positive/non-object bodies and 500/502/503
positive bodies in production. Existing test/demo transport fallback policy is preserved, not expanded.

HTTP/DB projections/provisioning/browser E2E are **NOT_EVIDENCED**. Compatibility is certified only for
the executed adapters/handlers and synthetic fixture. Consumer documents record these amendments.

## G. Functional ALLOW Coverage

| Operation | Additional actual code exercised | Persistence |
|---|---|---|
| Invoice mark_paid pending/overdue | Dispatch, platform gate, real MarkInvoicePaidSerializer, paid_at/reference and real Subscription.activate state/date effects | Save simulated |
| Invoice paid retry | 200 without rewrite or subscription activation, missing/same reference | Sequential only |
| Registry revoke | Signed bearer authentication → owner filter → authenticated JTI preservation | ORM simulated |
| Service read then tenant suspension | Both adapters → resolver → credential authentication → organization handlers | ORM/HTTP simulated |

The inherited functional suite also re-executes plan changes, subscription activation/cancel,
entitlement restrictions/audit, membership deactivation, user disable/password, tenant suspension,
settings, invitations and backoffice gates. This invocation adds no trial, quota, shared subscription,
pricing or E/F/G adjudication. [authorization-delta.csv](authorization-delta.csv) overlays the existing
778-row ledger; method aliases/OPTIONS are not promoted to functional evidence. Service adapter
coverage is recorded separately in [functional-coverage.csv](functional-coverage.csv).

## H. Adversarial DENY Results

New invoice tests deny anonymous/technical/inactive/unprivileged principals, missing model permission,
elevation/foreign-relation fields, structured/boolean/null/oversized payment references, and
cancelled/refunded/draft/unknown states. Conflicting paid references return 409. A replay of an already
paid invoice cannot reactivate a subscription whose authority has since been withdrawn.

[reproduction-before.log](reproduction-before.log): 11 methods, six failing methods, 48 failing subtests,
zero errors before the first fixes. [reproduction-5xx.log](reproduction-5xx.log): one additional method
with six failing subtests before discarding server-error bodies. All seven unique reproduction methods
pass in the final 12-method suite. Development/imported-suite mistakes and intermediate runs are retained
in `/tmp` and excluded from final counts. These are simulated effects, not transactional proof.

## I. Invitation Lifecycle

The existing P0R suite reruns actual serializer consumption after validation, then loss of inviter
activity/membership/role/staff/model permission, tenant activity, invitation state/expiry or identity.
Mass assignment, disabled fence and replay remain denied; valid consumption issues real signed tokens.
No invitation logic or historical tests were changed here. Historical continuity across a complete
revoke→restore cycle, and SQL concurrent mutation/consumption, remain unverified/open policy.

## J. Historical Regression Results

Every inherited selected method's identity and status matches the immediately preceding P0R baseline:
[historical-reconciliation.json](historical-reconciliation.json). Existing failures are retained, not
converted to skips or pass. The invitation fixture error was already present at the start of this
invocation; it remains an error. The ten Django Admin methods pass within historical-api-admin.

| Suite | Methods executed | PASS | FAIL | ERROR |
|---|---:|---:|---:|---:|
{rows}

| Counting category | Count |
|---|---:|
| New unique methods this invocation | 12 |
| Inherited unique method origins rerun | 931 |
| Total unique origins | 943 |
| Selected final method executions | 1,433 |
| Final PASS / FAIL / ERROR executions | 1,349 / 24 / 60 |

Repeated inheritance is deduplicated in [unique-methods.json](unique-methods.json). The previous 40 new
P0R methods are inherited here. Subtest failures and development/baseline retries do not inflate totals.
Separate frontend checks: ISO A 4/4 and B 3/3; Med A 4/4 and B 4/4, **15 scenarios PASS**, excluded from
Python method totals. These extract existing login/refresh functions; they are not browser tests.

Django system check with synthetic settings/dummy backend: PASS. In-memory compilation of all five
source paths and git diff --check in all three repositories: PASS. Ruff/Flake8/Pylint/pytest are absent
from each inspected venv and PATH: lint execution NOT_EVIDENCED. No tool installation was attempted.
Harness guards report zero DB/network attempts. Full suite logs, commands and per-method results are included.

## K. Acceptance Criteria

| Criterion | Status | Evidence/limit |
|---|---|---|
| P0R-01 | PASS | Session ownership matrix and explicit contracts |
| P0R-02 | FAIL | Central semantics verified offline; local access/refresh/cookie convergence remains incomplete |
| P0R-03 | PASS_OFFLINE | B/D consumers reject revoked central proofs; suspended tenant 404 no fallback |
| P0R-04 | PASS_OFFLINE | Central generations/replay; no equivalent local-family guarantee |
| P0R-05 | PASS_OFFLINE | Actual credential hashing/identity path with synthetic fixtures |
| P0R-06 | PASS_OFFLINE | Tenant/product grants and output isolation rerun |
| P0R-07 | PASS_OFFLINE | Both actual clients/all seven handlers; no full E2E claim |
| P0R-08 | PASS_OFFLINE | More real serializer/state ALLOW evidence, including overdue payment and retry |
| P0R-09 | PASS_OFFLINE | New and inherited adversarial DENY |
| P0R-10 | PASS_OFFLINE | Existing platform/model gates preserved, Admin regressions pass |
| P0R-11 | PASS_OFFLINE | Existing consumption/authority suite rerun; continuity/SQL open |
| P0R-12 | PASS_OFFLINE | B/D/MFA green; A/C/H exact inherited statuses |
| P0R-13 | PASS | Historical suites byte-preserved, failures reported |
| P0R-14 | PASS | HEAD/index unchanged, invocation-only diff/hashes |
| P0R-15 | PASS | PostgreSQL/E2E classified; actual persistence NOT_EVIDENCED |
| P0R-16 | PASS | Commercial/governance holds preserved |

## L. Remaining Local Gaps

1. P0: define/implement local token session-family binding and universal access/refresh verification,
   including legacy-token policy, current-session preservation, cookie/logout/password/disable semantics.
   UserSession deactivation alone is insufficient. No global convergence closure is awarded.
2. Invoice/subscription saves remain separate, without a new lock/transaction. Sequential retry safety
   is verified; concurrent reference conflicts and partial failures remain NOT_EVIDENCED. Add a coherent
   transaction/outbox only with proportional persistence tests and existing billing governance.
3. Full ALLOW branches for billing issuance/batches/exports, entitlement expansion, commercial trials,
   shared ownership and quotas remain incomplete/held; no permissions were widened to make tests pass.
4. Invitation revoke→restore continuity policy and the historical invalid-inviter fixture incompatibility
   remain documented. Preserve the historical suite; add successors for adjudicated policy.

## M. External Dependencies

PostgreSQL migration/trigger activation, real locks/rollback/RLS/concurrency and durable outbox:
**NOT_EVIDENCED**, with shared DB/service access outside authorization. Real credential grants, external_id
projection persistence, HTTP/browser E2E and operational provisioning:
**BLOCKED_BY_EXTERNAL_DEPENDENCY**. Exact non-secret grant schema and product-specific provisioning
requirements remain in the preceding contract. Linters: **NOT_EVIDENCED**, unavailable locally.
No migration, shared DB connection, worker, deployment, commit or push was performed.

## N. Next Engineering Slice

First resolve the local session-binding contract and implement issuance/access/refresh/logout together
with explicit treatment of old tokens; preserve central SID separation. Then verify the B fence and
payment write ordering using an independently authorized isolated PostgreSQL harness. Continue remaining
functional ALLOW branches only under existing commercial adjudications.

Preserved exactly: `S3-IMP-01`, `S3_DECISION_02A_NOT_CLOSED`, `PHASE31_5 = EXECUTION_HELD`,
`REC-2FA-04`, `REC-SSO-02`, `REC-SSO-03A`, `REC-SSO-03B-CH`,
`DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED`. E/F/G remain open.

Reproduce the new tests without active project settings, DB or network:

```sh
cd /home/felipe/proyectos/adminapps
backend/.venv/bin/python -B backend/scripts/rec_sso_03d_api_p0_offline.py apps.api.test_p0r_continuation
```

The [contract delta](CONTRACT.md), [OpenAPI delta](p0r-continuation.openapi.json), [test matrix](test-matrix.csv),
[functional matrix](functional-coverage.csv), logs, hashes and attributable diff accompany this report.
'''
(d/'REPORT.md').write_text(report)
shutil.copy2(d.parent/'session-authority.csv',d/'session-authority.csv')
with (d/'functional-coverage.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['operation','test_class','handler','effects','persistence'])
 w.writerow(['Invoice.mark_paid','InvoiceFunctionalContinuationTests','real dispatch/gate/MarkInvoicePaidSerializer','pending/overdue paid and subscription activation; retry preserves evidence; invalid state/reference denied','NOT_EVIDENCED'])
 w.writerow(['User.revoke_sessions','LocalRegistryTokenContinuationTests','real signed bearer/dispatch','owner filter/current authenticated JTI; foreign keep-ID denied; NO local JWT invalidation','NOT_EVIDENCED'])
 w.writerow(['consumer tenant suspension','ConsumerDenialContinuationTests','both actual adapters + credential hash + central organization/users/modules handlers','central 404 denies; zero local fallback calls','NOT_EVIDENCED'])
 w.writerow(['consumer HTTP errors','ConsumerDenialContinuationTests','both actual adapters; synthetic HTTP responses','all 4xx denied; 5xx bodies never grant production access','NOT_EVIDENCED'])
contract='''# Service grant consumer amendment — 2026-10-19 continuation

Both adapters now fail closed on every central HTTP 4xx, including missing/disabled tenant 404.
They return allowed=false and authorization_denied=true; existing local fallback cannot bypass this.
Server HTTP error bodies are discarded: allowed/valid/modules inside a 5xx are not authority. Existing
explicit test/demo transport fallback policy remains, and IS_PRODUCTION=true disables it.

No active settings, credentials or grants were changed. The seven service grants, authenticated
credential_id, tenant/product lists and independence from SSOClient retain the preceding contract.
No additional permission or fallback is implied. Actual adapter/central-handler tests use synthetic
credentials and simulated ORM/HTTP. Real provisioning, projection persistence and HTTP E2E remain open.

Evidence and full contract delta:
`/home/felipe/proyectos/adminapps/docs/security/REC-SSO-03D-S2-P0R/continuation-20261019/REPORT.md`.

PRODUCTION_READY = FALSE · NO_DEPLOYMENT · NO_COMMIT · NO_PUSH · GOVERNANCE_PRESERVED.
'''
for repo,folder in [('isosmart','transformation'),('ISO_Smart_MedSupplier','security')]:
 (root/repo/'docs'/folder/'REC_SSO_03D_S2_P0R_SERVICE_GRANTS_CONTINUATION_2026-10-19.md').write_text(contract)
