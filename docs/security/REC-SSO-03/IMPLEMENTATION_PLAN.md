# Implementación futura, aceptación y recuperación

**PROPOSED_PENDING_APPROVAL. Ningún slice está autorizado para ejecución por
este documento.** Especifica unidades mínimas revisables; aprobar política,
aprobar código y autorizar intervención operacional son actos separados.

## Orden y separación de intervenciones

Primero adjudicar A, después C/binding H, D, B y E/F/G/resto H. La implementación
debe respetar dependencias: enforcement D necesita C/H y frescura B; la mitigación
de A no puede esperar al rediseño comercial, pero tampoco puede dejar fallback
de identidad abierto. S0 prepara contratos; S1 prepara consumidores; S2 cierra
legacy; S3/S4 cubren confianza/autorización con S5 para frescura; S6/S7 atienden
política comercial. No desplegar una parte que afirme garantías de otra pendiente.

| Slice | Cambio mínimo y orden interno | Clase / prerrequisitos | Salida verificable futura | Recuperación propuesta |
| --- | --- | --- | --- | --- |
| S0 | Firmar decisiones y contratos/versiones, inventario de familias JWT/clientes/operaciones y matriz de permisos. | Documental/configuración propuesta. Sin cambios runtime; cada valor requiere dueño/entorno. | A–H con opción y alcance; incertidumbres/cortes explícitos; sin nombres/keys inventados. | Volver a deliberación; nunca transformar silencio en aprobación. |
| S1 | Adaptadores 2FA y UX en ISO/MedSupplier; cerrar fallback identidad de MedSupplier y rutas alternas; conservar cookies/CSRF ISO y control del estado previo al factor. | Código sin nuevas migraciones. Contrato A aprobado; validar prerequisito schema 2FA en gate DB aparte. | AC-A positivo/negativo en ambos productos; cero sesión antes de factor; readiness del consumidor documentado. | Suspender login afectado y reparar hacia delante; no reabrir password-only. |
| S2 | Guard legacy A en AdminApps, preservando protocolo REC-2FA-04; integrar S1 con login/verificación existentes. | Código sin nueva DDL; activación después de S1, o contención con indisponibilidad expresamente aprobada. | NF01 denegado y flujo 2FA íntegro con TOTP/backup; REC-2FA-04 sin regresión. | Mantener guard deny, cerrar canal afectado. No restituir consumos ni activar bypass. |
| S3 | Registro/validación client-aud C; validadores de familias locales/centrales; binding de servicio H; inventario y errores por entorno. | Código + contrato/config. No nueva DDL si registro inmutable configurado es aprobado. Claves/IdP aparte. | AC-C/H con intercambio entre productos y tenant ajeno denegado; tokens válidos correctos funcionan. | Conservar allowlist estricta previamente aprobada o cerrar receptor; no quitar issuer/audience. |
| S4 | Matriz D con tipos validados, emisión y enforcement backend en ambos dominios; añadir validate de producto donde falta. | Código + contrato; usa schema existente. Datos scopes actuales requieren inventario/backfill separado si cambia su significado. | AC-D por rol/producto/objeto, incluidas acciones custom y permisos MedSupplier; scopes vacíos no otorgan. | Mantener última política restrictiva válida; cerrar operaciones afectadas, nunca volver a write universal. |
| S5a | Guard B de rol, revalidación de operaciones sensibles/refresh y bypass de caché positiva; resolver errores/freshness. | Código sin nueva migración, coordinado con S3/S4. No afirmar revocación permanente todavía. | NF06 y revocación básica; outage no concede y refresh no reemite permisos revocados. | Cerrar refresh/operación si autoridad no validable; no volver a snapshot permisivo. |
| S5b | Versión durable de sesión/identidad o mecanismo equivalente adjudicado; eventos/invalidación y corte de tokens viejos. | Diseño DB o IdP, migración independiente, backup/reconciliación. No se inventa schema aquí. | AC-B ida/vuelta, reactivación, logout global/local y concurrencia bajo SLA firmado. | Preservar versiones/revocaciones, invalidar sesiones bajo mandato de cambio; no restaurar autorización antigua. |
| S6 | Implementar E y F adjudicadas: una regla runtime/writers, toggle/PATCH/admin, intervalo y evaluated_at; UX y cachés. | Código sin columnas nuevas; contrato comercial y cohortes firmados. P05/P06 revisados juntos, P07 según frontera elegida. | AC-E/F por producto y todos los writers; no razón contradictoria al cruzar tiempo. | Mantener deny en cohortes inciertas; cualquier restauración de derechos requiere decisión comercial trazable. |
| S7 | Materializar G y principal durable H si aplica: expand/contract, relaciones explícitas, inventario y backfill verificable. | DB/datos/contrato, gates DBA/data owners/cambio. Sin incorporación automática de financial. | AC-G/H, referencias reconciliadas, historia intacta y restore ensayado. | Preferir forward fix/cuarentena; preservar ownership, revocaciones, auditoría y facturas posteriores al backup. |
| S8 | Laboratorio transversal de candidatos aprobados con datos sintéticos, sesiones/HTTP/DB reales y evidencia por producto. | Servicios y persistencia requieren autorización NUEVA de target/fixtures. No usar runtime existente por comodidad. | Matriz completa, sin mocks como única evidencia; rollback ensayado y firmas de consumidores. | Detener y conservar evidencia, cerrar accesos afectados; teardown solo del target autorizado. |

S1/S2/S3/S4/S5a/S6 son **código sin nuevas migraciones**, no “operaciones sin DB”:
su futura ejecución usa modelos y puede requerir que el schema preexistente esté
listo. No equivalen a autorización para ejecutar laboratorio o datos persistentes.
Pruebas unitarias sin I/O pueden prepararse en futura campaña de código; no se
ejecutaron aquí porque el alcance actual es revisión/gobernanza.

## DB e IdP: carriles separados

Se conserva [MIGRATION_READINESS REC-SSO-02](../REC-SSO-02/MIGRATION_READINESS.md)
sin ampliar alcance. Si se autorizara inspección operacional:

1. Verificar target/revisión/settings sin imprimir secretos y contrastar ledger
   con schema real. Precondiciones users.0003 e integration.0005; detener ante
   parcialidad o drift. El grafo offline anterior no determina plan actual.
2. Revisar por separado `users.0004_transactional_2fa` e
   `integration.0006_integration_api_key_lifecycle`; backup cifrado, restore en
   clon autorizado, locks y plan exacto. No migrate general ni --fake.
3. users.0004 agrega generación/contadores/challenges; no revertir consumos y
   estado antirreplay. integration.0006 clasifica legacy plaintext; **no elimina
   plaintext**, ni aporta scopes de principal H. Reverse RunPython noop no
   reconstruye historia. No bajar de versión después de keys hashed/revocaciones.
4. Versiones B3, relaciones G o principal H necesitan diseño/migración propios,
   no incorporarse como dependencias implícitas de los dos targets anteriores.
   organizations.0004, integration.0007, financial, RLS/grants quedan fuera.
5. IdP/algoritmo/rotación: inventario de emisores, receptores y claves por referencia,
   publicación/distribución segura, periodo exacto de coexistencia y revocación.
   No se consulta IdP, generan claves ni se configura OIDC/SAML en esta campaña.

## Acceptance Criteria

Todo resultado abajo es **NOT_EXECUTED en REC-SSO-03**. Los positivos requieren
tenant, identidad, producto y política vigentes; no prueban autorización global.

| ID / vínculo | Caso positivo exigido | Casos negativos mínimos y salida esperada |
| --- | --- | --- |
| AC-A / NF01 / P01 | Sin 2FA autorizado; con 2FA challenge→TOTP/backup correcto→sesión única. | Legacy 2FA 403/valid=false; challenge nunca abre sesión; wrong/expired/replayed factor; cliente/tenant cambiado; error de emisión sin rehabilitar factor. MedSupplier contraseña local+perfil y headers no eluden denegación. |
| AC-C / NF02–03 / P03 | Cada familia local/central funciona solo en receptor/entorno esperado, issuer/aud/client coherentes. | Aud ausente/ajena/mixta/malformada, issuer ausente/ajeno, firma/algoritmo/tipo incorrecto, token local tratado como central, challenge y refresh de otro cliente: denegar antes de sync o sesión. |
| AC-D / NF04–05 / P04 | Scope de rol intersectado con entitlement y permiso de objeto permite acción exacta. | Viewer/auditor write; rol desconocido; scopes vacíos; entitlement suspendido; tenant/producto cruzado; customer contra privado/mutación; request directo sin UI: no escritura ni lectura indebida. |
| AC-B / NF06 / P02 | Rol vigente funciona; reautenticación tras cambio produce nueva política. | Rol obsoleto, revocación de cada entidad, caché positiva+outage, refresh antiguo, rol ida/vuelta/reactivación bajo B3, logout/rotación: no resurrección. Medir SLA, expiración y carreras. |
| AC-E / NF07 / P05–06 | Bajo E2, billing=false sin sub o trial/active con sub efectiva vigente permiten; bajo E1, trial explícito elegible dentro de límites. | E2: no sub, billing bloqueado, null borrando vínculo, toggle/admin/PATCH inconsistentes deniegan. E1: trial fuera de límites o excepción no aprobada deniega. Nunca saltar test para ocultar adjudicación distinta. |
| AC-F / NF08 / P07 | t=inicio y dentro del intervalo; zonas equivalentes; fin null. | t<inicio; t=fin bajo F2 y t>fin; rango invertido/vacío/naive; caché pasada de vigencia; mismo evaluated_at para allowed/reason. |
| AC-G / NF09 / P08 | Dueño y beneficiario explícitos autorizados, preservando historia. | Suscripción ajena, producto ajeno, vínculo expirado/revocado, cambio no autorizado en create/PATCH/toggle/admin/runtime: deny; rollback no reasigna factura ni resucita beneficiario. |
| AC-H / adicional / P09 | Key/principal activo habilita solo tupla aprobada; excepción central auditable dentro de vigencia. | Key correcta en tenant/producto/operación/client ajeno; nombre mutable; registro ausente; excepción vencida; revoked/rotated/fallback; DB en lookup/last_used/audit: deny y error sanitizado. |
| AC-X / transversal | Mismo fixture contractual en los tres productos, sesiones y APIs reales en laboratorio autorizado. | API directa, switch-org, perfil viejo, JWT con IDs locales/externos confundidos, permiso retirado entre consulta y uso; no sync positivo/traslado de tenant por error. Repetir REC-2FA-04 pertinente sin degradar garantías. |
| AC-R / recuperación | Restore probado y reconciliación de hechos posteriores con target/ventana autorizados. | Restauración no reactiva key/beneficiario/sesión revocados, no recupera backup code consumido ni elimina auditoría. Fail-closed durante incertidumbre. |

Los futuros tests deben inspeccionar **efecto** (sesión, lectura/escritura,
proyección, factor consumido), no solo HTTP 200/403 ni existencia de un claim.
Los resultados unitarios son necesarios pero no suficientes para compatibilidad.

## Criterios de salida por campaña futura

Decisiones firmadas y contratos reconciliados; diffs compuestos revisados;
valores por entorno aprobados; consumidores adaptados; inventario/cohortes y
schema verificados en alcance autorizado; positivos/negativos y regresiones con
evidencia real proporcional; rollback ensayado; aceptación explícita de ambos
productos. Fallos pendientes deben quedar con dueño y bloqueo, no “PASS con mocks”.

Ninguno de esos criterios está satisfecho automáticamente por este plan. Incluso
si se cumplen para un slice, S3-IMP-01, S3_DECISION_02A_NOT_CLOSED y PHASE31_5
mantienen sus propios gates. Publicar, commitear o desplegar requiere mandato
expreso posterior; la aprobación de gobernanza no lo concede.
