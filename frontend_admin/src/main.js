import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { installEnglishFallback } from './i18n/adminLocale'

window.addEventListener('vite:preloadError', event => {
  event.preventDefault()

  const reloadKey = 'xhb_admin_preload_reload_at'
  const lastReloadAt = Number(sessionStorage.getItem(reloadKey) || 0)
  const now = Date.now()

  // 发布后浏览器可能缓存旧入口，缺少旧 hash 资源时刷新一次拉取新版本。
  if (now - lastReloadAt > 10000) {
    sessionStorage.setItem(reloadKey, String(now))
    window.location.reload()
  }
})

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
installEnglishFallback()
