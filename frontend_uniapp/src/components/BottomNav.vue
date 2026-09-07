<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import Icon from './Icon.vue'

const current = ref('pages/login/index')
let timer = null
function sync() {
  try {
    const pages = getCurrentPages()
    current.value = pages[pages.length - 1]?.route || 'pages/home/index'
  } catch {}
}
function go(route) { uni.reLaunch({ url: `/${route}` }) }
onMounted(() => { sync(); timer = setInterval(sync, 300) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <view v-if="current !== 'pages/login/index'" class="gc-app-bottom-nav" role="navigation" aria-label="Primary navigation">
    <view class="gc-app-bottom-nav__item" :class="{ active: current === 'pages/home/index' }" @click="go('pages/home/index')"><Icon name="home" :size="22" /><text>Home</text></view>
    <view class="gc-app-bottom-nav__item" :class="{ active: current === 'pages/orders/index' }" @click="go('pages/orders/index')"><Icon name="applications" :size="22" /><text>My Applications</text></view>
    <view class="gc-app-bottom-nav__item" :class="{ active: current === 'pages/profile/index' }" @click="go('pages/profile/index')"><Icon name="account" :size="22" /><text>My Account</text></view>
  </view>
</template>

<style scoped>
.gc-app-bottom-nav { position:fixed; z-index:999; left:50%; bottom:calc(10px + env(safe-area-inset-bottom)); width:calc(100% - 28px); height:68px; transform:translateX(-50%); display:flex; padding:0 12px; border:1px solid #e3eaf4; border-radius:34px; background:rgba(255,255,255,.97); box-shadow:0 -2px 14px rgba(23,32,51,.12); }
.gc-app-bottom-nav__item { display:flex; flex:1; flex-direction:column; align-items:center; justify-content:center; gap:4px; color:#8a96a8; font-size:11px; }
.gc-app-bottom-nav__item.active { color:#c86f0c; font-weight:700; }
</style>
