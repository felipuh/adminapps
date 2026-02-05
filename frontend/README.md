# Admin Apps Frontend

Sistema de Gestión de Organizaciones y Usuarios para ISO Smart - Comtech Backoffice

## 🛠️ Tecnologías

- **React 18** - Framework UI
- **Vite** - Build tool
- **Tailwind CSS** - Estilos
- **React Router** - Navegación
- **Axios** - Peticiones HTTP
- **Lucide React** - Iconos
- **Recharts** - Gráficas

## 📋 Requisitos

- Node.js 18+
- npm o yarn

## 🚀 Instalación Local

```bash
# Clonar o copiar archivos
cd adminapps-frontend

# Instalar dependencias
npm install

# Copiar archivo de entorno
cp .env.example .env

# Iniciar en modo desarrollo
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

## 🏗️ Build para Producción

```bash
# Generar build optimizado
npm run build

# Preview del build
npm run preview
```

## 🖥️ Despliegue en Servidor (192.168.100.100)

### 1. Preparar directorio

```bash
# En el servidor de producción
sudo mkdir -p /home/aplicacion/projects/adminapps/frontend/logs
cd /home/aplicacion/projects/adminapps/frontend
```

### 2. Copiar archivos

```bash
# Desde la máquina local, transferir archivos
scp -r ./* aplicacion@192.168.100.100:/home/aplicacion/projects/adminapps/frontend/
```

### 3. Instalar dependencias y construir

```bash
cd /home/aplicacion/projects/adminapps/frontend
npm install
npm run build
```

### 4. Configurar PM2

```bash
# Iniciar con PM2
pm2 start ecosystem.config.cjs

# Guardar configuración
pm2 save

# Verificar estado
pm2 status
```

### 5. Configurar Nginx (ya debería estar configurado)

El bloque de servidor para Admin Apps Frontend ya existe en:
`/etc/nginx/conf.d/isosmart-all.conf`

```nginx
upstream react_adminapps {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name adminapps.isosmart.local;
    
    location / {
        proxy_pass http://react_adminapps;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 6. Recargar Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 📁 Estructura del Proyecto

```
adminapps-frontend/
├── public/              # Archivos estáticos
├── src/
│   ├── components/      # Componentes reutilizables
│   │   └── layout/      # Layout principal, Header, Sidebar
│   ├── contexts/        # Contextos de React (Auth)
│   ├── pages/           # Páginas de la aplicación
│   │   ├── LoginPage.js
│   │   ├── DashboardPage.js
│   │   ├── OrganizationsPage.js
│   │   ├── OrganizationDetailPage.js
│   │   ├── UsersPage.js
│   │   ├── SubscriptionsPage.js
│   │   └── SettingsPage.js
│   └── services/        # Servicios de API
├── index.html           # HTML principal (Vite)
├── vite.config.js       # Configuración de Vite
├── tailwind.config.js   # Configuración de Tailwind
├── package.json
└── ecosystem.config.cjs # Configuración de PM2
```

## 🔐 Autenticación

El sistema usa JWT tokens:
- Access token: 8 horas de validez
- Refresh token: 7 días de validez

Los tokens se almacenan en localStorage.

## 🎨 Temas y Estilos

- Tema oscuro con efecto glassmorphism
- Paleta de colores basada en azules (primary) y grises oscuros (dark)
- Componentes reutilizables definidos en `src/index.css`

## 📱 Responsivo

La interfaz es completamente responsiva con:
- Sidebar colapsable en móviles
- Grid adaptativo
- Touch-friendly

## 🔗 URLs

- **Producción**: http://adminapps.isosmart.local
- **API Backend**: http://adminapps.isosmart.local/api/

## 📝 Comandos Útiles

```bash
# Desarrollo
npm run dev

# Build
npm run build

# Preview
npm run preview

# PM2 - Ver logs
pm2 logs adminapps-frontend

# PM2 - Reiniciar
pm2 restart adminapps-frontend

# PM2 - Detener
pm2 stop adminapps-frontend
```

## 🐛 Solución de Problemas

### Error de conexión API
- Verificar que el backend esté corriendo en puerto 8000
- Revisar configuración de CORS en el backend

### Build falla
- Limpiar node_modules y reinstalar: `rm -rf node_modules && npm install`
- Verificar versión de Node.js

### PM2 no inicia
- Revisar logs: `pm2 logs adminapps-frontend`
- Verificar que el build existe: `ls dist/`
