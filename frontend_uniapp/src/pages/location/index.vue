<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import { getUserInfo, submitLocation } from '../../api/index.js'
import { getCurrentLocation } from '../../utils/platform.js'
import { errorMessage, formatDate, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', user: null })
const busy = ref(false)

async function load() {
  if (!requireSession()) return
  try { state.value = { loading: false, error: '', user: await getUserInfo() } }
  catch (error) { state.value = { loading: false, error: errorMessage(error), user: null } }
}

/**
 * 获取用户主动授权的当前位置并提交一次性风险校验。
 *
 * :return: 无
 */
async function locate() {
  if (busy.value) return
  busy.value = true
  try {
    const position = await getCurrentLocation()
    await submitLocation({ latitude: position.latitude, longitude: position.longitude, accuracy: position.accuracy, source: 'uniapp-user-action' })
    state.value.user = { ...state.value.user, location_updated_at: new Date().toISOString() }
    uni.showToast({ title: 'Location submitted', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: errorMessage(error, 'Location permission was not granted.'), icon: 'none' })
  } finally {
    busy.value = false
  }
}

onMounted(load)
usePageResume(() => { if (!busy.value) return load() })
</script>

<template>
  <view class="gc-page">
    <PageHeader title="Location check" subtitle="Share your current location once when it helps verify your application." :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="gc-card">
        <text class="gc-section-title">Your choice</text>
        <text class="copy">We do not track your location continuously. Your location is requested only after you tap the button and grant the system permission.</text>
        <view class="gc-list-row"><text class="gc-list-row__label">Last update</text><text class="gc-list-row__value">{{ state.user?.location_updated_at ? formatDate(state.user.location_updated_at) : 'Not shared yet' }}</text></view>
        <button class="gc-button" :loading="busy" :disabled="busy" @click="locate">{{ busy ? 'Checking…' : 'Share current location' }}</button>
      </view>
      <view class="gc-safe-note">Location is used for application security and regional service checks. You can decline and contact support if you need help.</view>
    </AsyncState>
  </view>
</template>

<style scoped>
.copy { display:block; color:var(--gc-muted); font-size:24rpx; line-height:1.55; }
</style>
