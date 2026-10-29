# Offline staging preparation

Run from the AdminApps repository root:

```sh
python3 -B -m unittest discover -s tools/staging_recovery -p 'test_*.py'
python3 -B tools/staging_recovery/preflight.py tools/staging_recovery/plan.example.json
```

Preflight always exits 2 and reports execution BLOCKED. Even structurally valid
local evidence is `STRUCTURALLY_VALID_UNATTESTED`, never deployment PASS. The
example deliberately has no secret references or dependency lock: these require
real provenance, not placeholders. Capacity budgets are provisional planning
reserves; calibrate them with the isolated target's measured workload.

Checks include explicit false bypass/fallback flags, product/authority, HTTPS
endpoint and loopback ports, every PostgreSQL alias, endpoint/role/volume sharing,
canonical path overlap (including symlinks), running process directories, independent
venv configuration, installed package/hashed lock agreement and known incompatible
Django baselines. A lock is metadata evidence, not a vulnerability scan. A declared
cluster ID, credential reference or endpoint is not proof of network isolation.
Remote DNS aliases, all service users, ACLs, loaded settings, TLS and egress rules
remain unverified execution blockers. No app settings or dotenv are loaded by preflight.

20 tests currently cover structural/local checks and historical reproductions.
The two historical source-risk tests load exact baseline Git objects from sibling
`isosmart` and `ISO_Smart_MedSupplier` repositories. Their PASS means the former
risk was reproduced; current regressions live in each consumer's `integration/`.
Tests use temporary local files, mocked transport and no database.

Additional read-only audit tools are separate from preflight:

- `read_only_inventory.py SOURCE_ROOT OUTPUT`: reads systemd/proc and dotenv as
  data, without Django; writes only flags, fingerprints and pseudonymous DB refs.
  Requires the existing `python-dotenv` package. Never writes source configurations.
- `dependency_audit.py REQUIREMENTS...`: run using the interpreter being audited;
  reads distribution metadata, canonicalizes package names and checks requirements.
  Requires existing `packaging`; does not install or import application code.
- `git_matrix.py`: compares local commit objects and sanitized content manifests;
  no fetch, merge, cherry-pick, reset or push.

See `docs/P0_REMEDIATION_STAGING_2026-10-29.md` for the consolidated report and
`docs/evidence/p0-remediation-2026-10-29/` for evidence generated in this execution.

The coordinated AdminApps SSO test supports explicit independent interpreters:

```sh
REC_SSO_ISO_PYTHON=/ISOLATED/iso/venv/bin/python \
REC_SSO_MED_PYTHON=/ISOLATED/med/venv/bin/python \
/ADMINAPP_TEST_PYTHON -B backend/scripts/rec_sso_03b_offline.py
```

The variables affect only the offline subprocess harness. They do not configure
application authentication, services or deployment. The original checkout-local
`.venv` default is retained for existing callers; isolated audits should always
supply both explicit runtimes.
