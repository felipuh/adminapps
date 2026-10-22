# SEC-02 — Clean sanitized checkout

2026-10-22. Remote-only single-branch clone of
`security/rec-git-sec-01-20261021`, baseline `ab54411ad4bccaed536558bed17e5973f9b822e9`
(one root commit, no original ancestry). Original checkout untouched.

Reproduce in a new clone, from its root:

```sh
python3 -m venv .venv-sec02
.venv-sec02/bin/python -m pip install -r backend/requirements.txt
.venv-sec02/bin/python -m pip check
.venv-sec02/bin/python scripts/security/verify_clean_clone.py
(cd frontend && npm ci --ignore-scripts && npm run build)
```

Validated with Python 3.9 and Node 24.21.0 / npm 11.19.0. No manifest changes
were necessary. Child checks receive a minimal environment, deny network and
Django/libpq connections, reject private environment/database files, and forbid
execution of operational settings. Synthetic settings generate an ephemeral key.
The existing syntax check reads tracked settings as source without executing it.

- SEC02_CLEAN_CLONE = PASS
- SEC02_BACKEND_IMPORTS = PASS
- SEC02_DJANGO_CHECK = PASS (zero issues)
- SEC02_CRITICAL_OFFLINE_TESTS = PASS (25 human-session, 7 lifecycle, 21 MFA)
- SEC02_NO_PRIVATE_FILE_DEPENDENCY = PASS
- Frontend lockfile install and production build = PASS; install lifecycle scripts disabled.
- LAB04 runner and all four runtime URL modules import successfully.

These offline tests simulate persistence; they do NOT prove PostgreSQL isolation
or HTTP E2E. PostgreSQL suites were not rerun for SEC-02. Dependency resolution
works but transitive Python dependencies are not fully locked. npm reported
20 dependency advisories (4 moderate, 15 high, 1 critical); no automatic upgrades
or claim of dependency security closure. Build output is ignored, not published.

An initial verifier run rejected the syntax-only read of tracked settings. The
check now forbids execution instead, and the complete focused run passed.

PRODUCTION_READY = FALSE; PHASE31_5 = EXECUTION_HELD;
S3_DECISION_02A_NOT_CLOSED; NO_DEPLOYMENT; NO_SHARED_DB_MUTATION.
Historical credential exposure remains open; no rotation is evidenced.
