# Staging/Target Smoke Runbook - 2026-07-08

## Alcance

Ejecutar la matriz AdminApps + ISO Smart + MedSupplier en staging/target controlado, con configuracion equivalente a produccion pero sin exposicion publica final.

No declarar produccion. No tocar dominio, DNS, certificados, HTTPS publico, Nginx publico, Certbot ni deploy productivo final.

## Reglas Operativas

- No imprimir secretos.
- No imprimir `.env` reales.
- No imprimir tokens completos.
- No imprimir passwords.
- No imprimir API keys.
- No activar fallback.
- No crear bypasses.
- No marcar PASS una prueba no ejecutada.
- Usar `--no-fallback` como gate obligatorio.

## Placeholders

Reemplazar en el entorno seguro de ejecucion:

- `<ADMINAPPS_PROJECT_PATH>`
- `<ISOSMART_PROJECT_PATH>`
- `<MEDSUPPLIER_PROJECT_PATH>`
- `<ADMINAPPS_VENV_PYTHON>`
- `<ISOSMART_VENV_PYTHON>`
- `<MEDSUPPLIER_VENV_PYTHON>`
- `<ADMINAPPS_INTERNAL_BASE_URL>`
- `<ADMINAPPS_INTEGRATION_BASE_URL>`
- `<QA_ORG_SLUG>`
- `<QA_ORG_ID>`
- `<DENIED_ORG_SLUG>`
- `<ISO_SMART_LOGIN_URL>`
- `<CONTROLLED_QA_EMAIL>`

Secrets deben venir del secret manager, CI masked variables o entorno protegido. No pegarlos en comandos compartidos.

## 1. Preflight Por Repositorio

```bash
git status --short --branch
git branch --show-current
git log --oneline -n 10
git diff --stat
```

Esperado:

- Rama `hardening/p0-p1-enterprise-readiness`.
- Sin working tree sucio no explicado.
- Sin merge a `main` o `master`.
- Sin tags de release.

## 2. AdminApps QA

```bash
cd <ADMINAPPS_PROJECT_PATH>
<ADMINAPPS_VENV_PYTHON> manage.py check
<ADMINAPPS_VENV_PYTHON> manage.py makemigrations --check --dry-run
<ADMINAPPS_VENV_PYTHON> manage.py migrate --plan
<ADMINAPPS_VENV_PYTHON> manage.py test apps.products.tests apps.integration.tests
```

### AdminApps Smokes HTTP

Health sin key:

```bash
curl -sS -o /tmp/adminapps-health-no-key.json -w "%{http_code}\n" \
  "<ADMINAPPS_INTEGRATION_BASE_URL>/health/"
```

Esperado: HTTP 401.

API key invalida:

```bash
curl -sS -o /tmp/adminapps-health-invalid-key.json -w "%{http_code}\n" \
  -H "X-API-Key: invalid-staging-smoke-key" \
  "<ADMINAPPS_INTEGRATION_BASE_URL>/health/"
```

Esperado: HTTP 401.

API key valida:

```bash
curl -sS -o /tmp/adminapps-health-valid-key.json -w "%{http_code}\n" \
  -H "X-API-Key: ${ADMINAPPS_API_KEY:?masked env var required}" \
  "<ADMINAPPS_INTEGRATION_BASE_URL>/health/"
```

Esperado: HTTP 200. No imprimir la key.

Validate ISO Smart:

```bash
curl -sS -o /tmp/adminapps-validate-isosmart.json -w "%{http_code}\n" \
  -H "X-API-Key: ${ADMINAPPS_API_KEY:?masked env var required}" \
  "<ADMINAPPS_INTEGRATION_BASE_URL>/organizations/<QA_ORG_ID>/products/ISO_SMART/validate/"
```

Esperado:

- HTTP 200.
- `allowed=true`.
- `reason=ok`.
- `billing_status=active`.
- `source=adminapps`.
- `fallback=false`.

Validate MedSupplier:

```bash
curl -sS -o /tmp/adminapps-validate-medsupplier.json -w "%{http_code}\n" \
  -H "X-API-Key: ${ADMINAPPS_API_KEY:?masked env var required}" \
  "<ADMINAPPS_INTEGRATION_BASE_URL>/organizations/<QA_ORG_ID>/products/MEDSUPPLIER/validate/"
```

Esperado:

- HTTP 200.
- `allowed=true`.
- `reason=ok`.
- `billing_status=active`.
- `source=adminapps`.
- `fallback=false`.

## 3. ISO Smart QA

```bash
cd <ISOSMART_PROJECT_PATH>
<ISOSMART_VENV_PYTHON> manage.py check
<ISOSMART_VENV_PYTHON> manage.py makemigrations --check --dry-run
<ISOSMART_VENV_PYTHON> manage.py migrate --plan
<ISOSMART_VENV_PYTHON> manage.py test authentication.tests integration.tests
<ISOSMART_VENV_PYTHON> manage.py check_isosmart_adminapps --organization-slug <QA_ORG_SLUG> --no-fallback
```

Esperado para `check_isosmart_adminapps`:

- `adminapps_available=True`.
- `product_access_source=adminapps`.
- `iso_smart_access_enabled=True`.
- `iso_smart_access_reason=ok`.
- `billing_status=active`.
- `fallback_allowed=False`.
- Sin fallback usado.

### Login Real Controlado

Ejecutar desde un shell que ya tenga credenciales QA en variables masked:

```bash
curl -sS -o /tmp/isosmart-login-positive.json -w "%{http_code}\n" \
  -H "Content-Type: application/json" \
  -d '{"email":"'"${CONTROLLED_QA_EMAIL:?masked env var required}"'","password":"'"${CONTROLLED_QA_PASSWORD:?masked env var required}"'"}' \
  "<ISO_SMART_LOGIN_URL>"
```

No imprimir `/tmp/isosmart-login-positive.json` completo si contiene tokens.

Evidencia esperada, reportada de forma sanitizada:

- HTTP 200.
- `access` presente.
- `refresh` presente.
- `validate_credentials=1`.
- `validate_product_access=1`.
- `allowed=true`.
- `reason=ok`.
- `source=adminapps`.
- `fallback=false`.
- `product_code=ISO_SMART`.

## 4. MedSupplier QA

```bash
cd <MEDSUPPLIER_PROJECT_PATH>
<MEDSUPPLIER_VENV_PYTHON> manage.py check
<MEDSUPPLIER_VENV_PYTHON> manage.py makemigrations --check --dry-run
<MEDSUPPLIER_VENV_PYTHON> manage.py migrate --plan
<MEDSUPPLIER_VENV_PYTHON> manage.py test <FOCUSED_MEDSUPPLIER_TEST_TARGETS>
<MEDSUPPLIER_VENV_PYTHON> manage.py check_medsupplier_adminapps --organization-slug <QA_ORG_SLUG> --no-fallback
```

Esperado:

- `source=adminapps`.
- `reason=ok`.
- `fallback=false`.
- Scopes activos esperados.

## 5. Prueba Negativa ISO Smart

No mutar SMART3AI piloto.

Tenant negativo sugerido:

- `SMART3AI_DENIED_TEST`
- `smart3ai-denied-test`
- `ISO_SMART_DENIED_TEST`

Precondiciones:

- Organizacion existe.
- Producto `ISO_SMART` existe.
- Entitlement ausente o inactivo.
- Subscription ausente, inactiva o con `billing_status` distinto de `active`, segun contrato.

Smoke AdminApps negativo:

```bash
curl -sS -o /tmp/adminapps-validate-isosmart-denied.json -w "%{http_code}\n" \
  -H "X-API-Key: ${ADMINAPPS_API_KEY:?masked env var required}" \
  "<ADMINAPPS_INTEGRATION_BASE_URL>/organizations/<DENIED_ORG_ID>/products/ISO_SMART/validate/"
```

Esperado:

- HTTP 200 o 403 segun contrato.
- `allowed=false`.
- Reason claro.
- `source=adminapps`.
- `fallback=false`.

Login ISO Smart negativo:

```bash
curl -sS -o /tmp/isosmart-login-denied.json -w "%{http_code}\n" \
  -H "Content-Type: application/json" \
  -d '{"email":"'"${DENIED_QA_EMAIL:?masked env var required}"'","password":"'"${DENIED_QA_PASSWORD:?masked env var required}"'"}' \
  "<ISO_SMART_LOGIN_URL>"
```

Esperado:

- Login bloqueado.
- No se emiten tokens.
- Reason claro.
- HTTP 403 o equivalente controlado.
- `source=adminapps`.
- `fallback=false`.
- Sin HTTP 500.
- Sin bypass.

## 6. Seguridad Staging/Target

Confirmar:

- No secretos en logs.
- No tokens en logs.
- No passwords en logs.
- No API keys en logs.
- No headers sensibles.
- No fallback silencioso.
- No bypass.
- No acceso permitido por defecto.
- HTTP 200 para permitido.
- HTTP 401 para API key invalida.
- HTTP 403 para acceso denegado.
- HTTP 404 para organizacion/producto inexistente, si ese es el contrato.
- HTTP 503 si AdminApps no esta disponible.

## 7. Dictamen

GO CONTROLADO STAGING/TARGET solo si:

- AdminApps PASS.
- ISO Smart PASS.
- MedSupplier PASS.
- Smoke `ISO_SMART` con `--no-fallback` PASS.
- Login real controlado ISO Smart PASS.
- Smoke `MEDSUPPLIER` con `--no-fallback` PASS.
- Prueba negativa controlada PASS.
- `source=adminapps` confirmado.
- `fallback=false` confirmado.
- Sin secretos expuestos.
- Sin bypass.
- Sin produccion publica tocada.

GO WITH RESTRICTIONS si falta host, runner, variables, credenciales, datos o permisos para ejecutar toda la matriz.

NO GO si hay entitlement bypass, tokens antes de validar AdminApps, fallback con `--no-fallback`, contrato incorrecto, regresion MedSupplier, secretos expuestos o smokes criticos fallando por bug real.
