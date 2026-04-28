import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

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
      vue({
        template: {
          compilerOptions: {
            isCustomElement: (tag) =>
              tag === 'AppHeader' ||
              tag === 'AppFooter' ||
              tag === 'app-header' ||
              tag === 'app-footer'
          }
        }
      })
    ],
    server: {
      port: 2001,
      host: '0.0.0.0',
      proxy
    }
  }
})
