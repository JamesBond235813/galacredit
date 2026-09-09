
<script>
import { onMounted } from 'vue'
import BottomNav from './components/BottomNav.vue'
import { checkForAppUpdate } from './utils/app-update.js'

export default {
  components: { BottomNav },
  setup() {
    const lockNativeViewport = () => {
      try {
        const webview = plus.webview.currentWebview()
        webview?.setStyle?.({ scalable: false, bounce: 'none' })
      } catch {}
    }
    onMounted(() => {
      lockNativeViewport()
      const run = () => checkForAppUpdate().catch(() => {})
      if (typeof plus !== 'undefined') run()
      else if (typeof document !== 'undefined') document.addEventListener('plusready', run, { once: true })
      if (typeof document !== 'undefined') document.addEventListener('plusready', lockNativeViewport, { once: true })
    })
  }
}
</script>

<template>
  <BottomNav />
</template>

<style>
@import './styles/theme.css';
</style>
