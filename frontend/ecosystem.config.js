module.exports = {
  apps: [{
    name: 'adminapps-frontend',
    script: 'npm',
    args: 'run dev',
    cwd: '/home/aplicacion/projects/adminapps/frontend',
    env: {
      NODE_ENV: 'development',
      PORT: 3000
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    watch: false,
    max_memory_restart: '500M',
    error_file: '/home/aplicacion/projects/adminapps/frontend/logs/error.log',
    out_file: '/home/aplicacion/projects/adminapps/frontend/logs/out.log',
    log_file: '/home/aplicacion/projects/adminapps/frontend/logs/combined.log',
    time: true
  }]
};
