<script setup>
import BrandLockup from '../../components/BrandLockup.vue'
import PageHeader from '../../components/PageHeader.vue'
import { signOut } from '../../utils/app.js'

function confirmSignOut() {
  uni.showModal({ title: 'Sign out?', content: 'You can sign in again with your phone.', success: ({ confirm }) => { if (confirm) signOut() } })
}
</script>

<template>
  <view class="gc-page about-page">
    <PageHeader title="About Us" :back="true" />
    <view class="about-card brand-card gc-card"><BrandLockup /><text class="copy">GalaCredit provides eligible customers with cash loan applications, MoMo disbursement and repayment bill services.</text></view>
    <view class="about-card gc-card info-card"><view class="info-row"><text>Service</text><text>Credit applications and repayment information</text></view><view class="info-row"><text>Support Hours</text><text>Weekdays, 09:00 - 18:00</text></view><view class="info-row"><text>Security Notice</text><text>Never transfer funds to a private account</text></view></view>
    <button class="gc-button" @click="confirmSignOut">Sign Out</button>
  </view>
</template>

<style scoped>
.about-page { padding-top:calc(24px + env(safe-area-inset-top)); padding-left:16px; padding-right:16px; }
.about-page :deep(.gc-page-header) { margin:0 -16px 19px; }
.about-card { text-align:center; }
.brand-card { padding:28px 20px 24px; }
.about-card :deep(.gc-brand) { justify-content:center; }
.about-card :deep(.gc-brand__logo) { width:76px; height:76px; border-radius:0; background-color:transparent; background-size:100%; box-shadow:none; }
.about-card :deep(.gc-brand__name) { font-size:24px; line-height:1.2; }
.about-card :deep(.gc-brand__tagline) { display:none; }
.copy { display:block; margin-top:14px; color:var(--gc-muted); font-size:14px; line-height:1.7; }
.info-card { text-align:left; padding:18rpx 30rpx; }
.info-row { display:flex; align-items:center; justify-content:space-between; gap:18rpx; min-height:92rpx; border-bottom:1rpx solid var(--gc-border); }
.info-row:last-child { border-bottom:0; }
.info-row text:first-child { color:var(--gc-muted); font-size:23rpx; }
.info-row text:last-child { max-width:62%; text-align:right; font-size:23rpx; font-weight:600; line-height:1.45; }
.about-page > .gc-button { margin-top:28px; }
</style>
