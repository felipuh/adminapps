# Offline staging preparation

Run from the AdminApps repository root:

```sh
python3 -B -m unittest discover -s tools/staging_recovery -p 'test_*.py'
python3 -B tools/staging_recovery/preflight.py tools/staging_recovery/plan.example.json
```

The second command intentionally exits 2: it cannot authorize or start infrastructure.
It reports structural plan errors separately from evidence and authorization blockers.
It never imports application settings, reads real dotenv files, connects to a database,
starts a process or performs migrations. The example contains proposed paths and
ports, not provisioned resources. No credentials are accepted or printed by the plan.

The eight policy tests are standalone. The two source-risk tests expect sibling
`isosmart` and `ISO_Smart_MedSupplier` repositories beside AdminApps. They extract
specific functions with AST and execute those functions with synthetic settings;
they never import the applications. Their PASS confirms a risk reproduction, not
a secure runtime. Exact consumer SHAs and offline test results are recorded in
`docs/evidence/staging-recovery-2026-10-29/`.

This tool is **not an installed startup guard**. Effective settings validation,
fresh-cluster provenance, role/ACL checks, secret provenance, private TLS, RAM/CPU
budgets and collision-free ports remain mandatory before a future authorized
runner can start. The filesystem paths and database names in a plan are not proof
of isolation. Do not replace these gates with self-asserted manifest approvals.

See the four `docs/STAGING_*_2026-10-29.md` recovery reports for infrastructure,
security, the execution matrix and the verdict. No operational startup, shutdown,
SQL, health or smoke runner is claimed ready while capacity and isolation are blocked.
