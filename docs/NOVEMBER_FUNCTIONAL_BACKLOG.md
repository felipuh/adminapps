# Smart3AI — functional development plan, November 2026

Baseline: `development/2026-11-product-completion`. Date: 2026-10-30, America/Costa_Rica. Goal: finish usable product flows during November, before a separately authorized cloud move and external validation coordinated by Félix. This is a plan with acceptance criteria, not a completion promise.

`PRODUCTION_READY = FALSE`; `PHASE31_5 = EXECUTION_HELD`; `S3_DECISION_02A_NOT_CLOSED`; `NO_DEPLOYMENT`; `NO_SHARED_DB_MUTATION`.

## Sources and coverage limits

Primary inputs: the unchanged DOCX integrated specification and JSON/XLSX master maps under ISO `docs/transformation/source-artifacts`. JSON contains 63 clause mappings, 43 entities, 33 agents, 17 onboarding steps, 14 events and 6 industry routes. OpenAPI and SQL DDL are subordinate partial implementation inputs, not proof of completeness. The 12 files in that directory were fingerprinted before and after this consolidation.

The historical gap matrix (3 implemented / 19 partial / 21 absent) predates the substantial `foundation` implementation and must not be reused as the current completion percentage. The current canonical-model crosswalk below establishes structural presence only. Existing migrations, services and tests are preserved. No model name alone earns a completed functional requirement; persistence, RLS and user journeys were not revalidated against PostgreSQL in this task.

## Completed consolidation requirements

- ISO recovery debug removed, central `/me` binding preserved, unsafe fallback rejected; regression fixtures run without confidential Git ancestry.
- Consumer central authentication/MFA/product/tenant/session contracts covered by offline positive and negative tests. MedSupplier rejects local Django-session bypass and emergency password overrides in operational environments.
- AdminApps retains the sanitized R3 authority, IAM/2FA/revocation behavior and reviewed P0 preflight/QA improvements.
- Independent, hash-locked Python candidates and a single verified shared Design System package make clean-checkout builds reproducible. The shared library remains the design authority.

These closures concern code, packaging and the tested offline scope. They do not declare live-service remediation, HTTP E2E or production readiness.

## Results to deliver

| Dates | User outcome / priority | Existing code to finish | Acceptance evidence and dependencies |
|---|---|---|---|
| Nov 2–6 | P0: a legitimate user signs in with central MFA, enters only authorized products/tenants, and loses access after revocation | AdminApps `apps/integration`, `apps/users`; consumers `authentication`, `integration`; login/AuthContext UI | Real HTTP login → MFA → `/me` → refresh → revoke, positive/negative tenant/product/role matrix, controlled persistence. Configure central trust and separate development data first. No local-password/session alternative. |
| Nov 2–6 | P0: developers and QA can reproduce a build and diagnose failures | `NOVEMBER_DEVELOPMENT.md`, candidate locks, baseline CI, shared design package | Clean install/build/check succeeds; observe remote CI; register intentional legacy-suite failures separately; supported AdminApps candidate needs migration and signing-provider validation before promotion. |
| Nov 9–13 | P0: a new organization resumes onboarding, completes the Foundation Gate, supplies a profile/evidence and receives a reviewable baseline | ISO `foundation/onboarding.py`, `foundation_gate.py`, `source_artifact_api.py`, `value_discovery.py`, frontend `OnboardingPage.jsx`, `foundationService.js` | Persist/resume after refresh and login; backend controls transitions, score/retries/tenant; document errors recover without data loss; visible results trace to evidence. AdminApps owns steps 1–7; payment/billing behavior stays held unless separately released. |
| Nov 9–13 | P0: Supplier and Customer users collaborate only within their assigned accounts | MedSupplier `medsupplier/models.py`, permissions/views, `medsupplierService.js`, Supplier/Customer UI | Supplier-only, Customer-only, both and neither roles; direct URL/API denial; invitations, contacts, requirements/documents visible to intended parties; cross-tenant and cross-account negative cases. Central identity first. |
| Nov 16–20 | P0: ISO user follows context → stakeholder → scope/process → risk/objective → evidence using one canonical business object | ISO `foundation/qms_context.py`, `risk_objective.py`, `qms_api_views.py`, QMS services plus legacy core/ai_modules pages | Map legacy IDs to canonical entities without duplication or destructive migration; CRUD/permissions/loading/empty/error states; evidence/version lineage; verify application and RLS isolation in a dedicated target. |
| Nov 16–20 | P0: audit findings lead to nonconformity, corrective action and effectiveness review | ISO `foundation/qms_capa_api.py`, frontend `features/qms/pages/QmsCapaPage.jsx`; historical improvement/performance modules | E2E audit → finding → NC → CAPA → evidence → effectiveness; preserve history and enforce reviewer roles; export is authorized and traceable. |
| Nov 16–20 | P1: MedSupplier completes a procurement and quality journey | `medsupplier` RFQ/Quote/PO/Lot/Shipment/Inspection/QualityEvent/CAPA/Scorecard/EvidencePackage | RFQ → quote → purchase order → lot/shipment → inspection → quality event/CAPA → evidence package; Supplier/Customer visibility, status transitions, audit and document version checks. No ISO↔Med history/code merge. |
| Nov 23–27 | P0: recommendations explain their basis and require human approval before material action | ISO `foundation/recommendation.py`, agent execution services, ModelPolicy/AgentRun/RecommendationBasis/Approval/ActionExecution | Evidence, rule/model/prompt version, confidence and assumptions are visible; deny execution without authorization; idempotency, outbox and rollback evidence. Retained financial capabilities remain disabled. |
| Nov 23–27 | P1: users inspect applicable standards and navigate consistent, accessible screens | Shared Design System; ISO evidence graph and missing dedicated Normative Intelligence Drawer | Implement the dedicated normative drawer (no named implementation found); standard edition and evidence lineage on demand; keyboard/focus, contrast, responsive views, translations/timezones, actionable errors. The build alone does not certify UI usability. |
| Nov 23–27 | P1: commercial entry routes lead to the right product and demo request | Landing existing `feature/productized-landing-architecture`; no modifications in this consolidation | Verify links, form success/failure, accessibility and handoff ownership; align copy to available functions. No cloud deployment. |
| Nov 30 | P0: a repeatable acceptance pack and prioritized residual defects are ready for Félix | All product flow tests and evidence | Execute scripted user journeys on separately authorized local development data; classify blockers and usability defects; prepare external-user scenarios and feedback form. Cloud transfer remains a later decision. |

## Current gaps and explicit non-closures

- **Partial:** all canonical entity structures found below; onboarding, evidence graph, QMS/CAPA, recommendation governance and MedSupplier flows have code but still need integrated persistence/UI acceptance. Existing legacy and canonical model duplicates require a mapping plan, not deletion.
- **Absent in inspected frontend:** a dedicated `NormativeIntelligenceDrawer` implementation. Existing EvidenceGraphPage and foundationService do not alone satisfy it.
- **Pending verification:** PostgreSQL RLS/roles, migration state, revocation propagation/concurrency, HTTP SSO with actual trust configuration, recoverability, accessibility and browser flows. No access to operational data was used to infer completion.
- **Known frontend/build defect fixed here:** imports depended on an unversioned sibling design-system folder. All products now pin the same reviewed package. Local dev/HMR defaults are compatible with loopback; MedSupplier previously inherited ISO HMR hostname defaults.
- **Security/operation:** historical secret copies still exist locally/remotely in old histories; rotation/revocation is not certified. Active services continue on previous checkouts and must be treated separately. Old CI definitions and operational requirements remain historical; the new explicit baseline workflow uses the candidate locks.
- **Dependency ownership:** AdminApps owns identity, global tenant, product grants and entitlements. Products own their domain projections and workflows. Design System owns shared UI. Landing owns commercial presence. Do not split ownership by duplicating identity or merging the product histories.

## Canonical entity crosswalk (43 source requirements)

| Source entity | Canonical code evidence | November state |
|---|---|---|
| Tenant | `backend/foundation/models.py:6` (`TenantProjection`) | Partial — user-flow acceptance pending |
| Organization | `backend/foundation/models.py:93` (`Organization`) | Partial — user-flow acceptance pending |
| Site | `backend/foundation/models.py:116` (`Site`) | Partial — user-flow acceptance pending |
| User | `backend/foundation/models.py:1689` (`UserProjection`) | Partial — user-flow acceptance pending |
| Standard | `backend/foundation/models.py:391` (`Standard`) | Partial — user-flow acceptance pending |
| StandardEdition | `backend/foundation/models.py:404` (`StandardEdition`) | Partial — user-flow acceptance pending |
| Clause | `backend/foundation/models.py:455` (`Clause`) | Partial — user-flow acceptance pending |
| RequirementControl | `backend/foundation/models.py:474` (`RequirementControl`) | Partial — user-flow acceptance pending |
| KnowledgeLayer | `backend/foundation/models.py:500` (`KnowledgeLayer`) | Partial — user-flow acceptance pending |
| KnowledgeLayerRule | `backend/foundation/models.py:523` (`KnowledgeLayerRule`) | Partial — user-flow acceptance pending |
| KnowledgeLayerBinding | `backend/foundation/models.py:561` (`KnowledgeLayerBinding`) | Partial — user-flow acceptance pending |
| StandardPack | `backend/foundation/models.py:439` (`StandardPack`) | Partial — user-flow acceptance pending |
| Process | `backend/foundation/models.py:147` (`Process`) | Partial — user-flow acceptance pending |
| Stakeholder | `backend/foundation/models.py:132` (`Stakeholder`) | Partial — user-flow acceptance pending |
| StakeholderRequirement | `backend/foundation/models.py:163` (`StakeholderRequirement`) | Partial — user-flow acceptance pending |
| Risk | `backend/foundation/models.py:243` (`Risk`) | Partial — user-flow acceptance pending |
| Opportunity | `backend/foundation/models.py:270` (`Opportunity`) | Partial — user-flow acceptance pending |
| Objective | `backend/foundation/models.py:295` (`Objective`) | Partial — user-flow acceptance pending |
| Change | `backend/foundation/models.py:351` (`Change`) | Partial — user-flow acceptance pending |
| Document | `backend/foundation/models.py:621` (`Document`) | Partial — user-flow acceptance pending |
| DocumentVersion | `backend/foundation/models.py:643` (`DocumentVersion`) | Partial — user-flow acceptance pending |
| Evidence | `backend/foundation/models.py:669` (`Evidence`) | Partial — user-flow acceptance pending |
| EvidenceCoverage | `backend/foundation/models.py:698` (`EvidenceCoverage`) | Partial — user-flow acceptance pending |
| Recommendation | `backend/foundation/models.py:725` (`Recommendation`) | Partial — user-flow acceptance pending |
| RecommendationBasis | `backend/foundation/models.py:748` (`RecommendationBasis`) | Partial — user-flow acceptance pending |
| AgentDefinition | `backend/foundation/models.py:812` (`AgentDefinition`) | Partial — user-flow acceptance pending |
| AgentRun | `backend/foundation/models.py:860` (`AgentRun`) | Partial — user-flow acceptance pending |
| AgentDecision | `backend/foundation/models.py:946` (`AgentDecision`) | Partial — user-flow acceptance pending |
| DomainEvent | `backend/foundation/models.py:1725` (`DomainEvent`) | Partial — user-flow acceptance pending |
| Approval | `backend/foundation/models.py:973` (`Approval`) | Partial — user-flow acceptance pending |
| ActionExecution | `backend/foundation/models.py:1100` (`ActionExecution`) | Partial — user-flow acceptance pending |
| EffectivenessCheck | `backend/foundation/models.py:1271` (`EffectivenessCheck`) | Partial — user-flow acceptance pending |
| Audit | `backend/foundation/models.py:1202` (`QmsAudit`) | Partial — user-flow acceptance pending |
| Finding | `backend/foundation/models.py:1219` (`Finding`) | Partial — user-flow acceptance pending |
| Nonconformity | `backend/foundation/models.py:1235` (`QmsNonconformity`) | Partial — user-flow acceptance pending |
| CorrectiveAction | `backend/foundation/models.py:1251` (`QmsCorrectiveAction`) | Partial — user-flow acceptance pending |
| IndustryProfile | `backend/foundation/models.py:424` (`IndustryProfile`) | Partial — user-flow acceptance pending |
| LearningPath | `backend/foundation/models.py:1751` (`LearningPath`) | Partial — user-flow acceptance pending |
| QuestionBank | `backend/foundation/models.py:1767` (`QuestionBank`) | Partial — user-flow acceptance pending |
| QuizAttempt | `backend/foundation/models.py:1801` (`QuizAttempt`) | Partial — user-flow acceptance pending |
| ConceptMastery | `backend/foundation/models.py:1822` (`ConceptMastery`) | Partial — user-flow acceptance pending |
| ModelPolicy | `backend/foundation/models.py:784` (`ModelPolicy`) | Partial — user-flow acceptance pending |
| ImmutableAuditLog | `backend/foundation/models.py:2117` (`ImmutableAuditLog`) | Partial — user-flow acceptance pending |

## Completion rule

For each user outcome: develop → focused tests → security audit → commit → normal push → verify remote SHA. Finish a usable vertical flow with observable acceptance evidence before starting unrelated technical work. Do not mark requirements complete from model/API presence, historical reports or simulated tests alone.
