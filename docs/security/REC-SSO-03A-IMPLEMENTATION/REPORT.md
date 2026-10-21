# REC-SSO-03A / Decision A — implementación local

Fecha: 2026-10-14, America/Costa_Rica.

Se implementó código coordinado en AdminApps, ISO Smart y MedSupplier en el host de desarrollo `192.168.56.11`. La autorización es la instrucción explícita del usuario de continuar código y pruebas locales de Decision A. No se solicitan nuevas aprobaciones de ese alcance ni se reescriben las adjudicaciones históricas.

**Resultado: implementación local verificada con pruebas offline; activación y cierre E2E pendientes. No Production Ready.** No se aplicaron migraciones, se consultaron bases compartidas, se iniciaron servicios, se hicieron commits, push ni despliegues. Se preservaron `S3-IMP-01`, `S3_DECISION_02A_NOT_CLOSED` y `PHASE31_5 = EXECUTION_HELD`.

## Cambios por repositorio

| Repositorio | Implementación |
| --- | --- |
| `/home/felipe/proyectos/adminapps` | `validate-credentials` rechaza con 403/`second_factor_required` después de verificar contraseña si hay 2FA habilitada; estado MFA/API key/DB falla cerrado y sanitizado. SSO emite procedencia firmada `auth_contract=decision-a-v1`, `amr` y generación MFA; introspection rechaza familia anterior, prueba password-only cuando MFA está habilitada, factores deshabilitados o generación anterior. Verify valida el contexto declarado del consumidor antes del consumo y retorna `requires_2fa=false` al completar. |
| `/home/felipe/proyectos/isosmart` | Serializer y backend eliminan autenticación local y flags de bypass. Adaptador central hace login/challenge/verify/introspection, comprueba contexto exacto y producto ISO_SMART antes de proyección/sesión. Conserva cookies HttpOnly y CSRF; no acepta bearer como sesión de navegador. Access, refresh y switch quedan ligados a prueba central, tenant y UUID de usuario; refresh revalida autoridad viva. UI solicita TOTP o backup y no marca challenge como autenticación. |
| `/home/felipe/proyectos/ISO_Smart_MedSupplier` | Se elimina rescate `candidate.check_password`, identidad fabricada con perfil y fallback JWT sin prueba. Reutiliza el mismo protocolo central con producto fijo MEDSUPPLIER; conserva transporte bearer/localStorage y permisos de dominio existentes. Login/challenge/refresh/switch y UI tienen las mismas denegaciones de procedencia y tenant. |

El emisor local no crea siquiera un refresh local hasta validar la prueba central. Los JWT locales incluyen la prueba de acceso central y su UUID de sujeto, bajo la firma existente; sus expiraciones no exceden la central. No se almacena el refresh central ni se ofrece renovación central silenciosa: al caducar la prueba se requiere autenticación central nueva. No se añadieron claves ni se modificó configuración de confianza. La separación criptográfica de claves/familias pertenece al trabajo pendiente de audiences/clientes.

La proyección nueva utiliza `username=adminapps:<UUID central>`; una cuenta local existente solo se admite si tiene ese vínculo o un mapping explícito de UUID central a PK local. No se toma una cuenta por coincidencia de email, no se reasigna `external_id` por slug y no se repunta un perfil al fallar una constraint. Se mantienen desactivación local, lockout y expiración temporal, además de la elegibilidad central. La restricción owner requiere UUID exacto; configuración incompleta falla cerrada.

El consumo del segundo factor continúa en el servicio transaccional existente. No se modifica `two_factor_service.py`, sus modelos ni REC-2FA-04; una falla posterior de proyección/emisión no restaura factores consumidos.

## Pruebas y evidencia

| Comprobación final | Resultado | Límite |
| --- | --- | --- |
| AdminApps, contratos sucesores | 30/30 PASS | Endpoints reales con ORM/transporte sustituidos; sin DB/red. Incluye regresiones de revocación, tenant, firma, expiración, errores y MFA. |
| ISO Smart, consumidor | 20/20 PASS | Serializer, login/challenge, JWT, refresh y proyección reales; mocks de transporte/ORM. |
| MedSupplier, consumidor | 20/20 PASS | Misma cobertura, incluyendo contraseña local conocida y rechazo central. |
| REC-2FA-04 | 21/21 PASS | Runner offline existente, con guardas de conexiones. |
| Frontend ISO / MedSupplier | 4/4 + 4/4 PASS | Ejecución de la función de login de producción: challenge, incompleto, rechazo y éxito; no navegador. |
| ESLint focalizado | PASS en ambos | Tres archivos frontend modificados por consumidor. |
| Builds frontend | PASS en ambos | Artefactos en `/tmp/decision-a-build-*`, sin sustituir `dist` existente. |
| Diff check | PASS en los tres | Incluye worktrees con cambios previos. |
| Discriminante MedSupplier | Baseline: FAIL; sucesor: PASS | La misma prueba negativa sobre el serializer original respaldado acepta login por contraseña/perfil local pese al rechazo central. No se restaura el worktree para ejecutarla. |

**99 pruebas positivas finales**, además de lint/build y el discriminante baseline intencionalmente fallido. Las suites backend se configuran con settings sintéticos y DB dummy; no cargan settings de despliegue. Las conexiones de aplicación quedan bloqueadas. El transporte SSH solo se usó para operar los repositorios autorizados. No hay evidencia de E2E HTTP real, PostgreSQL, concurrencia persistente, IdP real, versiones mixtas ni corte/reversión.

La suite histórica `rec_sso_02_offline.py` se conserva sin edición. La última corrida reporta **22 PASS / 9 métodos FAIL / 1 ERROR** sobre 32 métodos; unittest muestra 10 entradas FAIL porque incluye subtests. Cinco métodos siguen señalando políticas pendientes: scopes por rol/entitlement, trial/suscripción, inicio futuro y ownership de suscripción. Los demás fallos/error usan tokens históricos sin procedencia nueva o expectativas anteriores del JSON. El sucesor prueba la revocación/producto con una prueba nueva válida: 30/30 PASS. El PASS histórico de audience/rol sobre tokens antiguos rechazados no demuestra cierre de esas decisiones.

Los archivos `checks.json`, logs, `code-hashes.json`, `integrity-final.json`, `baseline.json` y diffs por repositorio contienen los resultados y la trazabilidad. Los parches `*.decision-a.patch` comparan con los bytes previos, **excluyendo cambios ajenos preexistentes**. Los originales editados se conservan en `before/`.

| Baseline Git conservada | Entradas originales | Sin cambios | Archivos originales editados y respaldados |
| --- | ---: | ---: | ---: |
| AdminApps `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` | 15.601 | 15.599 | 2 |
| ISO Smart `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` | 15.053 | 15.045 | 8 |
| MedSupplier `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` | 14.992 | 14.984 | 8 |

HEAD e índice conservados en los tres repositorios; cero modificaciones inesperadas sobre las 45.646 entradas. Los cambios previos ajenos de configuración/financial/foundation y todos los documentos históricos mantienen sus bytes. El SSO previamente modificado conserva su original completo en backup y su diff anterior por separado. Cobertura de integridad: tracked y untracked no ignorados; no se afirma un inventario global de ignored, secretos o datos reales.

## Compatibilidad y bloqueos reales

1. **Registro de receiver pendiente:** el adaptador exige `ADMIN_APPS_SSO` con `BASE_URL` de integración, `ISSUER`, `CLIENT_ID` y `AUDIENCE` explícitos, sin defaults de producto/portfolio. Producción exige HTTPS. No se inspeccionó ni cambió configuración activa; un receiver no registrado queda cerrado. AdminApps sigue sin registro dimensional del principal/API key: no se declara cerrado ese trabajo.
2. **Cuentas existentes:** la reconciliación de proyecciones antiguas necesita mappings explícitos `ADMIN_APPS_USER_BINDINGS` (UUID → PK) cuando no existe identidad canónica. No se ejecutó reconciliación ni se contaron cuentas afectadas. Las coincidencias de email/slug no habilitan acceso. Una instancia owner debe tener `OWNER_ORGANIZATION_EXTERNAL_ID` exacto.
3. **Sesiones anteriores y cambios de tenant:** tokens sin procedencia nueva se rechazan. Cambiar a otro tenant requiere login/challenge central nuevo; no se transforma una prueba de un tenant en otra. El refresh local termina al caducar el access central, aun si antes duraba siete días. Ese impacto requiere validación conjunta antes de activación; no se cambia el gate de despliegue.
4. **Política MFA:** se usa el estado habilitado vigente del factor, sin inferir enrolamiento universal. Definir población obligada sin factor sigue pendiente; esta implementación no inventa una exención ni una política global. Errores de lectura no conceden sesión.
5. **Revocación durable y scopes:** no se resolvieron versiones de sesión/eventos de revocación, ABA de roles, scopes de APIs ni decisiones comerciales E/F/G. Se conserva la política existente; central MFA no demuestra autorización universal.
6. **Validación real:** no se inspeccionó esquema compartido ni se ejecutó laboratorio PostgreSQL. No se certifica runtime desplegado, aceptación de consumidores o todos los AC-A01–AC-A12. El código queda preparado y comprobado en el alcance offline descrito.

## Siguientes pasos

Para el siguiente slice solicitado como **B (audience/clientes)**, registrar por entorno los receivers y principales exactos, vincular credenciales de servicio a cliente/producto/tenant y separar emisores, algoritmos y familias local/central. En la matriz histórica, audiences/clientes corresponden a **C/H**; **B** es la política durable de sesiones y revocación. No se renumeran esos antecedentes.

Para **scopes (D)**, definir la intersección rol × producto × entitlement, vacío/desconocido y read/write; aplicarla al emisor y a cada API/objeto QMS y supplier/customer. Después ejecutar un laboratorio conjunto desechable con configuración explícita, pruebas HTTP/CSRF, expiración, replay/concurrencia y revocación. No se requiere otra aprobación para continuar código y pruebas locales de A; DB, migraciones, servicios compartidos, push y despliegue permanecen fuera del mandato.
