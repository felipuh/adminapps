# Propuesta de revisión compuesta del diff A

Estado: **PROPOSED_PENDING_APPROVAL**. Especificación documental del sucesor
**P01-A-R1**; no se generó ni aplicó un parche ejecutable.
[Original P01](../REC-SSO-02/proposals/A-legacy-deny-2fa.patch) permanece intacto.
Su hash no puede aprobarse como si contuviera los componentes futuros de esta ficha.

## Contrato propuesto

AdminApps verifica contraseña y segundo factor. El consumidor establece su
sesión solo a partir de un resultado central completo y validado para ese
contexto, con identidad/membresía/producto vigentes y autorización local de dominio.

Estados semánticos para el adaptador, sin inventar nuevos campos ya disponibles:

| Estado | Evidencia requerida / respuesta | Efecto permitido en consumidor |
| --- | --- | --- |
| Desafío pendiente | Login SSO actual: HTTP 200, requires_2fa=true, challenge_token y vencimiento. | Mostrar OTP/backup/recuperación; conservar solo contexto de preautenticación protegido y efímero. Sin cookie autenticada, access/refresh ni actualización positiva de perfil. |
| Autenticación completa | Respuesta central final con tokens verificables; login puede indicar requires_2fa=false, verify actualmente no lleva ese campo. | Validar esquema según endpoint, firma/tipo/emisor/receptor/cliente/contexto, identidad viva y producto. Después emitir sesión del consumidor según contrato firmado. Ausencia del campo no prueba éxito. |
| Segundo factor requerido en legacy | Tras contraseña válida: HTTP 403, valid=false, code=second_factor_required. | Invitar al flujo SSO; no continuar por EmailBackend/ModelBackend ni otro fallback. No tratar el 403 como factor verificado. |
| Denegación de identidad/autorización | Credenciales inválidas o decisión central negativa. | Denegación terminal sin sesión; distinguir 401 de 403 según contrato y no divulgar detalles sensibles. |
| Autoridad no verificable | Timeout, red/TLS, 5xx, respuesta corrupta/incompleta, DB o lectura de MFA incierta. | 503 sanitizado en adaptador cuando corresponda a autoridad obligatoria; ninguna sesión ni allow cacheado de rescate. Código HTTP aislado nunca equivale a autenticación. |

Conservar rutas centrales /api/integration/sso/login/ y
/api/integration/sso/login/verify-2fa/. El desafío liga usuario, canal, generación,
tenant y contexto client/audience; no aceptar que parámetros del navegador
sustituyan ese contexto al verificar. TTL observado de desafío: 300 s; cambios
a TTL, límites de intentos o recuperación necesitan revisión explícita.

## Componentes del sucesor

Las rutas abajo son targets propuestos relativos a cada repositorio. Sus cambios
exactos y hashes se prepararán solo bajo mandato futuro de implementación.

| Componente | Targets propuestos / revisión | Cambio exigido |
| --- | --- | --- |
| A-R1-AA | AdminApps backend/apps/integration/views.py; sso_views.py solo en los límites contractuales necesarios; documentación/OpenAPI aplicable. | Conservar guard legacy de MFA, comprobar elegibilidad/política central y devolver error estructurado. Capturar fallos de autoridad alrededor de key lookup/lifecycle y consultas, sin exponer excepciones ni devolver valid=true. Mantener protocolo 2FA transaccional. |
| A-R1-MS-identity | MedSupplier backend/integration/client.py, backends.py; authentication/serializers.py; backend/settings.py en cadena de autenticación. | Adaptar transporte de login/verify y resultados tipados. Eliminar aceptación por candidate.check_password y fabricación de admin_apps_data como prueba central. Hacer terminales deny/error/challenge para la cadena completa. Retornar None por sí solo es insuficiente. |
| A-R1-MS-session | MedSupplier authentication/views.py, urls.py; integration/sso_auth.py; frontend/src/services/authService.js y UI/contexto de login identificados en futura implementación. | Introducir preautenticación sin JWT local, adaptar verificación central y validar MEDSUPPLIER fresco antes de sesión. Conservar scope supplier/customer, cuenta y visibilidad. Tratar refresh, cambio de organización, logout, recuperación y tokens en localStorage sin reciclar sesión antigua. |
| A-R1-IS | ISO Smart integration/client.py, backends.py, sso_auth.py; authentication/serializers.py, views.py, urls.py, cookie_auth.py; authService.js y UI de login. | Estados challenge/verify, ninguna cookie autenticada antes de finalizar; mantener CSRF y atributos seguros. Preservar validate ISO_SMART fresco. Cerrar vías locales/bypass para identidades sujetas a MFA y comprobar familias de tokens. |
| A-R1-cross | Ambos settings/validadores, contratos de sesión y suites independientes. | Binding de C/H y permisos D bajo sus decisiones, inventario de emisores/rutas y corte de sesiones antiguas. Probar API directa, no solo UI. Separar cambio de código de activación/configuración. |

El cliente MedSupplier llama raise_for_status antes de interpretar JSON; la
adaptación deberá conservar códigos estructurados como second_factor_required
sin convertir errores arbitrarios en éxito ni exponer respuesta bruta. Preservar
la diferencia entre fallo de credencial de servicio y contraseña del usuario.

Los JWT locales, si se mantienen, serán una representación de sesión derivada de
autenticación central verificada, con procedencia/contexto comprobables. No son
una segunda autoridad de contraseña/2FA. Elegir token central directo o intercambio
a sesión local, su evidencia de MFA y su validación pertenece a A/C/B; un claim
autodeclarado por el frontend o una copia local de is_enabled no basta.

## Alcance adicional imprescindible

Inventariar toda ruta capaz de emitir o aceptar sesión: login central habitual,
SSO, legacy, login local, admin, refresh, bearer, cookies, switch-organization,
reset/cambio de contraseña, recuperación y emisores auxiliares. No se afirma
auditoría exhaustiva ni vulnerabilidad de cada ruta: son superficies que la futura
implementación debe cubrir o cerrar explícitamente. Reset local nunca restablece
autoridad password-only; enrolamiento/desactivación MFA conservan control central.

No resolver colisiones por email/slug, reasignar external_id ni trasladar perfiles
para salvar login. El adaptador debe conservar identidad y tenant canónicos;
ambigüedad o deriva exige denegar y reconciliar por un proceso autorizado.

## Límites del diff y de su aprobación

- No modificar consumo irreversible, antirreplay, generación, auditoría ni
  commit boundary de REC-2FA-04. Si hay fallo después del consumo, no emitir
  sesión y no restaurar TOTP/backup/desafío consumido.
- Sin DDL nueva prevista para el guard/adaptadores básicos. La disponibilidad de
  users.0004 es precondición operacional no verificada; esta frase no aprueba
  migrarla. Evidencia durable de sesión podría requerir diseño/persistencia
  adicional y su gate propio.
- No aplicar P03/P04/P09 por dependencia implícita: C/H/D requieren adjudicación,
  configuración exacta y pruebas de ambos consumidores.
- No cambiar reglas comerciales E/F/G ni desbloqueos financieros/foundation.
- Un futuro artefacto compuesto necesita hashes de todos los archivos/diffs,
  contrato/config por versión, aceptación por consumidor y mandato de código.
  Aprobar dirección A no aprueba automáticamente ese artefacto ni su despliegue.
