import { createApp as createVueApp, createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

function setResponsiveRootFontSize() {
  if (typeof document === 'undefined' || typeof window === 'undefined') return
  // 750 设计稿换算为 rem；宽屏最多按 480px 设计宽，避免 H5/WebView 内容过大。
  const designWidth = Math.min(window.innerWidth || 375, 480)
  document.documentElement.style.fontSize = `${designWidth / 7.5}px`
}

function installH5Uni() {
  if (typeof window === 'undefined') return
  if (!window.__gcResponsiveRootInstalled) {
    window.__gcResponsiveRootInstalled = true
    setResponsiveRootFontSize()
    window.addEventListener('resize', setResponsiveRootFontSize, { passive: true })
  }
  if (window.uni) return
  const normalizeRpxStyles = (root = document) => {
    const styles = root.nodeType === 1 && root.tagName === 'STYLE' ? [root] : root.querySelectorAll('style')
    styles.forEach((style) => {
    if (!style.textContent.includes('rpx')) return
      // 与 Vite 构建保持一致，避免 H5 开发模式在宽屏下出现过大的字号和间距。
      style.textContent = style.textContent.replace(/(-?\d+(?:\.\d+)?)rpx/g, (_, value) => `${(Number(value) / 100).toFixed(6).replace(/0+$/, '').replace(/\.$/, '')}rem`)
    })
  }
  normalizeRpxStyles()
  new MutationObserver((records) => records.forEach((record) => record.addedNodes.forEach((node) => { if (node.nodeType === 1) normalizeRpxStyles(node) }))).observe(document.head, { childList: true })
  const apiBase = import.meta.env?.VITE_API_BASE_URL || 'https://galacredit.ebamotor.com/api'
  const resolveUrl = (url) => String(url || '').startsWith('http') ? url : `${apiBase}${url || ''}`
  let routeDepth = 1
  let internalNavigation = false
  window.getCurrentPages = () => Array.from({ length: routeDepth }, () => ({ route: window.location.pathname }))
  const go = (url, replace = false) => {
    // 保留 UniApp 标准页面路径；App.vue 按标准路径加载页面，旧 H5 链接仍由别名兼容。
    const target = String(url || '/pages/login/index')
    if (replace) {
      routeDepth = 1
      window.history.replaceState({}, '', target)
    } else {
      routeDepth += 1
      window.history.pushState({}, '', target)
    }
    internalNavigation = true
    window.dispatchEvent(new PopStateEvent('popstate'))
  }
  window.addEventListener('popstate', () => {
    if (internalNavigation) {
      internalNavigation = false
      return
    }
    routeDepth = Math.max(1, routeDepth - 1)
  })
  window.uni = {
    setStorageSync: (key, value) => window.localStorage.setItem(key, JSON.stringify(value)),
    getStorageSync: (key) => { try { return JSON.parse(window.localStorage.getItem(key)) } catch { return '' } },
    removeStorageSync: (key) => window.localStorage.removeItem(key),
    getSystemInfoSync: () => ({ platform: 'h5', model: navigator.userAgent, system: navigator.platform, deviceType: 'browser', language: navigator.language, screenWidth: window.innerWidth, screenHeight: window.innerHeight }),
    request: async (options) => {
      let timeoutId
      try {
        const token = window.localStorage.getItem('token')
        const headers = { ...(options.header || {}), ...(token ? { Authorization: `Bearer ${JSON.parse(token)}` } : {}) }
        const method = String(options.method || 'GET').toUpperCase()
        const query = ['GET', 'HEAD'].includes(method) && options.data ? `?${new URLSearchParams(Object.entries(options.data).filter(([, value]) => value !== undefined && value !== null)).toString()}` : ''
        const timeout = Number(options.timeout || 20000)
        const controller = typeof AbortController !== 'undefined' ? new AbortController() : null
        timeoutId = controller ? setTimeout(() => controller.abort(), timeout) : undefined
        const response = await fetch(`${resolveUrl(options.url)}${query}`, { method, headers: { 'Content-Type': 'application/json', ...headers }, body: options.data && !['GET', 'HEAD'].includes(method) ? JSON.stringify(options.data) : undefined, signal: controller?.signal })
        const data = await response.json().catch(() => ({}))
        options.success?.({ data, statusCode: response.status })
      } catch (error) { options.fail?.(error) }
      finally { if (timeoutId) clearTimeout(timeoutId) }
    },
    chooseImage: ({ count = 1, success, fail } = {}) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.multiple = count > 1
      input.accept = 'image/*'
      input.onchange = () => input.files?.length ? success?.({ tempFilePaths: Array.from(input.files).map((file) => { const url = URL.createObjectURL(file); window.__gcSelectedFiles = { ...(window.__gcSelectedFiles || {}), [url]: file }; return url }), files: Array.from(input.files) }) : fail?.(new Error('No image selected'))
      input.click()
    },
    uploadFile: async ({ url, filePath, name = 'file', formData = {}, header = {}, timeout = 45000, success, fail } = {}) => {
      let timeoutId
      try {
        const controller = typeof AbortController !== 'undefined' ? new AbortController() : null
        timeoutId = controller ? setTimeout(() => controller.abort(), Number(timeout) || 45000) : undefined
        const response = await fetch(resolveUrl(url), { method: 'POST', headers: header, body: (() => { const form = new FormData(); const file = window.__gcSelectedFiles?.[filePath] || document.querySelector('input[type=file]')?.files?.[0]; if (file) form.append(name, file); Object.entries(formData).forEach(([key, value]) => form.append(key, value)); return form })(), signal: controller?.signal })
        success?.({ data: await response.text(), statusCode: response.status })
      } catch (error) { fail?.(error) }
      finally { if (timeoutId) clearTimeout(timeoutId) }
    },
    uploadFiles: async ({ url, files = [], formData = {}, header = {}, timeout = 45000, success, fail } = {}) => {
      let timeoutId
      try {
        const form = new FormData()
        files.forEach(({ name, uri }) => { const file = window.__gcSelectedFiles?.[uri]; if (file) form.append(name, file) })
        Object.entries(formData).forEach(([key, value]) => form.append(key, value))
        const controller = typeof AbortController !== 'undefined' ? new AbortController() : null
        timeoutId = controller ? setTimeout(() => controller.abort(), Number(timeout) || 45000) : undefined
        const response = await fetch(resolveUrl(url), { method: 'POST', headers: header, body: form, signal: controller?.signal })
        success?.({ data: await response.text(), statusCode: response.status })
      } catch (error) { fail?.(error) }
      finally { if (timeoutId) clearTimeout(timeoutId) }
    },
    showToast: ({ title } = {}) => { if (title) window.alert(title) },
    showModal: ({ title, content, success } = {}) => { success?.({ confirm: window.confirm(`${title || ''}\n${content || ''}`) }) },
    navigateTo: ({ url } = {}) => go(url),
    reLaunch: ({ url } = {}) => go(url, true),
    switchTab: ({ url } = {}) => go(url),
    navigateBack: () => window.history.back(),
    getLocation: ({ success, fail } = {}) => {
      const nativeLocation = window.webkit?.messageHandlers?.galacreditLocation
      if (nativeLocation?.postMessage) {
        const callbackName = `__gcLocation_${Date.now()}_${Math.random().toString(16).slice(2)}`
        let settled = false
        const finish = (payload) => {
          if (settled) return
          settled = true
          clearTimeout(timeout)
          delete window[callbackName]
          payload?.error ? fail?.({ code: 1, message: payload.error }) : success?.(payload)
        }
        const timeout = setTimeout(() => finish({ error: 'LOCATION_TIMEOUT' }), 12000)
        window[callbackName] = finish
        try { nativeLocation.postMessage({ callbackName }) } catch { finish({ error: 'LOCATION_BRIDGE_FAILED' }) }
        return
      }
      navigator.geolocation?.getCurrentPosition((position) => success?.({ latitude: position.coords.latitude, longitude: position.coords.longitude, accuracy: position.coords.accuracy }), (error) => fail?.(error)) || fail?.({ code: 2, message: 'GEO_UNSUPPORTED' })
    },
    makePhoneCall: ({ phoneNumber } = {}) => { window.location.href = `tel:${phoneNumber || ''}` }
  }
  document.addEventListener('click', (event) => {
    const target = event.target.closest?.('navigator[url]')
    if (target) { event.preventDefault(); go(target.getAttribute('url') || '/') }
  })
}

export function createApp() {
  installH5Uni()
  const app = createSSRApp(App)
  app.use(createPinia())
  return { app }
}

if (typeof document !== 'undefined') {
  installH5Uni()
  const app = createVueApp(App)
  app.use(createPinia())
  app.mount('#app')
}
