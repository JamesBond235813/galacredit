<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import Icon from '../../components/Icon.vue'
import { getUserInfo } from '../../api/index.js'
import { uploadImage } from '../../utils/platform.js'
import { errorMessage, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', user: null })
const scanning = ref(false)
const success = ref(false)
const selected = ref(false)
const tips = ['Face the camera', 'Use good lighting', 'Keep your face clear']
const statusText = computed(() => success.value ? 'Completed' : scanning.value ? 'Verifying' : 'Not Started')

async function load() {
  if (!requireSession()) return
  try {
    const user = await getUserInfo()
    const passed = String(user?.face_auth_status || '').toUpperCase() === 'PASSED'
    state.value = { loading: false, error: '', user }
    success.value = passed
  } catch (error) {
    state.value = { loading: false, error: errorMessage(error, 'Unable to load face verification.'), user: null }
  }
}

/**
 * 选择一张清晰的人脸照片并提交统一认证接口。
 *
 * :return: 无
 */
async function startVerification() {
  // 已完成认证时仍允许用户继续进入紧急联系人页面，避免从历史状态返回后按钮失效。
  if (success.value) {
    uni.navigateTo({ url: '/pages/application/index' })
    return
  }
  if (scanning.value) return
  scanning.value = true
  try {
    selected.value = true
    const result = await uploadImage('/user/face-auth', { source: 'uniapp' }, 'face_image')
    state.value.user = { ...state.value.user, ...result }
    success.value = true
    uni.showToast({ title: 'Face verification successful', icon: 'none' })
    setTimeout(() => uni.navigateTo({ url: '/pages/application/index' }), 500)
  } catch (error) {
    const message = errorMessage(error, 'Unable to submit face verification.')
    if (message.includes('不符') || message.toLowerCase().includes('mismatch')) {
      uni.navigateTo({ url: `/pages/face-mismatch/index?reason=${encodeURIComponent(message)}` })
    } else {
      uni.showToast({ title: message, icon: 'none' })
    }
  } finally {
    scanning.value = false
  }
}

onMounted(load)
usePageResume(() => { if (!scanning.value) return load() })
</script>

<template>
  <view class="gc-page face-page">
    <PageHeader title="Face Verification" :back="true" />
    <view class="face-hero"><text class="hero-chip">Step 2 of 4</text><text class="hero-title">Complete Face Verification</text><text class="hero-desc">We use a live face check to confirm that you are completing this application.</text></view>
    <view class="tip-row"><text v-for="tip in tips" :key="tip" class="tip-pill">{{ tip }}</text></view>
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="gc-card scan-card">
        <view class="gc-row"><view><text class="card-title">Live Face Check</text><text class="card-desc">Keep your face centred in the frame</text></view><text class="capture-status" :class="{ done: success }">{{ statusText }}</text></view>
        <view class="scan-panel"><view class="scan-grid"><text></text><text></text><text></text><text></text></view><view class="scan-ring" :class="{ scanning, success }"><Icon name="user-circle" :size="74" /><text v-if="scanning" class="scan-line"></text></view></view>
        <view class="status-block"><text class="status-title">{{ success ? 'Verification successful' : scanning ? 'Verification in progress...' : 'Face the camera and keep still' }}</text><text class="status-desc">{{ success ? 'Next, provide two emergency contacts.' : 'Avoid backlighting, face coverings and sudden movement.' }}</text><text v-if="selected && !success" class="selected-tip">Photo selected. Complete the verification step.</text></view>
        <button class="gc-button" :loading="scanning" :disabled="scanning" @click="startVerification">{{ success ? 'Continue Application' : 'Start Verification' }}</button>
      </view>
      <view class="safe-note"><Icon name="shield-check" :size="13" />Your image is used only for identity and risk verification</view>
    </AsyncState>
  </view>
</template>

<style scoped>
.face-page { padding:calc(40px + env(safe-area-inset-top)) 16px calc(88px + env(safe-area-inset-bottom)); }
.face-page :deep(.gc-page-header) { margin:0 -16px 8px; }
.face-hero { display:flex; flex-direction:column; align-items:flex-start; width:100%; margin:14px 0 0; padding:0; }
.hero-chip { display:inline-flex; align-items:center; min-height:28px; padding:0 12px; border-radius:999px; color:var(--gc-brand-deep); background:rgba(234,149,24,.1); font-size:12px; font-weight:700; }
.hero-title { display:block; margin-top:12px; font-size:24px; line-height:1.28; font-weight:800; }
.hero-desc { display:block; margin-top:8px; color:var(--gc-muted); font-size:13px; line-height:1.65; }
.tip-row { display:flex; flex-wrap:wrap; gap:8px; width:100%; margin-top:12px; }
.tip-row .tip-pill { display:inline-flex; align-items:center; justify-content:center; min-height:34px; padding:0 12px; border-radius:999px; color:var(--gc-brand-deep); background:rgba(255,255,255,.68); border:1px solid rgba(234,149,24,.08); font-size:12px; font-weight:600; }
.scan-card { width:100%; margin-top:12px; padding:16px; }
.card-title,.status-title { display:block; font-size:17px; font-weight:700; }
.card-desc,.status-desc,.selected-tip { display:block; margin-top:4px; color:var(--gc-muted); font-size:12px; line-height:1.5; }
.capture-status { display:inline-flex; align-items:center; justify-content:center; min-height:28px; padding:0 12px; border-radius:999px; color:var(--gc-muted); background:rgba(154,168,188,.12); font-size:12px; font-weight:700; }
.capture-status.done { color:#0daa79; background:rgba(48,215,169,.14); }
.scan-panel { position:relative; margin:11px 0 12px; padding:16px 0; border-radius:18px; background:radial-gradient(circle at center,rgba(234,149,24,.08) 0%,rgba(234,149,24,.02) 52%,transparent 52%),linear-gradient(180deg,#fbfdff 0%,#f5f9ff 100%); overflow:hidden; }
.scan-grid text { position:absolute; width:16px; height:16px; border:2px solid rgba(234,149,24,.36); }
.scan-grid text:nth-child(1) { top:16px; left:16px; border-right:0; border-bottom:0; }
.scan-grid text:nth-child(2) { top:16px; right:16px; border-left:0; border-bottom:0; }
.scan-grid text:nth-child(3) { bottom:16px; left:16px; border-right:0; border-top:0; }
.scan-grid text:nth-child(4) { right:16px; bottom:16px; border-left:0; border-top:0; }
.scan-ring { position:relative; display:flex; align-items:center; justify-content:center; width:188px; height:188px; margin:0 auto; border:2px solid rgba(234,149,24,.2); border-radius:50%; color:var(--gc-brand-deep); background:rgba(255,255,255,.92); box-shadow:inset 0 0 0 14px rgba(234,149,24,.05); overflow:hidden; }
.scan-ring.scanning { border-color:rgba(234,149,24,.7); }
.scan-ring.success { border-color:rgba(29,138,91,.7); }
.scan-ring .gc-icon { color:var(--gc-brand-deep); }
.scan-ring.success .gc-icon { color:var(--gc-success); }
.scan-line { position:absolute; left:28px; right:28px; height:5px; border-radius:99px; background:var(--gc-brand); box-shadow:0 0 18px rgba(234,149,24,.5); animation:scan 1.8s linear infinite; }
@keyframes scan { from { top:30rpx; } to { top:246rpx; } }
.status-block { text-align:center; }
.status-title { font-size:18px; }
.status-desc { margin-top:8px; font-size:13px; line-height:1.6; }
.selected-tip { color:var(--gc-brand-deep); }
.gc-button { margin-top:16px; height:50px; min-height:50px; border-radius:14px; font-size:16px; }
.safe-note { display:flex; align-items:center; justify-content:center; gap:6px; width:100%; height:15px; margin-top:12px; color:#9aa4b3; font-size:12px; line-height:15px; }
</style>
