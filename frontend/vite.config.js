import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const hasCustomHmr = Boolean(
    env.VITE_HMR_HOST ||
      env.VITE_HMR_PROTOCOL ||
      env.VITE_HMR_CLIENT_PORT ||
      env.VITE_HMR_PORT,
  )

  const hmr = hasCustomHmr
    ? {
        ...(env.VITE_HMR_HOST ? { host: env.VITE_HMR_HOST } : {}),
        ...(env.VITE_HMR_PROTOCOL ? { protocol: env.VITE_HMR_PROTOCOL } : {}),
        ...(env.VITE_HMR_CLIENT_PORT ? { clientPort: Number(env.VITE_HMR_CLIENT_PORT) } : {}),
        ...(env.VITE_HMR_PORT ? { port: Number(env.VITE_HMR_PORT) } : {}),
      }
    : undefined

  return {
    plugins: [react()],
    server: {
      port: 3000,
      host: '0.0.0.0',
      ...(hmr ? { hmr } : {}),
      allowedHosts: [
        'sso.smart3ai.local',
        'adminapps.smart3ai.local',
        'smart3ai.local',
        'localhost',
        '127.0.0.1',
      ],
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      minify: 'terser',
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules/')) {
              if (
                id.includes('/react/') ||
                id.includes('/react-dom/') ||
                id.includes('/react-router/') ||
                id.includes('/react-router-dom/')
              ) {
                return 'vendor'
              }

              if (id.includes('/recharts/')) {
                return 'charts'
              }
            }
          },
        },
      },
    },
    define: {
      'process.env': {},
    },
  }
})
