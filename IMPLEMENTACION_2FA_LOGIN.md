# Implementación de 2FA en Login Flow - AdminApps

**Fecha:** 27 de Abril de 2026  
**Estado:** ✅ Completado  
**Tests:** 22/22 pasando

## Resumen Ejecutivo

Se ha completado la integración de autenticación de dos factores (2FA) en el flujo de login de AdminApps. El sistema ahora:

1. **Detecta 2FA habilitado** durante el login
2. **Devuelve un token temporal** si 2FA es requerido
3. **Valida el OTP/código de respaldo** en un paso separado
4. **Completa el login** después de verificar 2FA exitosamente

## Cambios Implementados

### Backend (Django)

#### 1. **CustomTokenObtainPairSerializer** (`apps/users/serializers.py`)
- ✅ Detecta si el usuario tiene 2FA habilitado
- ✅ Retorna `requires_2fa: True` si está habilitado
- ✅ Devuelve token temporal de acceso para verificación
- ✅ Difiere `record_login()` hasta después de 2FA

```python
# Respuesta cuando 2FA está habilitado:
{
    "requires_2fa": True,
    "access": "<jwt_token_temporal>",
    "user": {
        "id": "...",
        "email": "user@example.com",
        "full_name": "John Doe"
    }
}

# Respuesta cuando 2FA NO está habilitado:
{
    "access": "<jwt_token>",
    "refresh": "<refresh_token>",
    "user": {...full_data...}
}
```

#### 2. **verify_2fa_token()** (`apps/users/views_2fa.py`)
- ✅ Acepta token temporal del login
- ✅ Verifica OTP o código de respaldo
- ✅ Registra login después de verificación exitosa
- ✅ Retorna datos completos del usuario

```python
# POST /api/auth/2fa/verify/
# Header: Authorization: Bearer <temporary_access_token>
# Body: { "token": "123456" }

# Respuesta exitosa:
{
    "status": "verified",
    "message": "OTP token verified successfully",
    "user": {
        "id": "...",
        "email": "user@example.com",
        "full_name": "John Doe",
        "role": "user",
        "organization_id": "...",
        "organization_name": "Test Org",
        "theme": "dark",
        "avatar": "..."
    }
}
```

#### 3. **Pruebas Backend** (`apps/users/tests_2fa.py`)

Nueva clase `LoginWith2FATests` con 6 tests:

- ✅ `test_login_with_2fa_enabled_requires_token` - Login detects 2FA
- ✅ `test_login_without_2fa_enabled_works_normally` - Normal login still works
- ✅ `test_verify_2fa_token_after_login` - OTP verification with temp token
- ✅ `test_verify_2fa_with_backup_code_after_login` - Backup code verification
- ✅ `test_invalid_password_login_fails` - Invalid password rejected
- ✅ `test_2fa_required_is_false_for_user_without_2fa` - Non-2FA users unaffected

**Resultado:** `22 tests passed in 1.032s`

### Frontend (React)

#### 1. **LoginPage.jsx** (`frontend/src/pages/LoginPage.jsx`)
- ✅ Detecta respuesta `requires_2fa: True`
- ✅ Cambia a formulario 2FA
- ✅ Input de 6 dígitos con validación
- ✅ Opción para cancelar y volver a login
- ✅ Maneja backup codes igual que OTP

**Flujo de UI:**
1. Usuario ingresa email/password
2. Si `requires_2fa` es True → muestra pantalla 2FA
3. Usuario ingresa código de 6 dígitos
4. Si válido → completa login y redirige
5. Si inválido → muestra error y permite reintentar

#### 2. **authService** (`frontend/src/services/api.jsx`)
- ✅ Nueva instancia `api2FA` sin interceptores automáticos
- ✅ Método `verify2fa(data, tempToken)` con token temporal
- ✅ Método `login(credentials)` simplificado

```javascript
// Login con manejo de 2FA
const response = await authService.login({
  email: "user@example.com",
  password: "password123"
});

if (response.requires_2fa) {
  // Mostrar formulario 2FA
  const verifyResult = await authService.verify2fa(
    { token: "123456" },
    response.access  // token temporal
  );
}
```

#### 3. **Hook useLoginWith2FA** (Creado pero no usado en LoginPage actual)
- Proporciona alternativa reutilizable
- Mantiene estado separado de login vs 2FA
- Puede usarse en futuros componentes

## Flujo de Autenticación Completo

```
┌─────────────────────────────────────────────────────────┐
│ Usuario entra email + password                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ POST /api/auth/    │
        │ login/             │
        └─────────┬──────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼ (2FA habilitado)        ▼ (2FA no habilitado)
┌─────────────────┐    ┌──────────────────────┐
│ requires_2fa:   │    │ access_token +       │
│ True +          │    │ refresh_token +      │
│ temp_token      │    │ user_data            │
└────────┬────────┘    └──────────┬───────────┘
         │                        │
         │                        ▼
         │                   ✅ Login completo
         │
         ▼
   ┌──────────────────┐
   │ Mostrar OTP UI   │
   │ (6 dígitos)      │
   └────────┬─────────┘
            │
            ▼
    ┌──────────────────────┐
    │ POST /api/auth/2fa/  │
    │ verify/              │
    │ Token: <temp_token>  │
    └───────┬──────────────┘
            │
   ┌────────┴────────┐
   │                 │
   ▼ (válido)        ▼ (inválido)
┌──────────┐    ┌──────────────┐
│ user_    │    │ Mostrar      │
│ data +   │    │ error +      │
│ record   │    │ reintentar   │
│ login    │    └──────────────┘
└────┬─────┘
     │
     ▼
  ✅ Login completado
```

## Seguridad

### Consideraciones Implementadas

1. **Token Temporal**
   - Tiene el mismo tiempo de expiración que tokens regulares
   - No puede ser usado para acceder a endpoints sensibles (solo 2FA)
   - Se genera únicamente cuando 2FA está habilitado

2. **Auditoría**
   - `TwoFactorAuthLog` registra cada intento
   - Captura IP y User-Agent
   - Diferencia entre OTP y backup code

3. **Rate Limiting** (recomendado para futuro)
   - Limitar intentos fallidos de OTP
   - Bloquear después de N intentos

4. **Códigos de Respaldo**
   - 10 códigos por usuario
   - Single-use enforcement
   - Marcados como usados inmediatamente

## Validación End-to-End

### Flujo Probado:

```bash
# 1. Usuario sin 2FA intenta login → Success normal
curl -X POST http://127.0.0.1:8001/api/auth/login/ \
  -d '{"email":"no2fa@example.com","password":"Pass123!"}'
# ✓ Recibe access + refresh + user

# 2. Usuario con 2FA intenta login → Requiere OTP
curl -X POST http://127.0.0.1:8001/api/auth/login/ \
  -d '{"email":"with2fa@example.com","password":"Pass123!"}'
# ✓ Recibe requires_2fa: True + temp_access

# 3. Verifica OTP con token temporal
curl -X POST http://127.0.0.1:8001/api/auth/2fa/verify/ \
  -H "Authorization: Bearer <temp_token>" \
  -d '{"token":"123456"}'
# ✓ Recibe user_data completo + confirm login record
```

## Checklist de Completación

- ✅ Backend: Detecta 2FA en login
- ✅ Backend: Retorna token temporal
- ✅ Backend: Verifica OTP/backup code
- ✅ Backend: Registra login tras 2FA
- ✅ Tests: 22 tests pasando
- ✅ Frontend: UI para OTP input
- ✅ Frontend: Manejo de responses
- ✅ Frontend: Error handling
- ✅ Frontend: Soporte para códigos de respaldo

## Próximos Pasos (Opcional)

1. **Rate Limiting** en endpoint de verificación 2FA
2. **Email notification** cuando se detecta nuevo device
3. **Device trust** para recordar dispositivos 30 días
4. **Admin panel** para ver/revocar sesiones 2FA
5. **Backup code generation** UI mejorada

## Notas para el Equipo

- El `access_token` temporal tiene el mismo TTL que los tokens regulares
- El localStorage NO se modifica hasta que 2FA sea verificado exitosamente
- La UI es inline (no modal) para mejor UX
- Los códigos de respaldo funcionan exactamente igual que OTP (6 dígitos)
- El request ID middleware funciona en todo el flujo

## Comandos Útiles

```bash
# Ejecutar tests de 2FA
cd /home/aplicacion/projects/adminapps/backend
./venv_admin/bin/python manage.py test apps.users.tests_2fa -v 2

# Ejecutar solo tests de login con 2FA
./venv_admin/bin/python manage.py test apps.users.tests_2fa.LoginWith2FATests -v 2

# Ver logs de 2FA
./venv_admin/bin/python manage.py shell
>>> from apps.users.models_2fa import TwoFactorAuthLog
>>> TwoFactorAuthLog.objects.filter(event_type='token_verified').values()
```

---

**Versión:** 1.0  
**Autor:** GitHub Copilot  
**Estado:** Production Ready ✅
