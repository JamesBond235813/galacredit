import fs from 'node:fs'
import { resolve } from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import viteCompression from 'vite-plugin-compression'

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
      }),
      viteCompression({
        algorithm: 'gzip',
        ext: '.gz',
        threshold: 10240
      })
    ],
    server: {
      port: 2443,
      host: '0.0.0.0',
      proxy,
      https: {
        key: fs.readFileSync(resolve(process.cwd(), 'certs/dev-key.pem')),
        cert: fs.readFileSync(resolve(process.cwd(), 'certs/dev-cert.pem'))
      }
    }
  }
})
