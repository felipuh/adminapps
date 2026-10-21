# Enterprise Kickoff Checklist - 2026-07-08

## P0 Bloqueantes

- Ninguno abierto para kickoff local/controlado.

## P1 Altos

- Ejecutar evidencia equivalente en staging/target antes de produccion.
- Formalizar limpieza o rotacion del usuario controlado `iso-smart-controlled-login@smart3ai.local`.
- Mantener `--no-fallback` como gate obligatorio para smokes de kickoff.

## P2 Medios

- Agregar job automatizado que ejecute smokes AdminApps, ISO Smart y MedSupplier con salida sanitizada.
- Registrar evidencia de acceso denegado en ambiente aislado sin tocar la organizacion piloto real.

## Pendientes No Bloqueantes

- Preparar runbook de rollback operacional para datos controlados.
- Agregar evidencia de monitoreo y alertas cuando exista entorno target.

## Evidencia Lista

- AdminApps `check`, `makemigrations --check --dry-run`, `migrate --plan` y tests focalizados PASS.
- ISO Smart `check`, `makemigrations --check --dry-run`, `migrate --plan` y tests focalizados PASS.
- MedSupplier `check`, `makemigrations --check --dry-run`, `migrate --plan` y tests focalizados PASS.
- Smoke ISO Smart `--no-fallback` PASS.
- Smoke MedSupplier `--no-fallback` PASS.
- Login real controlado ISO Smart PASS contra AdminApps.
- Idempotencia de entitlement y usuario controlado verificada.

## Evidencia Faltante

- Staging/target real.
- Dominio publico.
- Certificados publicos.
- Nginx publico.
- Deploy productivo.
- Restore drill y monitoreo productivo.

## Fuera de Alcance

- Dominio.
- DNS.
- Certificados.
- HTTPS publico.
- Nginx publico.
- Deploy productivo.

