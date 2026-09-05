<script setup>
import { computed, markRaw, onBeforeUnmount, onMounted, ref } from 'vue'
import './styles/theme.css'
import { getStorage } from './utils/platform.js'
import Icon from './components/Icon.vue'

const path = ref(typeof window !== 'undefined' ? window.location.pathname : '/pages/login/index')
const routes = {
  '/': () => import('./pages/login/index.vue'),
  '/login': () => import('./pages/login/index.vue'),
  '/pages/login/index': () => import('./pages/login/index.vue'),
  // 兼容原生壳和历史 H5 深链接，避免升级业务页面后旧入口落到登录页。
  '/home': () => import('./pages/home/index.vue'),
  '/orders': () => import('./pages/orders/index.vue'),
  '/profile': () => import('./pages/profile/index.vue'),
  '/application-form': () => import('./pages/application/index.vue'),
  '/ocr': () => import('./pages/verification/index.vue'),
  '/review': () => import('./pages/application/index.vue'),
  '/withdraw': () => import('./pages/withdraw/index.vue'),
  '/bill': () => import('./pages/bill/index.vue'),
  '/location': () => import('./pages/location/index.vue'),
  '/risk': () => import('./pages/risk/index.vue'),
  '/channel': () => import('./pages/channel/index.vue'),
  '/change-password': () => import('./pages/password/index.vue'),
  '/agreement': () => import('./pages/agreement/index.vue'),
  '/support': () => import('./pages/support/index.vue'),
  '/pages/home/index': () => import('./pages/home/index.vue'),
  '/pages/orders/index': () => import('./pages/orders/index.vue'),
  '/pages/profile/index': () => import('./pages/profile/index.vue'),
  '/pages/application/index': () => import('./pages/application/index.vue'),
  '/pages/verification/index': () => import('./pages/verification/index.vue'),
  '/pages/withdraw/index': () => import('./pages/withdraw/index.vue'),
  '/pages/bill/index': () => import('./pages/bill/index.vue'),
  '/pages/location/index': () => import('./pages/location/index.vue'),
  '/pages/risk/index': () => import('./pages/risk/index.vue'),
  '/pages/channel/index': () => import('./pages/channel/index.vue'),
  '/pages/password/index': () => import('./pages/password/index.vue'),
  '/pages/agreement/index': () => import('./pages/agreement/index.vue'),
  '/pages/support/index': () => import('./pages/support/index.vue')
}
const currentPage = ref(null)
const currentLoader = computed(() => routes[path.value] || routes['/pages/login/index'])
const isH5Shell = computed(() => {
  try { return typeof window !== 'undefined' && window.uni?.getSystemInfoSync?.().platform === 'h5' } catch { return true }
})
const showBottomNav = computed(() => isH5Shell.value && Boolean(getStorage('token')) && !['/', '/login', '/pages/login/index'].includes(path.value))
let loadSequence = 0

async function loadPage() {
  const sequence = ++loadSequence
  const page = markRaw((await currentLoader.value()).default)
  // 快速连续切换页面时，旧异步 chunk 不能覆盖最后一次路由。
  if (sequence === loadSequence) currentPage.value = page
}
function syncPath() { path.value = window.location.pathname; loadPage() }
onMounted(() => { window.addEventListener('popstate', syncPath); loadPage() })
onBeforeUnmount(() => window.removeEventListener('popstate', syncPath))
</script>

<template>
  <component :is="currentPage" v-if="currentPage" />
  <view v-if="showBottomNav" class="gc-h5-bottom-nav" role="navigation" aria-label="Primary navigation">
    <navigator url="/pages/home/index" class="gc-h5-bottom-nav__item" :class="{ 'gc-h5-bottom-nav__item--active': path === '/pages/home/index' || path === '/home' }">
      <Icon class="gc-h5-bottom-nav__icon" name="home" :size="23" /><text>Home</text>
    </navigator>
    <navigator url="/pages/orders/index" class="gc-h5-bottom-nav__item" :class="{ 'gc-h5-bottom-nav__item--active': path === '/pages/orders/index' || path === '/orders' }">
      <Icon class="gc-h5-bottom-nav__icon" name="applications" :size="23" /><text>Applications</text>
    </navigator>
    <navigator url="/pages/profile/index" class="gc-h5-bottom-nav__item" :class="{ 'gc-h5-bottom-nav__item--active': path === '/pages/profile/index' || path === '/profile' }">
      <Icon class="gc-h5-bottom-nav__icon" name="account" :size="23" /><text>Account</text>
    </navigator>
  </view>
</template>

<style>
.gc-h5-bottom-nav { position:fixed; z-index:50; right:50%; bottom:0; width:100%; max-width:480px; transform:translateX(50%); display:flex; justify-content:space-around; padding:14rpx 24rpx calc(14rpx + env(safe-area-inset-bottom)); border-top:1rpx solid var(--gc-border); background:rgba(255,255,255,.96); box-shadow:0 -8rpx 24rpx rgba(23,32,51,.08); backdrop-filter:blur(12px); }
.gc-h5-bottom-nav__item { display:flex; flex:1; flex-direction:column; align-items:center; gap:4rpx; color:var(--gc-muted); font-size:20rpx; text-decoration:none; }
.gc-h5-bottom-nav__item--active { color:var(--gc-brand-deep); font-weight:750; }
.gc-h5-bottom-nav__icon { font-size:34rpx; line-height:1; }
</style>
