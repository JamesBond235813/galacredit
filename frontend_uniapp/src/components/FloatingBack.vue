<script setup>
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.reLaunch({ url: '/pages/login/index' })
}
</script>

<template>
  <button class="gc-floating-back" aria-label="Back" @click="goBack">‹</button>
</template>

<style>
.gc-floating-back { position:fixed; z-index:100; top:calc(24rpx + env(safe-area-inset-top)); left:24rpx; width:88rpx; height:88rpx; padding:0; border:1rpx solid rgba(31,42,58,.12); border-radius:50%; color:#1f2a3a; background:rgba(255,255,255,.96); box-shadow:0 8rpx 24rpx rgba(31,42,58,.16); font-size:58rpx; font-family:Arial,sans-serif; line-height:78rpx; }
.gc-floating-back::after { border:0; }
</style>
