# Plan de activación y reversión — NO EJECUTADO

Estado: BLOCKED_BY_EXTERNAL_DEPENDENCY para laboratorio PostgreSQL/HTTP/E2E. Además existen
bloqueos de implementación local detallados en REPORT.md; este plan NO autoriza activar.

1. Completar políticas de todos los handlers NOT_EVIDENCED, control plane, export/bulk,
   respuestas compuestas, propietario de assistant, jobs y quotas. Revisar el impacto de
   denegaciones funcionales nuevas. Resolver módulos y suscripciones sin inferir E/F/G.
2. Reconciliar CSV contra los URL resolvers efectivos en configuración de laboratorio,
   incluyendo aliases, admin, funciones sin método declarado, DEBUG/static y rutas privadas.
3. Preparar provisión revisable de SSOClient/tenants/grants exactos/membresías. Requiere
   autorización separada para datos reales/configuración/claves y aplicar 0008/0009/0010.
4. Ejecutar en PostgreSQL desechable autorizado: triggers bulk/M2M, fence, carreras de
   rol/membresía/entitlement, replay, generaciones, commit fallido, RLS y constraints de
   referencias anidadas. Nunca atribuir a mocks esos resultados.
5. HTTP real en ambos productos: MFA, cookies/CSRF y Bearer, scope read vs write, 403/404,
   aliases/search/export/bulk, counterpart accounts, usuarios/servicios y caída central.
   Navegadores, tamaño de cookies, carga del fence, formularios 300 s y versiones mixtas.
6. Solo tras aceptación, secuencia central y consumidores coordinada: versiones viejas de
   consumidor no aplican D; versiones nuevas sin evidencia D deniegan. No habilitar flags
   de bypass ni emitir grants genéricos para resolver incompatibilidad. No despliegue en este mandato.

Reversión local: verificar hashes y restaurar solo las rutas modificadas por D desde
before/<repo>/...; retirar solo archivos nuevos enumerados por integrity-final.json. No
reset/rebase, no tocar el índice ni cambios ajenos. Los .decision-d.patch distinguen D del
estado heredado completo; los .initial.diff reflejan cambios previos sobre HEAD. Reversión
real no ensayada. En un entorno activado, rollback a permisos previos puede reabrir brechas;
contener acceso con el mecanismo central aprobado antes de cualquier downgrade. Preservar
historial de revocación y outbox: jamás reducir generaciones o borrar sesiones para recuperar acceso.

Criterios de abortar: cualquier acceso ajeno/privilegio extra, falta de evidencia D, trust
inconsistente, sesiones revocadas aceptadas, exposición de datos de contraparte, pérdida de
CSRF, divergencia de grants/tenant, fallos SQL o política comercial no adjudicada.

S3-IMP-01; S3_DECISION_02A_NOT_CLOSED; PHASE31_5 = EXECUTION_HELD; REC-2FA-04;
REC-SSO-02; REC-SSO-03A; REC-SSO-03B-CH; DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED.
PRODUCTION_READY = FALSE. NO_DEPLOYMENT. NO_COMMIT. NO_PUSH. GOVERNANCE_PRESERVED.
