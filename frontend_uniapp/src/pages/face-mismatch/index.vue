<script setup>
import { computed } from 'vue'
import PageHeader from '../../components/PageHeader.vue'

const reason = computed(() => {
  if (typeof window === 'undefined') return ''
  const match = String(window.location.search || '').match(/[?&]reason=([^&]*)/)
  return String(match ? decodeURIComponent(match[1]) : '').trim()
})

/**
 * 返回人脸认证页面重新提交。
 *
 * :return: 无
 */
function retry() {
  uni.navigateTo({ url: '/pages/face/index' })
}
</script>

<template>
  <view class="gc-page mismatch-page">
    <PageHeader title="Verification Result" subtitle="Please check the photo and try again." :back="true" />
    <view class="gc-card mismatch-card">
      <view class="mismatch-icon">!</view>
      <text class="mismatch-title">Verification Unsuccessful</text>
      <text class="mismatch-copy">Your face image did not match your identity document. Please try again.</text>
      <text v-if="reason" class="mismatch-reason">Reason: {{ reason }}</text>
      <button class="gc-button" @click="retry">Try Face Verification Again</button>
    </view>
  </view>
</template>

<style scoped>
.mismatch-page { padding:calc(24px + env(safe-area-inset-top)) 16px calc(88px + env(safe-area-inset-bottom)); }
.mismatch-page :deep(.gc-page-header) { margin:0 -16px 20px; }
.mismatch-card { margin-top:0; text-align:center; padding:28px 18px 20px; }
.mismatch-icon { display:flex; align-items:center; justify-content:center; width:54px; height:54px; margin:0 auto 10px; border-radius:50%; color:#e64858; background:rgba(243,84,96,.12); font-size:28px; font-weight:700; }
.mismatch-title { display:block; font-size:22px; font-weight:800; }
.mismatch-copy { display:block; margin-top:10px; color:var(--gc-muted); font-size:14px; line-height:1.7; }
.mismatch-reason { display:block; margin-top:12px; padding:10px 12px; border:1px solid rgba(243,84,96,.16); border-radius:12px; color:var(--gc-muted); background:rgba(255,255,255,.76); font-size:12px; line-height:1.6; text-align:left; word-break:break-word; }
.mismatch-card .gc-button { margin-top:16px; height:50px; min-height:50px; border-radius:14px; font-size:16px; }
</style>
