# 📋 ANÁLISIS DEL FRONTEND DE ADMINAPPS - PROBLEMAS IDENTIFICADOS

**Fecha:** 4 de febrero de 2026  
**Estado:** EN RESOLUCIÓN - Se encontraron 3 problemas y se han iniciado correcciones

---

## ❌ PROBLEMAS ENCONTRADOS Y ESTADO DE CORRECCIÓN

### 1. **Error 404: GET /api/organizations/new/** 
**Severidad:** CRÍTICA  
**Estado:** ✅ CORREGIDO

**Causa:** El frontend intenta obtener una organización con ID="new" como si fuera un ID válido.

**Error en el navegador:**
```
GET http://adminapps.isosmart.local/api/organizations/new/ 404 (Not Found)
Error cargando datos: AxiosError: Request failed with status code 404
```

**Solución aplicada:**
- Archivo: `src/pages/OrganizationDetailPage.js`
- Se agregó validación en el `useEffect` para detectar si `id === "new"`
- Si es "new", se redirige a `/organizations` en lugar de intentar obtener datos
- Código añadido:
```javascript
// Validate ID - 'new' is not a valid organization ID
useEffect(() => {
  if (id === 'new') {
    navigate('/organizations', { replace: true });
    return;
  }
  // ... rest of fetchData logic
}, [id, navigate]);
```

---

### 2. **Error 500: GET /api/products/modules/by_organization/?organization_id=new**
**Severidad:** CRÍTICA  
**Estado:** ✅ PARCIALMENTE CORREGIDO

**Causa:** El endpoint existe pero recibe un ID inválido ("new").

**Error en el navegador:**
```
GET http://adminapps.isosmart.local/api/products/modules/by_organization/?organization_id=new 500 (Internal Server Error)
```

**Solución aplicada:**
1. ✅ Agregado servicio `moduleService` en `src/services/api.js` con:
   - `getByOrganization(organizationId)` - valida que organizationId exista
   - Lanza error si `organizationId` es null/undefined
   
2. ⏳ FALTA: Validar en el componente que llama a `moduleService.getByOrganization()` que el ID no sea "new"

**Código agregado en api.js:**
```javascript
export const moduleService = {
  getByOrganization: async (organizationId) => {
    if (!organizationId) {
      throw new Error('organizationId is required');
    }
    const response = await api.get('/modules/by_organization/', { 
      params: { organization_id: organizationId } 
    });
    return response.data;
  },
  // ... otros métodos
};
```

---

### 3. **Error: URL de endpoint incorrecto en API** 
**Severidad:** MEDIA  
**Estado:** ✅ CORREGIDO

**Causa:** El servicio intenta acceder a `/organizations/${id}/settings/` pero el backend usa `/organizations/${id}/organization_settings/`

**Solución aplicada:**
- Archivo: `src/services/api.js`
- Cambio de URLs:
  - `/organizations/${id}/settings/` → `/organizations/${id}/organization_settings/`
  - Aplicado en `getSettings()` y `updateSettings()`

---

## 🔍 INVESTIGACIÓN ADICIONAL REQUERIDA

**Pregunta abierta:** ¿Dónde se llama a `moduleService.getByOrganization("new")`?

El error indica que algún componente o hook está intentando cargar módulos automáticamente cuando la aplicación carga con `organization_id=new`. 

**Posibles ubicaciones:**
1. ❓ Contexto de autenticación (AuthContext.js) - puede estar cargando datos al iniciar
2. ❓ Componente dentro de DashboardPage
3. ❓ Hook personalizado de instalación/inicialización
4. ❓ Middleware/Interceptor de Axios

**Acción recomendada:** Buscar en el código:
```javascript
moduleService.getByOrganization
// o
/modules/by_organization
// o  
products/modules/by_organization
```

---

## 📊 ESTRUCTURA DEL FRONTEND ACTUAL

```
adminapps/frontend/src/
├── App.js                          # Router principal
├── pages/
│   ├── LoginPage.js               # Login
│   ├── DashboardPage.js           # Dashboard principal
│   ├── OrganizationsPage.js       # Listado de organizaciones
│   ├── OrganizationDetailPage.js  # ✅ CORREGIDO - Valida ID "new"
│   ├── UsersPage.js              # Gestión de usuarios
│   ├── SubscriptionsPage.js      # Suscripciones
│   └── SettingsPage.js           # Configuración
├── components/
│   └── layout/
│       └── MainLayout.js          # Layout principal
├── contexts/
│   └── AuthContext.js             # Contexto de autenticación
└── services/
    └── api.js                     # ✅ ACTUALIZADO - URLs correctas y moduleService
```

---

## ✅ CORRECCIONES REALIZADAS

| # | Problema | Archivo | Solución | Status |
|---|----------|---------|----------|--------|
| 1 | URL /settings/ incorrecta | `api.js` | Cambiar a /organization_settings/ | ✅ |
| 2 | ID "new" no validado | `OrganizationDetailPage.js` | Agregar validación y redirect | ✅ |
| 3 | moduleService no existe | `api.js` | Crear servicio con método getByOrganization | ✅ |
| 4 | Llamada con org_id="new" | ❓ DESCONOCIDO | Encontrar componente y validar ID | ⏳ |

---

## 🚀 PASOS SIGUIENTES

1. **Ejecutar esta búsqueda en todo el frontend:**
   ```bash
   grep -r "moduleService.getByOrganization\|by_organization" src/
   ```
   
2. **Si encuentra resultados, validar que:**
   - Solo se llama si `organizationId` es válido (no "new")
   - Se valida antes: `if (organizationId && organizationId !== 'new')`

3. **Reiniciar el servidor de desarrollo:** 
   - El frontend necesita recargar para obtener las URLs corregidas

4. **Probar flujo completo:**
   - ✅ Crear nueva organización (debe quedar en modal, no navegar)
   - ✅ Ver detalle de organización existente
   - ✅ Cargar módulos sin errores

---

## 📝 RESUMEN TÉCNICO

**Archivos modificados:**
- `/home/aplicacion/projects/adminapps/frontend/src/services/api.js` ✅
- `/home/aplicacion/projects/adminapps/frontend/src/pages/OrganizationDetailPage.js` ✅

**Cambios en api.js:**
- Corrección de URL: `/settings/` → `/organization_settings/` (2 métodos)
- Nuevo servicio: `moduleService` con 5 métodos

**Cambios en OrganizationDetailPage.js:**
- Nuevo useEffect para validación de ID "new"
- Redirección automática si ID es "new"

---

**Prioridad:** 🔴 ALTA  
**Última actualización:** 4 de febrero de 2026 - 18:30 CDMX

