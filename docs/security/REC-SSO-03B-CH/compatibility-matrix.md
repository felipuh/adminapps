# Compatibilidad — REC-SSO-03B-CH

Los resultados ALLOW/DENY son pruebas offline de código con ORM/transporte simulados. La compatibilidad desplegada y HTTP real es NOT_EVIDENCED. El contrato nuevo requiere corte coordinado; no se ejecutó.

| Combinación | Resultado/estado | Evidencia o dependencia |
| --- | --- | --- |
| AdminApps CH + ISO Smart CH | ALLOW offline; DEPENDIENTE DE CONFIGURACIÓN | ch-adminapps.log, coordinated ISO; requiere registro durable y claves |
| AdminApps CH + MedSupplier CH | ALLOW offline; DEPENDIENTE DE CONFIGURACIÓN | ch-adminapps.log, coordinated MEDSUPPLIER |
| AdminApps CH + consumidor histórico | RECHAZADO INTENCIONALMENTE | Faltan contexto, principal registrado o versión; pruebas históricas conservadas |
| AdminApps histórico + consumidor CH | RECHAZADO INTENCIONALMENTE por validadores; combinación de servidores completa NO COMPROBADA | Respuestas y tokens Decision A rechazados, sin fallback; no E2E mixto |
| Tokens pre-Decision A | DENY | Firma/configuración general no válida para nuevas familias |
| Tokens Decision A | DENY | Nuevo auth_contract, RSA/kid y familia obligatorios |
| Tokens CH propios | ALLOW offline | Firma, issuer, audiencia exacta, producto, tenant y UUID; rol viewer conservado |
| Token ISO en MedSupplier y viceversa | DENY | Prueba coordinada con sujetos y tenants distintos |
| Token CENTRAL como sesión LOCAL | DENY | Validador local y keyring propios |
| Token LOCAL como prueba CENTRAL | DENY | Verificación RSA central antes de introspección |
| Cliente no registrado | DENY | No fila SSOClient vinculada al principal |
| Cliente deshabilitado | DENY | Estado leído en cada operación central |
| Principal deshabilitado/revocado/rotado | DENY | Lifecycle existente y vínculo de fila; rotación requiere rebind explícito |
| API key incorrecta / de otro producto | DENY | Verificador real y vínculo principal/cliente |
| Tenant no permitido o deshabilitado | DENY | M2M explícita + estado activo + membresía vigente |
| Usuario deshabilitado | DENY | Consulta vigente del usuario central |
| MFA pendiente, inválido o generación anterior | DENY | Challenge sin sesión; estado de factor/generación se revalida |
| Prueba central expirada | DENY | Firma/exp y revalidación viva |
| Refresh local con prueba expirada | DENY | Rechazo aun si la envoltura local sigue firmada y vigente |
| Cambio a otro tenant con la misma prueba | DENY | Requiere nueva autenticación central para ese tenant |
| Configuración incompleta / tabla ausente | DENY, error sanitizado | Sin fallback a settings históricos ni claves generales |
| Esquema persistente y datos de registro reales | BLOCKED_BY_EXTERNAL_DEPENDENCY | Migración y provisión fuera del mandato |

No se ofrece compatibilidad permisiva temporal. Los permisos de dominio y B/D/E/F/G no quedan cerrados por este contrato.
