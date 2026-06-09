import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import viteCompression from 'vite-plugin-compression'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = env.VITE_API_PROXY_TARGET
  const proxy = apiProxyTarget
    ? {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
          ws: true
        }
      }
    : undefined

  return {
    plugins: [
      vue(),
      viteCompression({
        algorithm: 'gzip',
        ext: '.gz',
        threshold: 10240
      })
    ],
    server: {
      port: 2002,
      strictPort: true,
      host: '0.0.0.0',
      proxy
    }
  }
})
