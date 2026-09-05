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
  <view class="gc-page-header">
    <button v-if="back" class="gc-page-header__back" aria-label="Back" @click="goBack"><Icon name="chevron-left" :size="24" label="Back" /></button>
    <view class="gc-page-header__copy">
      <text class="gc-page-header__title">{{ title }}</text>
      <text v-if="subtitle" class="gc-page-header__subtitle">{{ subtitle }}</text>
    </view>
  </view>
</template>

<style scoped>
.gc-page-header { display:flex; align-items:center; gap:16rpx; margin-bottom:28rpx; }
.gc-page-header__back { width:66rpx; height:66rpx; padding:0; border:1rpx solid var(--gc-border); border-radius:20rpx; color:var(--gc-ink); background:#fff; font-size:48rpx; line-height:58rpx; }
.gc-page-header__back::after { border:0; }
.gc-page-header__copy { flex:1; }
.gc-page-header__title { display:block; font-size:42rpx; font-weight:800; }
.gc-page-header__subtitle { display:block; margin-top:6rpx; color:var(--gc-muted); font-size:23rpx; }
</style>
