# LAB05-A — Real local HTTP runtime

2026-10-22. LAB05_A_HTTP_RUNTIME_PASS.

Run from the clean clone prepared by SEC-02, as a non-root user with PostgreSQL
initdb/pg_ctl/psql on PATH:

```sh
.venv-sec02/bin/python backend/lab04/run.py --http-only
```

This opt-in path reuses LAB04 migrations, provisioning SQL, synthetic fixtures,
settings and runtime middleware. It skips the previous LAB04 acceptance suites
and runs only LAB05-A. Python 3.9, PostgreSQL 18.6, two independent WSGI processes,
ephemeral loopback HTTP ports, new private PostgreSQL Unix socket and SCRAM logins.
The application runtime uses real lab04_iam and lab04_control_plane logins, without
SET ROLE. Existing bootstrap/maintenance provisioning remains separate.

`http-result.json` records 12 real HTTP responses and actual SQL session identities:

- IAM login 200; JWT-authorized CP catalog list 200.
- IAM CP route 404; CP IAM login route 404; /admin/ 404 on both.
- IAM logout 200; identical JWT subsequently receives CP 401.
- Instrumented real catalog handler count remains 1 after every denial.
- Fresh libpq connection per request with distinct backend PIDs.
- Revoked JWT plus technical headers still receives 401; technical header alone
  receives 403, without executing the handler.
- PostgreSQL restart preserves revocation: CP 401 and IAM refresh 401.

No Django test client, simulated ORM or mocked auth is used. The only handler
instrumentation counts entry and invokes the unchanged real catalog list method.
The first run reached the restart check but failed an additional refresh check
because the harness used an incorrect URL (404). The corrected complete run passed.

HTTP processes are terminated in finally; PostgreSQL is stopped and owned runtime
files (credentials, database, fixtures) are removed. `cleanup.json` confirms this.
JWTs remain in orchestrator memory and are never included in evidence. No production
configuration, shared database, external integration, billing or financial migration
was used. No event worker or historical Admin was activated. No LAB05-B/C/D work.

SEC-03 server execution is now independently confirmed:
[successful GitHub run for 2189aa5](https://github.com/felipuh/adminapps/actions/runs/39806311153).
This does not enable mandatory branch protection.

PRODUCTION_READY = FALSE; PHASE31_5 = EXECUTION_HELD;
S3_DECISION_02A_NOT_CLOSED; NO_DEPLOYMENT; NO_SHARED_DB_MUTATION.
Historical credential exposure/rotation and dependency advisories remain open.
