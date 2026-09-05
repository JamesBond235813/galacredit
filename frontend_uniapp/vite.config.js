import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const smsCollectionEnabled = process.env.VITE_SMS_COLLECTION_ENABLED === 'true'

function smsChannelPlugin(enabled, command) {
  return {
    name: 'galacredit-sms-channel',
    enforce: 'pre',
    transform(code, id) {
      // 在生产安全渠道把动态入口改成无权限安全桩，使 Rollup 不会解析真实短信模块。
      if (command !== 'build' || enabled || !id.endsWith('/src/utils/risk.js')) return null
      return { code: code.replace("import('./sms-loader.js')", "import('./sms-disabled.js')"), map: null }
    }
  }
}

function transformRpx() {
  const replaceRpx = (code) => code.replace(/(-?\d+(?:\.\d+)?)rpx/g, (_, value) => `${(Number(value) / 100).toFixed(6).replace(/0+$/, '').replace(/\.$/, '')}rem`)
  return {
    name: 'galacredit-rpx-fallback',
    enforce: 'post',
    transform(code, id) {
      // Vue SFC 样式在构建时使用 `?vue&type=style` 虚拟模块，不一定带 .css 后缀。
      if (!id.includes('.css') && !id.includes('type=style')) return null
      // 用 rem 保持 Android 6/旧 WebView 兼容；运行时根字号会把设计宽限制到 480px。
      return replaceRpx(code)
    },
    generateBundle(_, bundle) {
      // Vite 会在 CSS 提取阶段重新生成样式，最终产物再做一次兜底转换，防止 rpx 泄漏到 H5。
      Object.values(bundle).forEach((asset) => {
        if (asset.type === 'asset' && asset.fileName.endsWith('.css')) {
          const source = typeof asset.source === 'string' ? asset.source : new TextDecoder().decode(asset.source)
          asset.source = replaceRpx(source)
        }
      })
    }
  }
}

const uniTags = new Set(['view', 'text', 'image', 'navigator', 'checkbox', 'slider', 'scroll-view', 'radio', 'picker'])
export default defineConfig(({ command }) => ({
  define: { 'import.meta.env.VITE_SMS_COLLECTION_ENABLED': JSON.stringify(smsCollectionEnabled ? 'true' : 'false') },
  plugins: [
    vue({ template: { compilerOptions: { isCustomElement: (tag) => uniTags.has(tag) } } }),
    transformRpx(),
    smsChannelPlugin(smsCollectionEnabled, command)
  ],
  server: { host: '0.0.0.0', port: 2004 }
}))
