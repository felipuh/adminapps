# Matriz de compatibilidad de DECISION-A revisada

Estado de todas las pruebas runtime: **NOT_EXECUTED**.
La compatibilidad se evalúa por fuente, no por configuración desplegada.

| Consumidor / canal | Situación actual | P01 original aislado | Requisito de P01-A-R1 / evidencia futura |
| --- | --- | --- | --- |
| ISO Smart login backend/UI | Consume valid legacy, sin challenge en authService; rechaza local sin bypass. | 2FA pierde login; denegar no completa autenticación. | Inicio/verificación SSO, preauth sin cookie, validación ISO_SMART fresca, sin rescate local. AC-A01–A05/A08. |
| ISO Smart cookie, bearer, refresh, switch-org | Cookies/CSRF y bearer; familias JWT sin issuer/audience configurados en SIMPLE_JWT; claims de refresh previos. | No remedia tokens/sesiones anteriores ni validación del receptor. | Mantener CSRF y aislar familias; binding C/H, evidencia central y revalidación/corte B. AC-A06/A07/A09. |
| MedSupplier login backend/UI | Fallback de contraseña y perfil activo; payload central sintetizado; JWT local tras serializer. | Bloqueo insuficiente: denegación central puede llegar a ruta local. | Cerrar ambas vías y la cadena de backends; challenge/verify; validar MEDSUPPLIER fresco antes del JWT. AC-A02/A04/A05/A08. |
| MedSupplier bearer, refresh, switch-org y recuperación | Bearer/localStorage, refresh deriva access, perfiles locales y controles side/account. | Ningún cierre transversal de sesión/autoridad. | Procedencia central verificable, corte de tokens sin prueba suficiente, error terminal; conservar aislamiento supplier/customer. AC-A06/A07/A09/A10. |
| AdminApps clientes propios / login habitual | Flujo 2FA existente y refresh estándar; SSO con contexto y defaults. | Guard solo toca validate_credentials. | Regresión independiente del login 2FA y sus superficies alternas; no admitir tokens de otro canal como atajo. AC-A03/A06/A10. |
| Otros consumidores legacy o emisores auxiliares | Inventario operacional no disponible; emisor diagnóstico ISO registrado en fuente histórica. | Impacto no cuantificado; no presuponer compatibilidad ni excepción. | Inventariar dueño, canal, entorno, client/aud y política; adaptar o deshabilitar ruta antes del corte. No ejecutar ni autorizar emisores retenidos. |

## Coexistencia de versiones y corte

“Nueva” significa versión futura revisada y autorizada; no existe una versión
implementada en esta campaña. Las siguientes conclusiones son condiciones de
diseño, no resultados de pruebas.

| AdminApps | ISO Smart | MedSupplier | Evaluación |
| --- | --- | --- | --- |
| Actual | Actual | Actual | Baseline con NF01 y fallback MS abiertos; no satisface A. |
| Solo guard P01 | Actual | Actual | ISO pierde login 2FA y MS conserva ruta local; no aceptar como remediación global. |
| Adaptado | Adaptado | Actual | MedSupplier impide cierre. Suspender su canal solo sería contención con impacto firmado. |
| Adaptado | Actual | Adaptado | ISO sigue sin flujo 2FA completo; no aceptar compatibilidad global. |
| Actual con SSO existente | Adaptado | Adaptado | Preparación posible en laboratorio autorizado; mientras legacy/rutas antiguas sean alcanzables no declarar cierre de A. |
| Adaptado | Adaptado | Adaptado | Candidato a corte solo con C/H/D/B pertinentes, sesiones previas tratadas y AC completos. Sin evidencia sigue NOT_EXECUTED. |
| Cualquier reversión permisiva | Cualquiera | Cualquiera | Inadmisible como rollback: no reabrir password-only ni quitar validación de receptor. Cerrar canal afectado. |

No exige actualizar todos los procesos simultáneamente: se puede preparar código
por fases, pero ninguna ventana de coexistencia aceptada puede conservar un
camino activo que omita MFA obligatorio. Versiones incompatibles se aíslan o se
cierra temporalmente el canal bajo mandato de impacto. Los clientes viejos pueden
mostrar reautenticación requerida; no reciben sesiones de compatibilidad.

Cada consumidor debe aportar evidencia desde login hasta API protegida, de
rechazo cruzado ISO_SMART/MEDSUPPLIER, y de caída central con perfil/contraseña/
caché previos. Los tests ConsumerTests históricos de transporte no satisfacen
esta matriz.
