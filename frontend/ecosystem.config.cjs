module.exports = {
  apps: [
    {
      name: 'adminapps-frontend',
      script: 'server.js',
      cwd: '/home/felipe/proyectos/adminapps/frontend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      error_file: '/home/felipe/proyectos/adminapps/frontend/logs/pm2-error.log',
      out_file: '/home/felipe/proyectos/adminapps/frontend/logs/pm2-out.log',
      time: true
    }
  ]
};
