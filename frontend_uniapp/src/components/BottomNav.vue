<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import Icon from './Icon.vue'

const current = ref('pages/login/index')
let timer = null
function sync() {
  try {
    const pages = getCurrentPages()
    current.value = String(pages[pages.length - 1]?.route || 'pages/home/index').replace(/^\/+/, '')
  } catch {}
}
function go(route) { uni.reLaunch({ url: `/${route}` }) }
const isLogin = () => ['pages/login/index', 'login', ''].includes(current.value)
onMounted(() => { sync(); timer = setInterval(sync, 300) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <view v-if="!isLogin()" class="gc-app-bottom-nav" role="navigation" aria-label="Primary navigation">
    <view class="gc-app-bottom-nav__item" :class="{ active: current === 'pages/home/index' || current === 'home' }" @click="go('pages/home/index')"><Icon name="home" :size="22" :use-vant="false" /><text>GalaCredit</text></view>
    <view class="gc-app-bottom-nav__item" :class="{ active: current === 'pages/profile/index' || current === 'profile' }" @click="go('pages/profile/index')"><Icon name="account" :size="22" :use-vant="false" /><text>My Account</text></view>
  </view>
</template>

<style scoped>
.gc-app-bottom-nav { position:fixed !important; z-index:9999; left:50%; bottom:10px; bottom:calc(10px + constant(safe-area-inset-bottom)); bottom:calc(10px + env(safe-area-inset-bottom)); width:calc(100% - 28px); max-width:402px; height:68px; transform:translate3d(-50%, 0, 0); display:flex !important; padding:0 24px; border:1px solid #e3eaf4; border-radius:34px; background:rgba(255,255,255,.97); box-shadow:0 -2px 14px rgba(23,32,51,.12); -webkit-backdrop-filter:blur(12px); backdrop-filter:blur(12px); }
.gc-app-bottom-nav__item { display:flex; flex:1; flex-direction:column; align-items:center; justify-content:center; gap:4px; min-width:0; color:#8a96a8; font-size:13px; line-height:1.15; text-align:center; }
.gc-app-bottom-nav__item .gc-icon { display:block; width:22px; height:22px; margin-bottom:3px; }
.gc-app-bottom-nav__item.active { color:#c86f0c; font-weight:700; }
</style>
