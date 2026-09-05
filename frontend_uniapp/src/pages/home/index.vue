<script setup>
import { computed, onMounted, ref } from 'vue'
import BrandLockup from '../../components/BrandLockup.vue'
import AsyncState from '../../components/AsyncState.vue'
import Icon from '../../components/Icon.vue'
import { loadHomeData } from '../../api/index.js'
import { errorMessage, formatMoney, loanStatusLabel, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', profile: null, loan: null, products: [] })
const status = computed(() => state.value.loan?.status || 'INIT')
const available = computed(() => state.value.loan?.available_credit_limit ?? state.value.loan?.credit_limit ?? 0)
const actionText = computed(() => ({ INIT: 'Start my application', REVIEWING: 'View review status', REJECTED: 'Update my application', APPROVED: 'Choose a loan option', WITHDRAWING: 'View disbursement', DISBURSED: 'View repayment plan', OVERDUE: 'Resolve overdue bill', SETTLED: 'Apply again' }[status.value] || 'View account'))
const statusLabel = computed(() => ({ INIT: 'Ready when you are', REVIEWING: 'Application under review', APPROVED: 'Credit approved', WITHDRAWING: 'Preparing disbursement', DISBURSED: 'Repayment in progress', OVERDUE: 'Action required', SETTLED: 'Previous loan settled', REJECTED: 'Application needs an update' }[status.value] || 'Account update'))

async function load() {
  if (!requireSession()) return
  state.value.loading = true
  try { const data = await loadHomeData(); state.value = { loading: false, error: '', ...data, loan: data.status } }
  catch (error) { state.value.loading = false; state.value.error = errorMessage(error, 'We could not load your credit centre.') }
}

function action() {
  const page = ['INIT', 'REJECTED', 'SETTLED'].includes(status.value) ? '/pages/verification/index' : status.value === 'REVIEWING' ? '/pages/application/index' : status.value === 'APPROVED' ? '/pages/withdraw/index' : '/pages/bill/index'
  uni.navigateTo({ url: page })
}

onMounted(load)
usePageResume(load)
</script>

<template>
  <view class="gc-page home-page">
    <view class="gc-topbar"><BrandLockup /><text class="home-greeting">Hello, {{ state.profile?.name || 'there' }}</text></view>
      <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="hero gc-card gc-card--brand"><text class="gc-card__eyebrow">{{ statusLabel }}</text><text class="gc-card__value">{{ available ? formatMoney(available) : '—' }}</text><text class="gc-card__hint">Your available credit updates as your application moves forward.</text><button class="hero__button" @click="action"><text>{{ actionText }}</text><Icon name="chevron-right" :size="22" /></button></view>
      <view class="metric-row"><view class="metric"><text class="metric__label">Status</text><text class="metric__value">{{ loanStatusLabel(status) }}</text></view><view class="metric"><text class="metric__label">Loan term</text><text class="metric__value">{{ state.products?.[0]?.term_days || state.loan?.term_days || '—' }} days</text></view></view>
      <text class="gc-section-title">Your next steps</text>
      <view class="gc-grid">
        <navigator url="/pages/verification/index" class="gc-action-card"><view class="gc-action-card__icon"><Icon name="shield-check" :size="28" /></view><text class="gc-action-card__title">Verify identity</text><text class="gc-action-card__desc">Ghana Card and face check</text></navigator>
        <navigator url="/pages/application/index" class="gc-action-card"><view class="gc-action-card__icon"><Icon name="plus" :size="28" /></view><text class="gc-action-card__title">Complete application</text><text class="gc-action-card__desc">Add your application details</text></navigator>
        <navigator url="/pages/orders/index" class="gc-action-card"><view class="gc-action-card__icon"><Icon name="applications" :size="28" /></view><text class="gc-action-card__title">My applications</text><text class="gc-action-card__desc">Track every submission</text></navigator>
        <navigator url="/pages/support/index" class="gc-action-card"><view class="gc-action-card__icon"><Icon name="help" :size="28" /></view><text class="gc-action-card__title">Help centre</text><text class="gc-action-card__desc">We are here to help</text></navigator>
      </view>
      <view class="gc-safe-note">GalaCredit reviews applications responsibly. Rates, fees and repayment dates are shown before you confirm any loan.</view>
    </AsyncState>
  </view>
</template>

<style scoped>
.home-page { padding-top:38rpx; }
.home-greeting { color:var(--gc-muted); font-size:22rpx; }
.hero { margin-top:12rpx; padding-bottom:24rpx; }
.hero__button { display:flex; align-items:center; justify-content:space-between; width:100%; min-height:82rpx; margin-top:28rpx; padding:0 24rpx; border:0; border-radius:18rpx; color:#7e4908; background:#fff7e9; font-size:26rpx; font-weight:750; }
.hero__button::after { border:0; }
.metric-row { display:grid; grid-template-columns:1fr 1fr; gap:18rpx; margin-top:20rpx; }
.metric { padding:22rpx; border:1rpx solid var(--gc-border); border-radius:20rpx; background:#fff; }
.metric__label { display:block; color:var(--gc-muted); font-size:22rpx; }
.metric__value { display:block; margin-top:8rpx; font-size:27rpx; font-weight:750; }
</style>
