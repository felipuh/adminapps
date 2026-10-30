# November 2026 development baseline

Work only from `development-2026-11-product-completion`. This is a development baseline, not an operational promotion. Existing service checkouts, databases and environment files remain separate.

`PRODUCTION_READY = FALSE` · `PHASE31_5 = EXECUTION_HELD` · `S3_DECISION_02A_NOT_CLOSED` · `NO_DEPLOYMENT` · `NO_SHARED_DB_MUTATION`.

## Reproduction

Linux x86_64, Python 3.12.13, Node 24. Create a NEW independent virtualenv; never point installation at an active service environment. `requirements.txt` remains historical operational input. The lock below is the explicit, separately tested development candidate; no migration or production compatibility is claimed.

```sh
python3.12 -m venv .venv-development
.venv-development/bin/python -m pip install --require-hashes --only-binary=:all: -r backend/requirements-development.lock
.venv-development/bin/python -B scripts/verify_november.py
(cd backend && DJANGO_SETTINGS_MODULE=config.settings_test DJANGO_ENV=test BILLING_SCHEDULER_ENABLED=false ../.venv-development/bin/python -B ../scripts/check_without_io.py)
(cd frontend && npm ci --ignore-scripts --no-audit --no-fund && npm run build)
python3 scripts/security/check_secrets.py --ref HEAD
```

Gitleaks 8.30.1 is required. Its verified download checksum is recorded in `.github/workflows/november-baseline.yml`. The historical regression fixtures contain minimal vulnerable excerpts and are test-only; they remove any dependency on confidential Git ancestry. Lab harnesses remain isolated and are not runtime dependencies.

The frontend consumes the identical reviewed shared Design System 1.0.0-beta.1 archive, pinned by npm integrity and SHA-256 under `frontend/vendor/`. It builds from a standalone checkout without a sibling design-system directory. Change the library at its shared source, then update all consumers from one reviewed package. Development and preview bind to loopback by default; no local TLS setup is required.

Do not start application servers with test settings for real users. Configure central identity/trust and dedicated development data through a separate, reviewed setup. These checks deliberately deny database and network connections; HTTP SSO E2E, PostgreSQL RLS, migrations, persistence and external-user acceptance remain pending. Retained financial capabilities are not activated.

For coordinated SSO regression, place `adminapps`, `isosmart` and `ISO_Smart_MedSupplier` checkouts as siblings, set `REC_SSO_ISO_PYTHON` and `REC_SSO_MED_PYTHON` to their independent virtualenv interpreters, then run `scripts/verify_november.py --ecosystem` with the AdminApps candidate. The default per-repository CI does not claim this cross-product run.
