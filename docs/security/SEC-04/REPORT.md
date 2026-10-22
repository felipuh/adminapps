# SEC-04 — Remediación npm focalizada

2026-10-22 (America/Costa_Rica). Un lote compatible; sin despliegue.

Base limpia: `24b06b3e0233d7baa5c5a4e37310350688d200d0`.
Rama local: `security/rec-git-sec-01-workspace-20261021`.
Upstream: `origin/security/rec-git-sec-01-20261021`, SHA inicial idéntico confirmado con ls-remote.
Raíz única: `ab54411ad4bccaed536558bed17e5973f9b822e9`; sin ascendencia original recuperada.
Único proyecto npm versionado: `frontend/package.json` y `frontend/package-lock.json` (v3).
El build consume también fuentes/CSS del directorio hermano design-system; su manifiesto tiene sólo peer dependencies, sin lockfile ni instalación independiente requerida. No se modifica ese repositorio.

## Inventario

Conteos npm por paquete afectado, no por CVE única: inicialmente 20 (1 Critical, 15 High, 4 Moderate); después 7 (0 Critical, 5 High, 2 Moderate). Se corrigen 13 entradas: 1 Critical, 10 High, 2 Moderate. Producción después: 0 en todas las severidades.
Los JSON adjuntos conservan cada advisory, severidad, rango vulnerable, URL y propagación transitiva; el código de salida 1 de audit completo es esperado y no se oculta.

| Paquete | Severidad inicial | Relación / alcance | Antes → después | Versión corregida instalada o pendiente | Estado |
|---|---|---|---|---|---|
| axios | high | directa / producción | 1.18.1 → 1.20.0 | 1.20.0 | CORREGIDA |
| baseline-browser-mapping | moderate | transitiva / desarrollo | 2.10.38 → 2.11.30 | 2.11.30 | CORREGIDA |
| brace-expansion | high | transitiva / desarrollo | 5.0.6 → 5.0.12 | 5.0.12 | CORREGIDA |
| braces | high | transitiva / desarrollo | 3.0.3 → 3.0.3 | ninguna publicada | PENDIENTE |
| browserslist | high | transitiva / desarrollo | 4.28.4 → 4.29.4 | 4.29.4 | CORREGIDA |
| chokidar | high | transitiva / desarrollo | 3.6.0 → 3.6.0 | migrar cadena Tailwind; propuesta npm 4.3.3 | PENDIENTE |
| fast-glob | high | transitiva / desarrollo | 3.3.3 → 3.3.3 | migrar cadena Tailwind; propuesta npm 4.3.3 | PENDIENTE |
| follow-redirects | high | transitiva / producción | 1.16.0 → 1.16.1 | 1.16.1 | CORREGIDA |
| micromatch | high | transitiva / desarrollo | 4.0.8 → 4.0.8 | migrar cadena Tailwind; propuesta npm 4.3.3 | PENDIENTE |
| nanoid | high | transitiva / desarrollo | 3.3.15 → 3.3.20 | 3.3.20 | CORREGIDA |
| postcss | high | directa / desarrollo | 8.5.15 → 8.5.31 | 8.5.31 | CORREGIDA |
| postcss-nested | moderate | transitiva / desarrollo | 6.2.0 → 6.2.0 | migrar cadena Tailwind; propuesta npm 4.3.3 | PENDIENTE |
| postcss-selector-parser | moderate | transitiva / desarrollo | 6.1.4 → 6.1.5 | 7.1.6 (major) | PENDIENTE |
| proxy-addr | critical | transitiva / producción | 2.0.7 → 2.0.8 | 2.0.8 | CORREGIDA |
| qs | moderate | transitiva / producción | 6.15.2 → 6.16.1 | 6.16.1 | CORREGIDA |
| react-router | high | transitiva / producción | 7.18.0 → 7.18.4 | 7.18.4 | CORREGIDA |
| react-router-dom | high | directa / producción | 7.18.0 → 7.18.4 | 7.18.4 | CORREGIDA |
| source-map-js | high | transitiva / desarrollo | 1.2.1 → 1.2.2 | 1.2.2 | CORREGIDA |
| tailwindcss | high | directa / desarrollo | 3.4.19 → 3.4.19 | migrar cadena Tailwind; propuesta npm 4.3.3 | PENDIENTE |
| vite | high | directa / desarrollo | 8.0.16 → 8.3.5 | 8.3.5 | CORREGIDA |

## Explotabilidad en este repositorio

La evaluación siguiente es inspección de rutas y configuración, no prueba de ausencia universal de explotación. No se identificó una ruta HTTP de producción que satisfaga las precondiciones de los advisories iniciales. El riesgo del servidor dev Vite y de entradas maliciosas al build es condicional y se conserva explícito.

- **axios**: Navegador, XHR por defecto; Node HTTP/2, proxy y data URI no usados. Gadgets requieren contaminación previa de prototipo; no se identificó ese origen. Se actualiza por uso real en autenticación.
- **baseline-browser-mapping**: Browserslist/build con configuración local.
- **brace-expansion**: Minimatch/ESLint de desarrollo; patrones locales, no entrada HTTP.
- **braces**: Sin parche publicado (última 3.0.3). Patrones locales de Tailwind/chokidar/micromatch; anidamiento malicioso en build puede agotar pila.
- **browserslist**: Autoprefixer/build con consultas del proyecto, no consultas remotas de usuarios.
- **chokidar**: Propaga braces por el watcher de Tailwind; sólo desarrollo.
- **fast-glob**: Propaga micromatch/braces por escaneo de fuentes de Tailwind; sólo desarrollo.
- **follow-redirects**: Sólo adaptador Node de Axios; no ejecutado por el cliente navegador ni server.js.
- **micromatch**: Propaga braces por patrones de archivos; sólo desarrollo.
- **nanoid**: Cadena PostCSS de desarrollo; no generación con tamaño controlado por usuarios.
- **postcss**: Build de CSS local; mapas maliciosos requieren entrada no confiable al build. No servicio de transformación CSS de usuarios.
- **postcss-nested**: Propaga postcss-selector-parser; parche exige salir de su rango actual.
- **postcss-selector-parser**: Parche 7.1.6; Tailwind 3/postcss-nested 6 requieren ^6.0.10. Selectores locales, sin CSS no confiable por HTTP.
- **proxy-addr**: Express en producción. server.js no activa trust proxy ni autorización por IP: no se identificó la precondición de subred IPv6 confiada. Parche preventivo prioritario.
- **qs**: Express/body-parser; servidor estático sin parser extended ni formularios configurados. No se identificó entrada al modo vulnerable.
- **react-router**: BrowserRouter/Routes en SPA; no RSC ni servidor de actions. Precondición CSRF RSC ausente.
- **react-router-dom**: Propaga alerta de react-router; SPA sin RSC.
- **source-map-js**: Mapas durante build; no mapas de usuarios procesados en peticiones.
- **tailwindcss**: Propaga ambas cadenas. npm propone 4.3.3, major con migración de configuración/CSS; no se aplica sin validación funcional/visual de esa migración.
- **vite**: Servidor dev expuesto en 0.0.0.0 con allowedHosts; riesgo condicional de editor/rutas si un atacante accede al dev server. Windows no corresponde a este host Linux. Build publicado no incluye servidor Vite.

Fuentes verificadas: [proxy-addr](https://github.com/advisories/GHSA-jqcg-44mw-7w3h), [braces sin parche](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm), [parser corregido en 7.1.6](https://github.com/advisories/GHSA-rj75-hqrm-r3gf). Las versiones instaladas corregidas de la tabla se validan con la auditoría posterior; no se presentan como versiones mínimas históricas.

## Cambio y pendientes

`npm audit fix --ignore-scripts`, sin force, aplica resoluciones dentro de los rangos compatibles. Se elevan mínimos de Axios 1.20.0, React Router DOM 7.18.4, PostCSS 8.5.31 y Vite 8.3.5. React/ReactDOM permanecen 19.2.7 y Tailwind 3.4.19. No overrides, exclusiones, supresiones ni dependencias funcionales eliminadas. Lockfile actualizado incluye las plataformas opcionales de Vite/Rolldown.

Pendientes: braces, chokidar, fast-glob, micromatch y tailwindcss (5 High); postcss-selector-parser y postcss-nested (2 Moderate). Son dos causas raíz propagadas. No hay parche de braces; forzar Tailwind 4 o parser 7 fuera de los rangos actuales no constituye una actualización compatible. Se requiere backport upstream o una migración separada con validación visual/funcional. Fuentes y patrones de build deben seguir siendo confiables. No se declara cierre total de vulnerabilidades.

## Validación

Node 24.21.0 / npm 11.19.0.

- `npm ci --ignore-scripts`: PASS con el lockfile actualizado.
- `npm run build`: PASS (Vite 8.3.5); salida dist ignorada, no publicada.
- `node --test src/services/authRefresh.test.js`: 41/41 PASS (React/ReactDOM/Axios reales; DOM y transporte sintéticos). Incluye refresh, interceptores, logout, errores y aislamiento entre sesiones.
- `verify_clean_clone.py`: PASS en exportación limpia de HEAD, backend sin modificaciones: Django check/imports y 25 pruebas human-session + 7 integración/lifecycle + 21 MFA. Red y DB bloqueadas; no PostgreSQL ni HTTP E2E.
- Primera ejecución backend en workspace encontró sintaxis Python 3.12 dentro de backend/.venv312 no versionado usando Python 3.9. Se resolvió ejecutando el verificador existente sobre `git archive HEAD`, sin alterar código ni entorno operacional.
- Auditoría completa después del lote y de instalación: 7 pendientes; auditoría `--omit=dev`: 0.

Reproducción desde raíz: `(cd frontend && npm ci --ignore-scripts && npm run build && node --test src/services/authRefresh.test.js)`; ejecutar auditorías completas y de producción por separado. Para backend, usar el entorno Python de SEC-02 y una exportación limpia con `scripts/security/verify_clean_clone.py`.

Entrega: revisión de diff, control Gitleaks 8.30.1 del índice y commit, commit y push normal a la rama sanitizada; SHA remoto y estado Git se reportan al finalizar. No se cambia arquitectura IAM, finanzas, secretos ni configuración operacional; no se ejecuta LAB05-B/C/D.

PRODUCTION_READY = FALSE

PHASE31_5 = EXECUTION_HELD

S3_DECISION_02A_NOT_CLOSED
