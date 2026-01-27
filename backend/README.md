# Admin Apps - Sistema de Gestión de Organizaciones

Sistema independiente para gestionar organizaciones, usuarios y suscripciones que utilizan ISO Smart.

## 📁 Estructura del Proyecto

```
adminapps/
├── backend/
│   ├── apps/
│   │   ├── api/              # Endpoints generales y dashboard
│   │   ├── organizations/    # Gestión de organizaciones
│   │   ├── users/            # Usuarios y autenticación
│   │   └── subscriptions/    # Planes y suscripciones
│   ├── config/               # Configuración Django
│   ├── logs/
│   ├── media/
│   ├── static/
│   ├── manage.py
│   └── requirements.txt
└── frontend/                 # React (por implementar)
```

## 🚀 Instalación en Rocky Linux

### 1. Crear Base de Datos MySQL

```bash
mysql -u root -p
```

```sql
CREATE DATABASE adminapps_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'adminapps_user'@'localhost' IDENTIFIED BY 'tu_password_seguro';
GRANT ALL PRIVILEGES ON adminapps_db.* TO 'adminapps_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2. Crear Entorno Virtual

```bash
cd /home/aplicacion/projects/adminapps/backend

# Crear entorno virtual
python3.9 -m venv venv_admin

# Activar
source venv_admin/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

```bash
cp .env.example .env
nano .env
# Editar con tus valores reales
```

### 4. Crear Directorios Necesarios

```bash
mkdir -p logs media static staticfiles
```

### 5. Ejecutar Migraciones

```bash
python manage.py makemigrations organizations users subscriptions api
python manage.py migrate
```

### 6. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 7. Cargar Datos Iniciales (Planes)

```bash
python manage.py shell
```

```python
from apps.subscriptions.models import Plan
from decimal import Decimal

# Plan Gratuito
Plan.objects.create(
    code='FREE',
    name='Gratuito',
    description='Plan básico para comenzar',
    price=Decimal('0.00'),
    billing_cycle='monthly',
    max_users=3,
    max_documents=50,
    max_storage_mb=100,
    modules_included=['sca', 'sie'],
    features=['Análisis básico', 'Soporte por email'],
    ai_analysis_enabled=False,
    is_active=True,
    is_featured=False,
    display_order=1
)

# Plan Profesional
Plan.objects.create(
    code='PRO',
    name='Profesional',
    description='Para equipos en crecimiento',
    price=Decimal('499.00'),
    billing_cycle='monthly',
    max_users=10,
    max_documents=500,
    max_storage_mb=2048,
    modules_included=['sca', 'sie', 'asb', 'spm', 'documents', 'risks'],
    features=['Todos los módulos', 'Análisis IA básico', 'Soporte prioritario'],
    ai_analysis_enabled=True,
    ai_monthly_quota=100,
    is_active=True,
    is_featured=True,
    display_order=2
)

# Plan Enterprise
Plan.objects.create(
    code='ENTERPRISE',
    name='Enterprise',
    description='Para grandes organizaciones',
    price=Decimal('1499.00'),
    billing_cycle='monthly',
    max_users=50,
    max_documents=5000,
    max_storage_mb=10240,
    modules_included=['sca', 'sie', 'asb', 'spm', 'documents', 'risks', 'objectives'],
    features=['Todo incluido', 'IA ilimitada', 'Soporte 24/7', 'Personalización'],
    ai_analysis_enabled=True,
    ai_monthly_quota=1000,
    is_active=True,
    is_featured=False,
    display_order=3
)

print("Planes creados exitosamente!")
```

### 8. Iniciar Servidor de Desarrollo

```bash
python manage.py runserver 0.0.0.0:8001
```

### 9. Configurar Gunicorn para Producción

Crear archivo de servicio systemd:

```bash
sudo nano /etc/systemd/system/adminapps.service
```

```ini
[Unit]
Description=Admin Apps Gunicorn Daemon
After=network.target

[Service]
User=aplicacion
Group=aplicacion
WorkingDirectory=/home/aplicacion/projects/adminapps/backend
Environment="PATH=/home/aplicacion/projects/adminapps/backend/venv_admin/bin"
ExecStart=/home/aplicacion/projects/adminapps/backend/venv_admin/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8001 \
    --timeout 120 \
    --access-logfile /home/aplicacion/projects/adminapps/backend/logs/access.log \
    --error-logfile /home/aplicacion/projects/adminapps/backend/logs/error.log \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable adminapps
sudo systemctl start adminapps
```

### 10. Configurar Nginx

Agregar a la configuración de Nginx:

```nginx
# Admin Apps API
location /adminapps/api/ {
    proxy_pass http://127.0.0.1:8001/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Admin Apps Static
location /adminapps/static/ {
    alias /home/aplicacion/projects/adminapps/backend/staticfiles/;
}

# Admin Apps Media
location /adminapps/media/ {
    alias /home/aplicacion/projects/adminapps/backend/media/;
}
```

## 📡 API Endpoints

### Autenticación
- `POST /api/auth/login/` - Iniciar sesión (JWT)
- `POST /api/auth/refresh/` - Refrescar token
- `POST /api/auth/register/` - Registro
- `POST /api/auth/logout/` - Cerrar sesión

### Usuarios
- `GET /api/auth/users/` - Listar usuarios
- `GET /api/auth/users/me/` - Perfil actual
- `POST /api/auth/users/change_password/` - Cambiar contraseña

### Organizaciones
- `GET /api/organizations/` - Listar organizaciones
- `POST /api/organizations/` - Crear organización
- `GET /api/organizations/{id}/` - Detalle
- `GET /api/organizations/{id}/settings/` - Configuración
- `GET /api/organizations/{id}/stats/` - Estadísticas

### Suscripciones
- `GET /api/subscriptions/plans/` - Listar planes
- `GET /api/subscriptions/` - Listar suscripciones
- `POST /api/subscriptions/{id}/activate/` - Activar
- `POST /api/subscriptions/{id}/cancel/` - Cancelar

### Dashboard
- `GET /api/dashboard/` - Dashboard principal
- `GET /api/stats/` - Estadísticas del sistema
- `GET /api/health/` - Health check

## 🔐 Roles de Usuario

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| `superadmin` | Super Administrador | Acceso total |
| `admin` | Administrador | Gestión de Admin Apps |
| `org_admin` | Admin de Organización | Gestión de su organización |
| `iso_manager` | Gestor ISO | Gestión del SGC |
| `auditor` | Auditor | Solo lectura + auditorías |
| `user` | Usuario | Acceso estándar |
| `viewer` | Visualizador | Solo lectura |

## 🔗 Integración con ISO Smart

Admin Apps proporciona autenticación centralizada para ISO Smart mediante JWT.

ISO Smart debe configurar:
```python
# settings.py de ISO Smart
ADMINAPPS_API_URL = 'http://localhost:8001/api'
```

Y validar tokens JWT contra Admin Apps para autenticación.
