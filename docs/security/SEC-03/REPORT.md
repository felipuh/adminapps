# SEC-03 — Automated secret protection

2026-10-22. Actions workflow runs on push and pull requests targeting the sanitized
branch. Only the event head's ancestry is fetched (no tags or unrelated branches).
Every reachable tree version and commit/tag metadata is scanned; this intentionally
includes more than the PR diff, catching secrets deleted before publication.
The unique root must be `ab54411ad4bccaed536558bed17e5973f9b822e9`;
merging an original lineage fails before scanning its content.

The guard, exact-file review exceptions and regression fixtures are extracted
from that immutable sanitized root, not executed from the candidate PR.
Gitleaks 8.30.1 uses the existing official archive SHA256 pin. Checkout v4.2.2
is pinned to its full SHA, verified against the official actions/checkout tag.
Token permissions are read-only, checkout does not persist credentials, no
application secrets are used, and no raw scanner reports are printed/uploaded.
See [GitHub's secure use guidance](https://docs.github.com/en/actions/reference/security/secure-use).

Validation:

```sh
GITLEAKS=/path/to/pinned/gitleaks python3 scripts/security/test_guard.py
GITLEAKS=/path/to/pinned/gitleaks python3 scripts/security/test_ci_guard.py
```

PASS: safe index/history; tracked .env, SQLite and virtualenv rejected; embedded
synthetic secret rejected; deleted secret in event ancestry rejected; generated
secret value absent from captured stdout/stderr. Official release integrity
verified on a fresh download. Staging and push undergo the same local guard.
GitHub execution status is checked after push and reported separately.

CI is NOT mandatory branch protection. No repository settings were changed.
Workflow changes themselves still require owner review/enforcement; future guard
upgrades must deliberately update the trusted root pin. Historical exposure and
rotation remain open. PRODUCTION_READY = FALSE; PHASE31_5 = EXECUTION_HELD;
S3_DECISION_02A_NOT_CLOSED; NO_DEPLOYMENT; NO_SHARED_DB_MUTATION.
