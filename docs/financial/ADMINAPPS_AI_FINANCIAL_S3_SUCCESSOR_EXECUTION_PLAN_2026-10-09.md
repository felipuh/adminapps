# S3 Decision 02-A — Successor Execution Plan

Fecha: 2026-10-09, America/Costa_Rica. Documento D.
`S3_SUCCESSOR_PLAN_READY_FOR_APPROVAL`: plan de secuencia y decisiones listo;
no aprobación de implementación productiva ni de ejecución privilegiada.
`S3_POSTGRESQL_AND_IPC_SUCCESSOR_SPECIFICATIONS_READY` solo a nivel de diseño;
IPC necesita elegir contrato antes de construir su harness.

## Prioridad y dependencias

Orden: reconciliación de fuentes (GOV-01) → contrato PG/IPC (PG-01 e IPC-01) →
preparación de cada harness (PG-02 e IPC-02) → revisión de código, SHA y runbook →
autorizaciones runtime independientes (PG-03 e IPC-03) → adjudicación (GOV-02).
Los contratos pueden revisarse independientemente. La integración IPC+DB depende
de ambas autorizaciones. Las carreras/faults completas de S3 siguen pendientes
aunque el aislamiento llegue a pasar; S4–S6 no se habilitan por este plan.

Los IDs REC-* son filas de la [matriz E](ADMINAPPS_AI_FINANCIAL_S3_GOVERNANCE_RECONCILIATION_2026-10-09.md),
no nuevas normas. Cada slice conserva los límites de la solicitud: sin sudo,
servicios, host lab, secretos, DB real, IPC real, contenedores, migraciones,
deployments o Git history operations durante esta revisión.

## S3-PG-01 — Contract & Threat Model

- Objetivo/requisitos: acordar identidad, ownership y autorización efectiva;
  REC-P01–P07, REC-G01. [Documento B](ADMINAPPS_AI_FINANCIAL_S3_POSTGRESQL_ISOLATION_SPECIFICATION_2026-10-09.md),
  Decision 02-A, migraciones 0002–0007, issuer/executor/services y tests.
- Prerrequisitos/dependencias: revisión GOV-01; autoridad de contrato/DBA que
  resuelva diferencias con Amendment 02 sin cambiar retroactivamente V1.1.
- Trabajo/pruebas/evidencias: inventario de fuente, tabla de grants finales,
  ownership 0006, autenticación, ruta serializable executor y revocación; hashes,
  inspección estática y suite offline. No acceso a catálogo vivo.
- Riesgos/STOP: rol issuer sin contrato, defaults desconocidos, trust confundido
  con autenticación, responsabilidad de DB verifier contradictoria.
- Aceptación: modelo revisable con decisiones explícitas, tests PG-T01–11 y
  excepciones documentadas; no exige fingir una implementación completa.
- Autorización: análisis local cubierto; decisión sobre contratos y futuras
  correcciones de producción corresponde a autoridad competente.
- Rollback/cleanup: cambios documentales nuevos; nada operativo que limpiar.

## S3-PG-02 — Isolation Test Harness

- Objetivo/requisitos: transformar PG-T01–11 en harness sintético independiente;
  REC-P01–P07 y REC-X01. Archivos actuales a reutilizar: tests financieros,
  verify_financial_s3_postgres.sh; nuevo sucesor separado después de PG-01.
- Prerrequisitos/dependencias: PG-01 resuelto, versión PG/herramientas disponibles,
  settings sintéticos sin dotenv, HBA aprobada, ownership/rol issuer definidos.
- Trabajo/pruebas: generar fixtures, catálogo allow-listed, conexiones por rol,
  errores SQLSTATE atribuibles y manifests; probar offline parsing, colisiones,
  rutas/symlinks, config incompleta y fallo de cleanup mediante dobles sin servicios.
- Evidencias: código y hash revisados, comandos exactos, resultados offline y
  listado explícito de pruebas runtime todavía no ejecutadas.
- Riesgos/STOP: requerir cambios productivos para hacer pasar fixtures, apuntar
  a DB compartida, usar rol administrador como runtime, stop fallido ocultado.
- Aceptación: harness revisado con teardown comprobable, sin falsas denegaciones
  ni secretos; exposición a clúster real permanece deshabilitada por autorización.
- Autorización: futuras correcciones SQL/servicio precisan alcance separado;
  construir harness local no autoriza ejecutarlo ni instalar herramientas.
- Rollback/cleanup: eliminar solo artefactos nuevos del slice si se descarta;
  nunca tocar trabajo previo. Ningún recurso DB se crea en esta etapa.

## S3-PG-03 — Authorized Runtime Validation

- Objetivo/requisitos: demostrar PG-T01–11 en clúster sintético, REC-P01–P07/X01.
  Archivos: harness de PG-02, fixtures y paquete de evidencia por ejecución.
- Prerrequisitos/dependencias: PG-02 aceptado, SHA aprobado, entorno privado
  identificado, autorización humana escrita para initdb/roles/migraciones
  sintéticos/start/stop/cleanup. Host compartido/DB existente quedan excluidos.
- Pruebas: selectores existentes de B más la nueva matriz de ACL/RLS/funciones,
  autenticación y carreras por FinancialExecutor; negativos con SQLSTATE e invariantes.
- Evidencias: versiones, identidad de sesiones, inventario catálogos, logs
  redactados, salidas/retornos por caso y recursos ausentes al finalizar.
- Riesgos/STOP: destino fuera del manifest, conexión real, secret leak, owner
  incorrecto, test inesperadamente omitido, privilegio excesivo, cleanup fallido.
- Aceptación: controles reales positivos/negativos y cleanup pasan; ningún
  resultado del harness antiguo con trust se eleva a evidencia de credenciales.
- Autorización: **PENDING_AUTHORIZATION**, no ejecutado ni solicitado todavía
  como aprobación ciega; antes deben existir artefactos concretos PG-02.
- Rollback/cleanup: detener clúster propio, confirmar PID/socket ausentes,
  borrar solo raíz temporal comprobada; ante falla conservar evidencia/manifest.

## S3-IPC-01 — Contract & Boundary Model

- Objetivo/requisitos: resolver IPC-C01–08, REC-I01/I02/P06.
  Archivos: [Documento C](ADMINAPPS_AI_FINANCIAL_S3_IPC_ISOLATION_SPECIFICATION_2026-10-09.md),
  interfaces issuer/executor, Decision 02-A y preflight/informe VM.
- Prerrequisitos/dependencias: GOV-01; PG-01 para entrega a DB y rol del issuer.
- Trabajo/pruebas/evidencias: aprobar topología, peer ACL, transporte, framing,
  errores, secretos, revocación/replay y lifecycle; ejemplos sintéticos sin socket.
- Riesgos/STOP: asumir UNIX/broker existente, UID del payload, grupo compartido
  como autorización, mezcla entre tenant y UID, contrato de credencial indefinido.
- Aceptación: tabla peer/endpoint/operación y schema inequívocos con responsables.
- Autorización: análisis cubierto; autoridad técnica debe elegir el contrato
  propuesto. Esto no autoriza cuentas, endpoint ni ejecución.
- Rollback/cleanup: solo propuesta documental, sin efectos externos.

## S3-IPC-02 — Isolation Test Harness

- Objetivo/requisitos: preparar IPC-T01–10 sobre contrato aprobado, REC-I01–I03.
  Archivos futuros: adaptador de transporte test-only, fixtures y harness; nombres
  finales/CLI se fijan al resolver IPC-01, no se presenta un archivo inexistente.
- Prerrequisitos/dependencias: IPC-01 y rol issuer; mecanismo peer aprobado,
  mapa de identidades, aislamiento de directorios y plan de cleanup.
- Trabajo/pruebas: lógica de autorización/framing/errores en memoria, controles
  positivos/negativos y manifest. No bind/listen/connect, pipes ni procesos
  operativos durante preparación; dobles no se etiquetan como evidencia IPC.
- Evidencias: código/hash, schema, resultados unitarios, comandos runtime y
  permisos mínimos por recurso listos para revisión.
- Riesgos/STOP: código que exponga SQL/secretos, fallback permisivo, ausencia
  de límite de frame/deadline, cleanup que borre recursos desconocidos.
- Aceptación: paquete concreto de endpoint/harness/runbook revisado; no IPC PASS.
- Autorización: implementar transporte productivo es scope separado;
  futuros ensayos reales requieren IPC-03 incluso si no usan privilegios.
- Rollback/cleanup: ninguna cuenta/socket creado; conservar evidencia de revisión.

## S3-IPC-03 — Authorized Runtime Validation

- Objetivo/requisitos: probar peers con UIDs efectivos distintos y operación
  permitida/denegada, REC-I01–I03/P06/H02; integración DB solo si PG-03 autorizado.
- Prerrequisitos/dependencias: IPC-02 aceptado, SHA/runbook, cuentas/rutas/units
  sintéticas exactas y autorización explícita de operador sobre entorno aislado.
- Pruebas: IPC-T01–10, lectura/escritura/peer spoof/replay/fallos/cleanup con
  servicio sano; documentar DAC de archivos por separado.
- Evidencias: kernel peer identity, códigos, contador de operaciones, logs
  sin secretos, invariantes DB cuando aplique y recursos ausentes tras teardown.
- Riesgos/STOP: identidad compartida con productos reales, actor no aprobado
  consigue operación, falta trazabilidad, recurso preexistente o cleanup incierto.
- Aceptación: controles efectivos con identidades distintas y sin recursos
  residuales; no sustituir procesos reales con monkeypatch de UID.
- Autorización: **PENDING_AUTHORIZATION**; no hay comando exacto aún porque
  IPC-01/02 no están completados. Este plan no los salta.
- Rollback/cleanup: lifecycle C, stop de procesos propios y eliminación por
  manifest; fallo bloquea conclusión y preserva recursos para adjudicación.

## S3-GOV-01 — Evidence Reconciliation

- Objetivo/requisitos: inventario trazable REC-* y FIN-* aplicables sin falso
  cierre; documentos A–E y JSON de evidencias offline.
- Prerrequisitos/dependencias: estado Git real, hashes previos, fuentes originales.
- Trabajo/pruebas/evidencias: distinguir reportado/reproducido/no ejecutado,
  detectar discrepancias, revisar links/hashes, pruebas seguras y diff.
- Riesgos/STOP: log reconstruido como histórico, fuente faltante, cambios
  concurrentes no explicados o intento de promover una propuesta a aprobación.
- Aceptación: filas con origen, contrato, implementación, evidencia, tests, gaps,
  dependencias y aceptación; inventario y checks nuevos persistentes.
- Autorización: cubierto por esta tarea. Alcance local realizado; archivo primario
  host y resolución de autoridad documental quedan como dependencias externas.
- Rollback/cleanup: conservar archivos previos y no sobrescribir actas históricas.

## S3-GOV-02 — Closure Adjudication

- Objetivo/requisitos: emitir verdict separado host/PG/IPC/S3, REC-H01–H05/G01/G02/X01.
  Archivos: matriz E, documentos A–D, evidencia de futuros runs y acta humana.
- Prerrequisitos/dependencias: paquete host original; PG-03/IPC-03; carreras/faults
  restantes de S3 y reconciliación explícita de versiones/aprobaciones.
- Pruebas/evidencias: revisar reproducibilidad, SHA/identidad/resultado por
  frontera, resultados negativos y cleanup; no convertir totales en cumplimiento.
- Riesgos/STOP: gaps, FAIL/SKIP aplicable, logs ausentes, autoridad no identificada.
- Aceptación: cierre solo de controles suficientemente probados; acta formal
  de autoridad competente para cierre integral. La revisión actual no la concede.
- Autorización: adjudicación formal humana **PENDING_AUTHORIZATION**;
  S4–S6, Phase31.5/Phase32, deployments y Git permanecen sin cambios.
- Rollback/cleanup: correcciones mediante addendum trazable, sin borrar historia.

## Siguiente decisión humana concreta

Primero revisar este paquete y decidir IPC-C01–08 y las discrepancias PG-R01–09,
además de aportar/aceptar la insuficiencia de evidencia primaria host. Autorizar,
si procede, un slice de preparación de harness con scope exacto y responsables;
no una ejecución inmediata del verifier anterior. Las futuras aprobaciones PG-03
e IPC-03 deben citar SHA, entorno, comandos, recursos, STOP y cleanup revisados.
La razón de esos gates es la política explícita de la solicitud §§5.4, 7 y 8,
no una aprobación adicional inventada por esta revisión.
