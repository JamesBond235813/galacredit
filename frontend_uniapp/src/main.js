import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

/**
 * 由 UniApp 运行时创建三端共用应用，不安装浏览器模拟 API。
 *
 * :return: 已注册状态管理的应用实例
 */
export function createApp() {
  const app = createSSRApp(App)
  app.use(createPinia())
  return { app }
}
