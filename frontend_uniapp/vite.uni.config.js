import { defineConfig } from 'vite'
import uniModule from '@dcloudio/vite-plugin-uni'

// 官方插件以 CommonJS 发布，兼容 ESM 工程中的默认导出包装。
const uni = uniModule.default || uniModule
export default defineConfig({
  plugins: [
    {
      name: 'galacredit-uni-entry',
      transformIndexHtml: {
        order: 'pre',
        handler: (html) => html.replace('/src/main.h5.js', '/src/main.js'),
      },
    },
    uni(),
    {
      name: 'galacredit-app-single-bundle',
      enforce: 'post',
      outputOptions(options) {
        // App 服务层使用 IIFE，短信按需入口必须内联，避免生成不支持的拆分 chunk。
        if (process.env.UNI_PLATFORM === 'app' || process.env.UNI_PLATFORM === 'app-plus') {
          return { ...options, inlineDynamicImports: true, manualChunks: undefined }
        }
      },
    },
  ],
  server: { host: '0.0.0.0', port: 2004 },
})
