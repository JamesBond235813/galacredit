<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import { getUserInfo, submitFaceAuth, submitOCR } from '../../api/index.js'
import { uploadImage } from '../../utils/platform.js'
import { errorMessage, requireSession, verificationStatusLabel } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', user: null })
const busy = ref(false)
const activeType = ref('')

async function load() {
  if (!requireSession()) return
  try { state.value = { loading: false, error: '', user: await getUserInfo() } }
  catch (error) { state.value = { loading: false, error: errorMessage(error), user: null } }
}

/**
 * 选择并上传 Ghana Card 图片，后端负责 OCR 处理。
 *
 * :param side: front 或 back
 * :return: 无
 */
async function uploadDocuments() {
  if (busy.value) return
  busy.value = true
  activeType.value = 'documents'
  try {
    const result = await submitOCR({ source: 'uniapp' })
    state.value.user = { ...state.value.user, ...result }
    uni.showToast({ title: 'Document uploaded', icon: 'none' })
  } catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to upload your document.'), icon: 'none' }) }
  finally { busy.value = false; activeType.value = '' }
}

/**
 * 选择人脸照片并提交认证。
 *
 * :return: 无
 */
async function uploadFace() {
  if (busy.value) return
  busy.value = true
  activeType.value = 'face'
  try {
    const result = await uploadImage('/user/face-auth', { source: 'uniapp' })
    state.value.user = { ...state.value.user, ...result }
    uni.showToast({ title: 'Face verification submitted', icon: 'none' })
  } catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to submit face verification.'), icon: 'none' }) }
  finally { busy.value = false; activeType.value = '' }
}

onMounted(load)
usePageResume(() => { if (!busy.value) return load() })
</script>

<template>
  <view class="gc-page">
    <PageHeader title="Verify your identity" subtitle="Use clear, current photos of your Ghana Card." :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="gc-card">
        <text class="gc-section-title">Ghana Card</text>
        <text class="copy">Upload both sides. Make sure every word is visible and the card is not cropped.</text>
        <view class="verify-row"><view><text class="label">Front</text><text class="value">{{ state.user?.id_card_front_image_url ? 'Uploaded' : 'Not uploaded' }}</text></view><text class="hint">Included below</text></view>
        <view class="verify-row"><view><text class="label">Back</text><text class="value">{{ state.user?.id_card_back_image_url ? 'Uploaded' : 'Not uploaded' }}</text></view><text class="hint">Included below</text></view>
        <button class="gc-button gc-button--secondary" :disabled="busy" @click="uploadDocuments">{{ activeType === 'documents' ? 'Uploading…' : 'Choose both sides' }}</button>
      </view>
      <view class="gc-card">
        <text class="gc-section-title">Face check</text>
        <text class="copy">Take one well-lit photo with your face centered and uncovered.</text>
        <view class="gc-list-row"><text class="gc-list-row__label">Status</text><text class="gc-list-row__value">{{ verificationStatusLabel(state.user?.face_auth_status) }}</text></view>
        <button class="gc-button" :loading="busy" :disabled="busy" @click="uploadFace">{{ activeType === 'face' ? 'Submitting…' : 'Start face check' }}</button>
      </view>
      <view class="gc-safe-note">Photos are used for identity verification and protected according to the GalaCredit privacy policy.</view>
    </AsyncState>
  </view>
</template>

<style scoped>
.copy { display:block; color:var(--gc-muted); font-size:24rpx; line-height:1.55; }
.verify-row { display:flex; align-items:center; justify-content:space-between; gap:18rpx; padding:24rpx 0; border-bottom:1rpx solid var(--gc-border); }
.verify-row:last-child { border-bottom:0; }
.label,.value { display:block; }
.label { color:var(--gc-muted); font-size:23rpx; }
.value { margin-top:6rpx; font-size:27rpx; font-weight:700; }
.verify-row .gc-button { width:210rpx; min-height:76rpx; margin-top:0; font-size:23rpx; }
</style>
