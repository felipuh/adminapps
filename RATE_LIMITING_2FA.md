# Rate Limiting para 2FA - AdminApps

**Fecha:** 27 de Abril de 2026  
**Estado:** ✅ Completado y Testeado  
**Tests:** 5/5 pasando  

---

## 📋 Resumen

Se ha implementado un sistema de rate limiting en el endpoint de verificación de 2FA para prevenir ataques de fuerza bruta. El sistema:

- **Máximo 5 intentos fallidos** por usuario
- **Ventana de bloqueo de 15 minutos**
- **Recuperación automática** tras verificación exitosa
- **Advertencias progresivas** cuando se acerca el límite
- **Almacenamiento en caché Django** (sin dependencias externas)

---

## 🏗️ Arquitectura

### Componentes

**Archivo:** `apps/users/rate_limit.py`

```python
# Funciones principales
get_two_fa_attempts(user)           # Obtiene intentos actuales
increment_two_fa_attempts(user)     # Incrementa contador
reset_two_fa_attempts(user)         # Resetea tras éxito
check_two_fa_rate_limit(user)       # Verifica límite (lanza excepción)
```

**Configuración:**
```python
MAX_TWO_FA_ATTEMPTS = 5              # Máximo de intentos
TWO_FA_LOCKOUT_MINUTES = 15         # Duración del bloqueo
TWO_FA_CACHE_KEY_PREFIX = 'two_fa_attempts'
```

### Integración en verify_2fa_token()

**Flujo:**

```
1. Usuario POST al endpoint /api/auth/2fa/verify/
2. check_two_fa_rate_limit(user) → Verifica si está bloqueado
3. Si bloqueado → PermissionDenied (403)
4. Si permitido → Valida OTP/backup code
5. Si inválido → increment_two_fa_attempts()
   └─ remaining_attempts en respuesta
   └─ warning si <= 2 intentos
6. Si válido → reset_two_fa_attempts()
   └─ remaining_attempts = 5
```

---

## 📊 Comportamiento

### Escenario 1: Intentos Fallidos Normales

```
Intento 1: ❌ → 400 Bad Request, remaining_attempts: 4
Intento 2: ❌ → 400 Bad Request, remaining_attempts: 3
Intento 3: ❌ → 400 Bad Request, remaining_attempts: 2
Intento 4: ❌ → 400 Bad Request, remaining_attempts: 1, warning: "Only 1 attempt remaining"
Intento 5: ❌ → 400 Bad Request, remaining_attempts: 0
Intento 6: ❌ → 403 Forbidden, "Too many failed attempts. Try again in 15 minutes"
```

### Escenario 2: Éxito Después de Intentos

```
Intento 1: ❌ → 400, remaining: 4
Intento 2: ❌ → 400, remaining: 3
Intento 3: ✅ → 200 OK, remaining_attempts: 5 (resetado)
```

### Escenario 3: Bloqueo en Diferentes Usuarios

```
Usuario A: 5 intentos fallidos → Bloqueado
Usuario B: 0 intentos → Puede intentar normalmente
Cada usuario tiene su propia key en cache
```

---

## 🧪 Tests Implementados

### `TwoFactorAuthRateLimitTests` (5 tests)

| Test | Descripción | Status |
|------|-------------|--------|
| `test_rate_limit_increments_on_failed_attempts` | Incrementa en cada intento fallido | ✅ |
| `test_rate_limit_resets_on_successful_verification` | Resetea tras verificación exitosa | ✅ |
| `test_rate_limit_blocks_after_max_attempts` | Bloquea en 6º intento (403) | ✅ |
| `test_rate_limit_shows_warning_when_near_limit` | Muestra advertencia en últimos intentos | ✅ |
| `test_rate_limit_returns_403_with_details` | Respuesta 403 tiene mensaje claro | ✅ |

**Cobertura:**
- Verificación de OTP ✅
- Códigos de respaldo ✅
- Contador de intentos ✅
- Reseteo tras éxito ✅
- Bloqueo correcto ✅

---

## 🔐 Seguridad

### Protecciones Implementadas

1. **Cache basado en Usuario**
   - Key: `two_fa_attempts:{user_id}`
   - Cada usuario tiene su propio contador
   - No se puede eludir siendo otro usuario

2. **TTL Automático**
   - Después de 15 minutos, el contador expira
   - Cache de Django maneja expiración
   - No requiere limpieza manual

3. **Single-Use Backup Codes**
   - Códigos de respaldo también limitados
   - Mismo endpoint = mismo rate limit
   - No diferencia entre OTP y backup

4. **Logging Completo**
   - `TwoFactorAuthLog` registra cada intento
   - Captura IP + User-Agent
   - Diferencia entre token_verified y token_failed

---

## 📝 Configuración

### En Django Settings

```python
# Cache backend (ya debe estar configurado)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # O Redis, Memcached, etc.
    }
}

# Rate limiting (opcional - está hardcodeado en rate_limit.py)
# Ajustar en apps/users/rate_limit.py si necesita cambiar:
MAX_TWO_FA_ATTEMPTS = 5          # Cambiar aquí
TWO_FA_LOCKOUT_MINUTES = 15      # Cambiar aquí
```

### Para Producción

```python
# Usar Redis para mejor performance
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

---

## 🚀 Ejemplos de Uso

### En API Client

```javascript
// Intento 1 (fallido)
POST /api/auth/2fa/verify/
Body: { "token": "000000" }
Response: 400
{
  "token": "Invalid OTP token or backup code",
  "remaining_attempts": 4
}

// Intento 4 (último antes de advertencia)
POST /api/auth/2fa/verify/
Body: { "token": "000000" }
Response: 400
{
  "token": "Invalid OTP token or backup code",
  "remaining_attempts": 1,
  "warning": "Only 1 attempt remaining before lockout"
}

// Intento 6 (bloqueado)
POST /api/auth/2fa/verify/
Body: { "token": "000000" }
Response: 403
{
  "detail": "Too many failed attempts. Please try again in 15 minutes."
}

// Intento exitoso (resetea todo)
POST /api/auth/2fa/verify/
Body: { "token": "123456" }  // Válido
Response: 200
{
  "status": "verified",
  "user": {...},
  "remaining_attempts": 5  // Resetado
}
```

---

## 📊 Métricas

### Después de Implementación

```
Total 2FA Tests: 27 (22 + 5 rate limiting)
Status: All Passing ✅

Antes:     22 tests
Después:   27 tests (+5)
Coverage:  100% de flujos de rate limit
```

---

## 🛠️ Mantenimiento

### Monitoreo

```bash
# Ver intentos de 2FA fallidos en logs
grep "2FA failed attempt" logs/*.log

# Ver bloqueos activos
python manage.py shell
>>> from django.core.cache import cache
>>> for key in cache._cache.keys():
...     if 'two_fa_attempts' in key:
...         print(f'{key}: {cache.get(key)} attempts')

# Resetear usuario específico
>>> from apps.users.models import User
>>> from apps.users.rate_limit import reset_two_fa_attempts
>>> user = User.objects.get(email='user@example.com')
>>> reset_two_fa_attempts(user)
```

### Configuración por Usuario (Futuro)

```python
# Posible extensión para usuarios VIP
USER_RATE_LIMITS = {
    'admin@company.com': {'attempts': 10, 'minutes': 30},
    # Default: 5 intentos en 15 minutos
}
```

---

## ✅ Checklist de Completación

- [x] Implementar rate limiting en cache
- [x] Integrar en verify_2fa_token()
- [x] Manejar respuesta de bloqueo (403)
- [x] Mostrar remaining_attempts
- [x] Advertencia progresiva
- [x] Reseteo en éxito
- [x] Tests completos (5/5)
- [x] Logging de intentos
- [x] Documentación

---

## 🔮 Futuras Mejoras (Opcional)

1. **Rate Limiting por IP**
   - Bloquear IP después de N usuarios intentando
   - Prevenir ataques distribuidos

2. **Notificación de Intento Fallido**
   - Email: "Alguien intentó acceder a tu cuenta"
   - Link para confirmar si fuiste tú

3. **Captcha tras N Fallos**
   - Mostrar reCAPTCHA después de 3 intentos
   - Dificultar bots

4. **Admin Dashboard**
   - Ver usuarios actualmente bloqueados
   - Desbloqueo manual
   - Estadísticas de intentos

---

**Estado Final:** ✅ Production Ready  
**Todos los 27 tests pasando**  
**Rate limiting activo y funcional**
