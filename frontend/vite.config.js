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
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            charts: ['recharts'],
          },
        },
      },
    },
    define: {
      'process.env': {},
    },
  }
})
