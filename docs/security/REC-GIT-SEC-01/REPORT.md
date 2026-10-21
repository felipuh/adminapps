# REC-GIT-SEC-01 — Repository containment

Date: 2026-10-21, America/Costa_Rica.

## Findings and scope

Initial checkout: `lab04/runtime-boundaries-20261021`, HEAD
`047d5868c13402030d1cd01f68b9bc1ca309e57b`, no upstream, clean index/worktree.
15,871 tracked files included `backend/.env`, three SQLite databases,
`.venv`/`venv_admin` dependencies and generated assets. Existing ignores did not
untrack existing entries and missed dot-prefixed virtual environments.

Origin was fetched successfully. `original-refs.json` records every local and
remote-tracking ref inspected, six historical environment blob IDs, variable names,
local dependency object counts and database/environment paths. All original branch
lineages contain historical credential values. The independent LAB04 delivery
`lab04/reviewed-delivery-20261021` (6a8855b208e1fcfecec9618cbc5f435ea0db7dbb)
has 52 files and is only an overlay, not an autonomous application snapshot.

## Delivery

`security/rec-git-sec-01-20261021` is a new orphan branch: no original commit is
its ancestor. It copies the complete tracked application source from the initial
HEAD, including backend apps/config/migrations/templates/static, frontend source
and dependency manifests, integration code, scripts and historical documentation.
It excludes 15,235 private/generated/dependency files, retaining 636 original
paths plus the security control, evidence and a sanitized production template.
The manifest enumerates retained paths and SHA256 checksums. Excluded categories:
`.env`, local SQLite, virtual environments, Python caches, collected static assets,
media uploads and backups. Source static assets and requirements/lockfiles remain.
No package installation, deployment, DB connection or migration was performed.

Only five retained baseline files differ: `.gitignore`, two environment templates,
MFA example documentation and a debug script. The debug script now reads its
password from `ADMINAPPS_DEBUG_PASSWORD`; the MFA example uses a placeholder.
All three environment templates contain variable names with empty values.
Active settings and actual environment values are not modified. The original
worktree's local configurations/dependencies/databases must remain on disk when
its index is aligned to the sanitized snapshot; original branch refs are retained.

37 LAB04 code/evidence files are byte-identical, listed in the manifest. No LAB04
suite was repeated. No LAB05, financial test, SQL architecture or activation work.

## Preventive control

`python3 scripts/security/install.py` installs checksum-pinned Gitleaks 8.30.1
(Linux x64) and shared local Git hooks. The pre-commit hook scans every staged
blob, not working-tree content. The pre-push hook scans all tree versions and
commit/tag metadata reachable from each pushed SHA, including deleted secrets.
Prohibited paths, populated env templates, symlinks and submodules are rejected.
Missing/wrong scanner versions fail closed. Scanner output is restricted to paths,
rule identifiers and line numbers, without matches or credential values.

Run:

```sh
python3 scripts/security/test_guard.py
python3 scripts/security/check_secrets.py
python3 scripts/security/check_secrets.py --ref HEAD
```

Put `~/.local/bin` in PATH or set `GITLEAKS` to the pinned binary. Hooks use the
installed path automatically. Existing worktrees share the hook configuration;
new clones must run the installer. Git hooks can be bypassed by a user and are
not server-side enforcement. Repository owners should require equivalent CI checks
and enable hosting secret protection. No permissions/settings were changed remotely.

Reviewed scanner false positives are restricted by exact path, whole-file SHA256,
rule and line, with reasons. They are integrity hashes, prose, script names and
synthetic negative-test text; there are no directory-wide or credential-pattern
exceptions. Any changed file requires fresh review. The scanner is a detection
control, not mathematical proof that arbitrary unknown secrets cannot exist.

## Validation

- PASS: synthetic safe index; rejected tracked env and vendored environment.
- PASS: staged secret rejected even with a safe unstaged replacement.
- PASS: deleted synthetic secret rejected in reachable history.
- PASS: offline Django application/model imports with synthetic settings and
  DB/network operations blocked; Python source syntax parsing.
- PASS: exact comparison against known historical env values found no matches
  in the delivery; active configuration files not loaded.
- PASS: 37 LAB04 files byte-identical to source HEAD.
- Final index/reachable-object audit, exclusion verification, root commit and
  remote SHA verification are recorded in the execution result. Commit SHA cannot
  be embedded in its own atomic root commit.

The first guard test run exposed a test-fixture staging error (a removed synthetic
.env was re-added by the fixture); the fixture was fixed and the test rerun passed.
The scanner also initially rejected the legitimate `credentials.py` module;
credential JSON patterns were narrowed while retaining that application module.
No failure was treated as a pass.

## Historical exposure remains OPEN

The original refs and remote history have NOT been rewritten, deleted or force
pushed. Original local history is retained. New sanitized publication does NOT
remove copies from existing branches, clones, forks, caches or backups.

Responsible owners must review and revoke/rotate every historical version of:

- `DJANGO_SECRET_KEY`: application signing authority; assess signed sessions,
  password-reset links and dependent JWT/signature uses.
- `SMART3AI_SSO_JWT_SECRET`: shared SSO/JWT signing authority and consumers;
  coordinate rejection of tokens signed with exposed versions.
- `DB_PASSWORD`: corresponding historical database accounts/endpoints; review
  access and rotate where still valid. Do not assume local labels imply safety.
- Literal debug-script account password: identity owner must establish whether
  it was ever valid or reused and rotate/revoke accordingly.
- Documented MFA seed: identity owner must establish whether the example was
  ever enrolled; if so, re-enroll MFA and invalidate recovery material.

Historical SQLite data also requires owner assessment for stored account hashes,
MFA material, sessions, tokens and personal data; its records were not dumped or
used. No credential revocation or rotation is evidenced by this task. Remote
history cleanup, access review and owner-authorized rotation remain separate,
explicit follow-up tasks. Never merge/cherry-pick the original lineage as a parent
of this sanitized root or push original refs under the assumption they are safe.

```
PRODUCTION_READY = FALSE
PHASE31_5 = EXECUTION_HELD
S3_DECISION_02A_NOT_CLOSED
```

`git diff --cached --check` against the empty root reports inherited whitespace
in the copied baseline (including stored patches). This is not a security failure;
those source/evidence files are preserved. New security files are checked
separately. No blanket formatting cleanup is part of this containment change.
