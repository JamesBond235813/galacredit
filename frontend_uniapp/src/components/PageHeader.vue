<script setup>
import Icon from './Icon.vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  back: { type: Boolean, default: false }
})

/**
 * 返回上一页或首页。
 *
 * :return: 无
 */
function goBack() {
  if (getCurrentPages().length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}
</script>

<template>
  <view class="gc-page-header" :class="{ 'gc-page-header--back': back }">
    <button v-if="back" class="gc-page-header__back" aria-label="Back" @click="goBack"><Icon name="chevron-left" :size="24" label="Back" /></button>
    <view class="gc-page-header__copy">
      <text class="gc-page-header__title">{{ title }}</text>
      <text v-if="subtitle" class="gc-page-header__subtitle">{{ subtitle }}</text>
    </view>
  </view>
</template>

<style scoped>
.gc-page-header { display:flex; align-items:center; gap:8px; min-height:54px; margin:0 -16px 8px; padding:0 8px; background:transparent; }
.gc-page-header__back { width:36px; height:36px; padding:0; border:0; border-radius:50%; color:var(--gc-ink); background:rgba(255,255,255,.96); box-shadow:0 4px 12px rgba(31,42,58,.12); font-size:24px; line-height:36px; }
.gc-page-header__back::after { border:0; }
.gc-page-header__copy { flex:1; }
.gc-page-header__title { display:block; padding-right:0; font-size:18px; line-height:24px; font-weight:700; text-align:center; }
.gc-page-header--back .gc-page-header__title { padding-right:0; }
.gc-page-header__subtitle { display:none; }
</style>
