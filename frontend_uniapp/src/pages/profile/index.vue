<script setup>
import { computed, onMounted, ref } from 'vue'
import AsyncState from '../../components/AsyncState.vue'
import Icon from '../../components/Icon.vue'
import { getLoanStatus, getUserInfo } from '../../api/index.js'
import { errorMessage, formatDate, requireSession, signOut, verificationStatusLabel } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'
import { checkForAppUpdate } from '../../utils/app-update.js'
import { applicationNextPage } from '../../utils/application-flow.js'

const state = ref({ loading: true, error: '', loanError: '', user: null, loan: null })
const maskedPhone = computed(() => {
  const value = String(state.value.user?.phone || '')
  return /^\d{11}$/.test(value) ? value.replace(/(\d{3})\d{6}(\d{2})/, '$1******$2') : value
})

async function load() {
  if (!requireSession()) return
  const [userResult, loanResult] = await Promise.allSettled([getUserInfo(), getLoanStatus()])
  if (userResult.status === 'rejected') {
    state.value = { loading: false, error: errorMessage(userResult.reason), loanError: '', user: null, loan: null }
    return
  }
  state.value = {
    loading: false,
    error: '',
    loanError: loanResult.status === 'rejected' ? 'Application status is temporarily unavailable. You can retry shortly.' : '',
    user: userResult.value,
    loan: loanResult.status === 'fulfilled' ? loanResult.value : null
  }
}
function openApplicationFlow() {
  uni.navigateTo({ url: applicationNextPage(state.value.loan?.status) })
}
function confirmSignOut() {
  uni.showModal({ title: 'Sign out?', content: 'You can sign in again with your phone.', success: ({ confirm }) => { if (confirm) signOut() } })
}
onMounted(() => { load(); checkForAppUpdate({ silent: false }).catch(() => {}) })
usePageResume(load)
</script>

<template>
  <view class="gc-page profile-page">
    <view class="profile-header"><view><text class="greeting">Hello, {{ maskedPhone || 'there' }}</text><view class="protection"><Icon name="shield-check" :size="16" /><text>Your information is encrypted and protected</text></view></view><view class="avatar"><Icon name="account" :size="34" /></view></view>
    <AsyncState :loading="state.loading" :error="state.error" :empty="!state.user" empty-text="No account details yet." @retry="load">
      <view class="notice-panel"><view class="notice-banner"><Icon name="volume" :size="16" /><text class="notice-copy">Notice: Never send repayment funds to a private account.</text><text class="notice-brand">GalaCredit</text></view><view v-if="state.loanError" class="status-note">{{ state.loanError }}</view><view class="gc-card services-card"><text class="gc-section-title">My Services</text><view class="services-grid"><view class="service-item" @click="openApplicationFlow"><view class="service-icon"><Icon name="balance" :size="23" /></view><text>Apply</text></view><view class="service-item" @click="openApplicationFlow"><view class="service-icon"><Icon name="records" :size="23" /></view><text>Under Review</text></view><view class="service-item" @click="openApplicationFlow"><view class="service-icon"><Icon name="idcard" :size="23" /></view><text>Repayment</text></view></view></view></view>
      <view class="gc-card menu-card"><text class="gc-section-title">More Services</text><navigator url="/pages/support/index" class="menu"><Icon name="support" :size="21" /><text>Customer Support</text><Icon name="chevron-right" :size="20" /></navigator><navigator url="/pages/password/index" class="menu"><Icon name="shield-check" :size="21" /><text>Change Password</text><Icon name="chevron-right" :size="20" /></navigator><navigator url="/pages/profile/index" class="menu" @click="uni.showToast({ title: 'Your information has been refreshed', icon: 'none' })"><Icon name="refresh" :size="21" /><text>Refresh Status</text><Icon name="chevron-right" :size="20" /></navigator><navigator url="/pages/about/index" class="menu"><Icon name="info" :size="21" /><text>About Us</text><Icon name="chevron-right" :size="20" /></navigator><navigator url="/pages/agreement/index" class="menu"><Icon name="document" :size="21" /><text>User Agreement</text><Icon name="chevron-right" :size="20" /></navigator><view class="menu" @click="uni.showToast({ title: 'The feedback channel is being prepared', icon: 'none' })"><Icon name="message" :size="21" /><text>Feedback</text><Icon name="chevron-right" :size="20" /></view></view>
    </AsyncState>
  </view>
</template>

<style scoped>
.profile-page { padding:calc(24px + env(safe-area-inset-top)) 10px calc(120px + env(safe-area-inset-bottom)); }
.profile-header { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:0 10px; }
.greeting { display:block; font-size:24px; line-height:1.2; font-weight:700; }
.protection { display:flex; align-items:center; gap:6px; width:max-content; max-width:304px; margin-top:14px; padding:8px 14px; border-radius:999px; color:#b37712; background:linear-gradient(180deg,#fff7dc 0%,#fff1cb 100%); font-size:13px; line-height:1.2; }
.protection text { flex:1; min-width:0; }
.avatar { display:flex; align-items:center; justify-content:center; width:70px; height:70px; padding:4px; border-radius:50%; color:var(--gc-brand-deep); background:linear-gradient(180deg,#eef3ff 0%,#f8fbff 100%); box-shadow:0 12px 26px rgba(23,32,51,.08); font-size:38rpx; font-weight:800; }
.name,.phone { display:block; }
.name { font-size:30rpx; font-weight:800; }
.phone { margin-top:8rpx; color:var(--gc-muted); font-size:24rpx; }
.menu { display:flex; align-items:center; gap:14px; min-height:60px; padding:0; border-bottom:1rpx solid #eef3fb; color:var(--gc-ink); font-size:15px; }
.menu:last-child { border-bottom:0; }
.menu text { flex:1; }
.menu .gc-icon { color:var(--gc-muted); }
.menu .gc-vant-icon { color:var(--gc-muted); }
.notice-panel { margin-top:28px; }
.status-note { margin:10px 0; padding:10px 12px; border-radius:10px; color:var(--gc-muted); background:#fff8ed; font-size:12px; line-height:1.45; }
.notice-banner { display:flex; align-items:center; justify-content:space-between; gap:12px; min-height:78px; padding:14px 16px 40px; border-radius:18px; color:rgba(255,255,255,.92); background:var(--gc-brand-deep); box-shadow:0 18px 36px rgba(201,111,12,.18); font-size:13px; }
.notice-copy { flex:1; min-width:0; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
.notice-icon { flex:none; }
.notice-brand { flex:none; color:rgba(255,255,255,.68); }
.services-card { position:relative; z-index:1; margin-top:-24px; padding:22px 18px 20px; border-radius:18px; }
.menu-card { margin-top:18px; padding:22px 18px 12px; border-radius:18px; }
.services-card .gc-section-title,.menu-card .gc-section-title { margin:0; font-size:17px; line-height:20px; }
.menu-card .gc-section-title + .menu { margin-top:12px; }
.services-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:22px; }
.service-item { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; min-height:92px; border-radius:16px; color:var(--gc-brand-deep); background:transparent; text-decoration:none; font-size:14px; font-weight:600; }
.service-item > text { color:var(--gc-ink); }
.service-icon { display:flex; align-items:center; justify-content:center; width:42px; height:42px; border-radius:14px; color:var(--gc-brand-deep); background:rgba(234,149,24,.08); }
.service-item:active { background:rgba(234,149,24,.08); }
</style>
