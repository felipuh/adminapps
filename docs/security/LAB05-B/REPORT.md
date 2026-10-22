# LAB05-B — Real HTTP invitation and tenant authority

2026-10-22. **LAB05_B_HTTP_INVITATIONS_PASS** — 55 actual HTTP requests,
including expected denials and two controlled PostgreSQL failures.

Baseline: clean `71318e52decb354838e90433cdcddf73e0c78f59`, local branch
`security/rec-git-sec-01-workspace-20261021`, upstream
`origin/security/rec-git-sec-01-20261021`. SEC-04 Actions completed successfully:
[run 39809309924](https://github.com/felipuh/adminapps/actions/runs/39809309924).
No SEC-04 corrective checkpoint was necessary.

Reproduce as a non-root user with the SEC-02 Python environment and PostgreSQL
binaries on PATH, from repository root:

```sh
/path/to/sec02/venv/bin/python backend/lab04/run.py --http-invitations
```

The new opt-in entry reuses LAB05-A's unchanged WSGI server, LAB04 isolated
settings, migrations, provisioning and synthetic fixtures. It runs LAB05-B only;
no LAB04 acceptance suites, npm audit or LAB05-C/D/E. IAM and CP are independent
processes bound to ephemeral 127.0.0.1 ports. PostgreSQL uses a private Unix
socket with TCP disabled and SCRAM runtime logins. No operational settings,
credentials, databases, external services or workers are used.

| Scenario | Result |
|---|---|
| Legitimate IAM authentication | 200 for root, tenant admin, viewer and newly registered invitee |
| Authorized CP organization creation | 201; inactive, no trial/subscription; existing root-only identity activation returns 200 |
| Invitation creation and authorized lookup | 201/200 using real CP endpoints |
| Public preview and IAM acceptance | CP `/api/organizations/invitations/accept/` 200; IAM `/api/auth/register/` 201 |
| Membership persistence | SQL confirms tenant, user role, active/primary membership and accepted timestamp; survives restart |
| Replay | Preview and registration 400, also with a different identity |
| Expired/cancelled invitation | Preview and consumption 400; no user created |
| Inviter authority withdrawn | Membership deactivation over CP HTTP; preview/registration 400; existing inviter JWT gets CP 403 |
| Cross-tenant access | Organization/invitation reads 404; foreign invitation creation and membership reparenting 400 |
| Role and scope escalation | Invitation, registration and membership payloads rejected with 400; viewer invitation creation 403 |
| Session revocation | IAM logout 200; original JWT gets CP 401 before/after restart; refresh 401 |
| Audit/outbox | Committed CP activity rows and tenant versions 1/2/3 persist after restart; outbox pending, attempts=0 |
| Registration rollback | AFTER INSERT SQL failure on membership gives HTTP 500; user and invitation consumption rolled back; retry succeeds |
| Tenant rollback | AFTER INSERT SQL failure on audit gives HTTP 500; name, audit count and outbox count unchanged; retry succeeds |
| Effective PostgreSQL principals | 55 distinct backend PIDs; current_user=session_user is lab04_iam or lab04_control_plane for every request |

The preview endpoint is intentionally in CP; IAM consumes invitations through
registration. No route was invented or moved. Creating tenant identity does not
enable a trial, billing or quotas. The existing explicit activation endpoint is
used only in the disposable laboratory. SQL confirms zero trials/subscriptions
and zero financial migrations.

The unchanged runtime boundary verifies grants, ownership, role memberships and
forbidden capabilities on actual connections. Runtime principals never SET ROLE;
maintenance inspection/fault installation is separate. Faults are actual
PostgreSQL triggers, removed before successful retries; no mocked HTTP/ORM/auth.
The 500 responses are expected test outcomes, not unresolved failures.

Harness corrections during development: inspect data_directory with bootstrap
before assuming the maintenance role; assert 403 (live membership denial), not
401 (session revocation), after inviter membership withdrawal. The final complete
run passes. No application defect requiring a business-code change was found.

[HTTP/SQL evidence](http-result.json) contains no bodies, invitation tokens,
passwords or JWTs. [Cleanup](cleanup.json) confirms removal of the owned runtime;
both HTTP workers were terminated/waited and PostgreSQL stopped. Raw private
failure logs are not published. Full LAB02/LAB04 concurrency suites were not rerun;
this objective preserves their provisioning and transaction mechanisms unchanged.
No business-decision blockers remain for the tested existing invitation contract.
Email delivery is an existing TODO and was not exercised; token retrieval uses
the authorized CP invitation listing, not an external email service.

Publication uses secret review, normal commit/push and remote SHA verification on
the sanitized lineage. No original history, force push or deployment.

PRODUCTION_READY = FALSE

PHASE31_5 = EXECUTION_HELD

S3_DECISION_02A_NOT_CLOSED
