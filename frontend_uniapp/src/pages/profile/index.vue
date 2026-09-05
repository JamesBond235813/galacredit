<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import Icon from '../../components/Icon.vue'
import { getUserInfo } from '../../api/index.js'
import { errorMessage, formatDate, requireSession, signOut, verificationStatusLabel } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', user: null })

async function load() {
  if (!requireSession()) return
  try { state.value = { loading: false, error: '', user: await getUserInfo() } }
  catch (error) { state.value = { loading: false, error: errorMessage(error), user: null } }
}
function confirmSignOut() {
  uni.showModal({ title: 'Sign out?', content: 'You can sign in again with your phone.', success: ({ confirm }) => { if (confirm) signOut() } })
}
onMounted(load)
usePageResume(load)
</script>

<template>
  <view class="gc-page">
    <PageHeader title="My account" subtitle="Your details and security controls." :back="false" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="!state.user" empty-text="No account details yet." @retry="load">
      <view class="gc-card account-hero"><view class="avatar">{{ state.user.name?.slice(0, 1) || 'G' }}</view><view><text class="name">{{ state.user.name || 'GalaCredit customer' }}</text><text class="phone">{{ state.user.phone }}</text></view></view>
      <view class="gc-card"><text class="gc-section-title">Verification</text><view class="gc-list-row"><text class="gc-list-row__label">Identity</text><text class="gc-list-row__value">{{ verificationStatusLabel(state.user.real_name_status) }}</text></view><view class="gc-list-row"><text class="gc-list-row__label">Face check</text><text class="gc-list-row__value">{{ verificationStatusLabel(state.user.face_auth_status) }}</text></view><view class="gc-list-row"><text class="gc-list-row__label">Member since</text><text class="gc-list-row__value">{{ formatDate(state.user.created_at) }}</text></view></view>
      <view class="gc-card"><navigator url="/pages/verification/index" class="menu">Identity verification <Icon name="chevron-right" :size="20" /></navigator><navigator url="/pages/location/index" class="menu">Location check <Icon name="chevron-right" :size="20" /></navigator><navigator url="/pages/risk/index" class="menu">Security review <Icon name="chevron-right" :size="20" /></navigator><navigator url="/pages/password/index" class="menu">Change password <Icon name="chevron-right" :size="20" /></navigator><navigator url="/pages/agreement/index" class="menu">Agreements and privacy <Icon name="chevron-right" :size="20" /></navigator></view>
      <button class="gc-button gc-button--ghost" @click="confirmSignOut">Sign out</button>
    </AsyncState>
  </view>
</template>

<style scoped>
.account-hero { display:flex; align-items:center; gap:20rpx; }
.avatar { display:flex; align-items:center; justify-content:center; width:88rpx; height:88rpx; border-radius:30rpx; color:#fff; background:linear-gradient(135deg,#f2a53d,#d9790d); font-size:38rpx; font-weight:800; }
.name,.phone { display:block; }
.name { font-size:30rpx; font-weight:800; }
.phone { margin-top:8rpx; color:var(--gc-muted); font-size:24rpx; }
.menu { display:flex; justify-content:space-between; padding:26rpx 0; border-bottom:1rpx solid var(--gc-border); font-size:26rpx; }
.menu:last-child { border-bottom:0; }
.menu .gc-icon { color:var(--gc-muted); }
</style>
