# REC-SSO-03A — Adjudicación técnica preliminar de DECISION-A

Fecha: 2026-10-14, America/Costa_Rica.
Resultado documental: **DECISION_A_REVISED_PROPOSAL_READY_FOR_HUMAN_APPROVAL**.
Decisión y todos los cambios propuestos: **PROPOSED_PENDING_APPROVAL**.
Pruebas de aplicación y compatibilidad runtime: **NOT_EXECUTED**.

La dirección solicitada queda adoptada como propuesta para revisión humana:
AdminApps será la autoridad central de autenticación y verificación 2FA;
ninguna ruta legacy o local podrá conceder sesión omitiendo un segundo factor
obligatorio; MedSupplier adaptará su autenticación junto con AdminApps e ISO
Smart; errores de autoridad fallarán cerrados; habrá regresiones independientes
y pruebas de compatibilidad entre consumidores. Esto no adjudica una aprobación
ni autoriza implementación, configuración o corte.

## Evaluación frente al contrato actual

Se revisaron [REPORT](../REC-SSO-03/REPORT.md),
[DECISIONS](../REC-SSO-03/DECISIONS.md) y
[APPROVAL_MATRIX](../REC-SSO-03/APPROVAL_MATRIX.md), sus documentos de soporte,
el diff A original y los puntos de autenticación de los tres repositorios.
Las fuentes CT/AA/IS/MS se identifican en
[EVIDENCE de REC-SSO-03](../REC-SSO-03/EVIDENCE.md).
La inspección es estática sobre el worktree, incluidos sus cambios preexistentes.

| Aspecto | Contrato / implementación observada | Evaluación de DECISION-A revisada |
| --- | --- | --- |
| Autoridad | CT1/CT3/CT4 atribuyen identidad, tenant y acceso a AdminApps; CT4 identifica MEDSUPPLIER como producto independiente. | Dirección coherente con autoridad central. Los perfiles locales son proyecciones, no prueba de autenticación. No crear un verificador MFA local. |
| Legacy | AA1: validate_credentials retorna valid=true tras contraseña y membresía activa; no consulta 2FA. NF01 histórico permanece abierto. | El comportamiento no cumple la propuesta cuando 2FA es obligatorio. El diff A aporta únicamente un guard de is_enabled; no es cierre transversal. |
| Protocolo SSO | AA2: login emite desafío ligado a organización/client/audience; verify consume factor y luego emite tokens. REC-2FA-04 conserva commit boundary, generación y antirreplay. | Reutilizar ese flujo, preservando sus garantías. No confundir challenge con sesión ni convertir requires_2fa ausente en éxito. |
| ISO Smart | IS1/IS4: backend consume legacy; serializer exige datos centrales salvo bypass y valida producto fresco; UI usa login sin challenge y sesión cookie/CSRF. | Requiere adaptación coordinada. Rechazar 403 no implementa un flujo 2FA utilizable. Bypass y familias JWT necesitan controles adicionales. |
| MedSupplier | MS1: tras fallo de authenticate se acepta candidate.check_password; sin datos centrales, perfil activo permite fabricar payload. LoginView emite JWT local; ese serializer no valida producto. | Brecha impeditiva. Denegar en AdminApps o retornar None en su backend no cierra la cadena local. Cerrar identidad local y validar MEDSUPPLIER antes de sesión. |
| Fail-closed | CT3 exige 503 si autoridad obligatoria no es validable. Cliente de producto deniega, pero esto no protege todos los caminos de identidad/sesión. | Deny/error debe ser terminal en consumidores. El diff A no sanitiza por sí solo errores de API key, DB, transporte o lectura de estado MFA. |
| Autorización | CT1/CT4 exigen producto; CT3/CT5 conservan permisos QMS y supplier/customer. C/H y D siguen pendientes. | Completar MFA no concede tenant, producto, scope ni permisos de objeto. A no decide audiences, clientes, scopes ni reglas comerciales. |
| Evidencia | REC-SSO-02: 23 PASS / 9 FAIL y 21/21 offline 2FA; REC-2FA-04 tiene cierre histórico con límites SSO/IdP. | Son antecedentes, no nuevos PASS. Ninguna ejecución en REC-SSO-03A acredita runtime, esquema desplegado o producción. |

**Recomendación preliminar: A1 revisada**, conservando denegación legacy para
identidades con 2FA y usando SSO existente con adaptadores de ambos productos.
A2 (legacy versionado con MFA propio) solo se reconsidera mediante decisión
humana documentada; A3 (retiro total legacy) requiere adjudicar su impacto.
No proponer password-only como degradación de servicio.

El estado observado is_enabled es el predicado del candidato, no evidencia de
una política global de enrolamiento obligatorio. Seguridad debe definir qué
identidades requieren MFA y cómo tratar enrolamiento incompleto. Si una política
exige MFA pero no hay factor utilizable, bloquear sesión y dirigir a recuperación
central; nunca inferir exención por ausencia de fila o por fallo al leerla.
No imponer enrolamiento universal por inferencia en esta campaña.

CT4 admite ciertos fallbacks demo/dev explícitos de producto; esa cláusula no
autoriza omitir MFA obligatorio ni fabricar identidad AdminApps. Los fixtures
sintéticos de pruebas deberán permanecer aislados de sesiones reales. No se
amplían excepciones actuales ni se concede una nueva.

## Entregables

- [Revisión del diff A](DIFF_A_REVISED_PROPOSAL.md): alcance compuesto, contrato y errores.
- [Compatibilidad por consumidor](COMPATIBILITY.md): rutas y coexistencia de versiones.
- [Implementación, reversión y aceptación](IMPLEMENTATION_AND_ACCEPTANCE.md).
- [Texto exacto para adjudicación humana](../REC-SSO-03/APPROVAL_MATRIX.md#rec-sso-03a--texto-exacto-para-adjudicación-humana): minuta sin firma ni efecto aprobatorio.

## Dependencias que requieren decisión separada

| ID | Dependencia | Qué debe fijar la autoridad humana | Efecto sobre A |
| --- | --- | --- | --- |
| A-DEP-01 / C | Audience y familias de token | Receptores exactos por entorno; issuer, algoritmo, tipo, ausencia/listas/múltiples aud; diferenciación token local/central y tenant local/UUID. | Bloquea activar login SSO adaptado y aceptar tokens entre productos. Denegación legacy aislada solo sería contención con impacto aprobado, no cierre. |
| A-DEP-02 / C/H | Clientes y principal | client_id por aplicación/canal; relación con audience/producto, operaciones y tenants permitidos del servicio; excepciones legacy explícitas. | El campo client_id declarado no autentica al llamador. Conservar contexto del desafío y ligar verificación/recepción al cliente autorizado. |
| A-DEP-03 / D | Scopes | Matriz rol × producto × entitlement × scope; vacío/desconocido, read/write, namespace y enforcement QMS/supplier/customer. | MFA completa no otorga tenant:write. Bloquea declarar acceso protegido compatible; no exige adjudicar D para documentar A ni para bloquear una ruta insegura. |
| A-DEP-04 / B/C | Refresh, sesiones previas y cambio de tenant | Evidencia de autenticación completa, revalidación, frescura, revocación y corte de tokens sin procedencia verificable. | No confiar en un bool MFA aportado por el navegador. Tokens anteriores sin evidencia suficiente exigen reautenticación central o rechazo según corte firmado. |
| A-DEP-05 / A | Cobertura MFA y recuperación | Enrolamiento, población obligada, canales, soporte, ventana e indisponibilidad aceptable. | Ningún fallback local o superusuario puede convertirse en exención implícita. |
| A-DEP-06 / E/F/G | Política comercial pendiente | Trial, fechas, ownership/beneficiarios según las decisiones existentes. | Preservar política vigente y denegaciones; no seleccionar E/F/G para resolver el login. Conflictos siguen con sus autoridades. |

No se asignan valores de audience/client por parecido con nombres de producto.
Los defaults smart3ai-portfolio en SSO y el emisor diagnóstico ISO descrito en
REC-SSO-03 son inventario de fuente, no registros aprobados. No se ejecuta ese
emisor ni se libera PHASE31_5.

## Preservación y evidencia documental

Se añaden documentos en REC-SSO-03A y una adenda a APPROVAL_MATRIX de REC-SSO-03.
REPORT y DECISIONS de REC-SSO-03 permanecen como antecedentes sin reescritura;
la adenda vincula la recomendación A con este sucesor. B–H, los nueve candidatos
originales, REC-SSO-02 y REC-2FA-04 se conservan.

La [matriz anterior](evidence/APPROVAL_MATRIX.before.md) conserva exactamente los
bytes sellados por REC-SSO-03. Su SHA256SUMS histórico se mantiene: la entrada de
APPROVAL_MATRIX corresponde ahora a esa versión anterior, no a la matriz con
adenda. El [sello sucesor](SHA256SUMS) incluye la matriz actual y este paquete;
no presentar una verificación del sello histórico contra la matriz actual como
si no hubiese habido cambio. El informe de integridad histórico es de su campaña.

[Baseline](evidence/baseline.json), [antecedentes y fuentes](evidence/antecedents.json),
[comparación final](evidence/integrity-final.json) y
[verificaciones documentales](evidence/document-checks.json) registran la revisión.
Cobertura: entradas tracked/untracked no ignoradas de los tres repositorios;
archivos por SHA-256 y symlinks por destino, más artefactos sellados históricos,
incluidos logs ignorados. No se afirma cobertura global de ignored o secretos.
No se cargaron settings/.env, importaron aplicaciones, ejecutaron tests, parches,
migraciones, servicios, DB, autenticaciones, commits, push ni despliegues.

Permanecen **S3-IMP-01 = BLOCKED_PENDING_AUTHORITY**,
**S3_DECISION_02A_NOT_CLOSED** y **PHASE31_5 = EXECUTION_HELD**.
El resultado READY califica únicamente esta propuesta documental; no cierra A,
no cambia aprobaciones y no declara Production Ready.
