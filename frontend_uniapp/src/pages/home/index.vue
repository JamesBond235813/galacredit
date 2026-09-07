<script setup>
import { computed, onMounted, ref } from 'vue'
import BrandLockup from '../../components/BrandLockup.vue'
import AsyncState from '../../components/AsyncState.vue'
import Icon from '../../components/Icon.vue'
import { loadHomeData } from '../../api/index.js'
import { errorMessage, formatMoney, loanStatusLabel, requireSession } from '../../utils/app.js'
import { applicationNextPage } from '../../utils/application-flow.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', profile: null, loan: null, products: [] })
const status = computed(() => state.value.loan?.status || 'INIT')
const available = computed(() => state.value.loan?.available_credit_limit ?? state.value.loan?.approved_credit_limit ?? state.value.loan?.credit_limit ?? 0)
const actionText = computed(() => ({ INIT: 'Apply Now', REVIEWING: 'View Review Status', REJECTED: 'Resubmit Application', APPROVED: 'Choose a Loan', WITHDRAWING: 'View Disbursement', DISBURSED: 'View Repayment Bill', OVERDUE: 'Resolve Overdue Bill', SETTLED: 'Apply Again' }[status.value] || 'Processing'))
const statusLabel = computed(() => ({ INIT: 'Ready when you are', REVIEWING: 'Application under review', APPROVED: 'Credit approved', WITHDRAWING: 'Preparing disbursement', DISBURSED: 'Repayment in progress', OVERDUE: 'Action required', SETTLED: 'Previous loan settled', REJECTED: 'Application needs an update' }[status.value] || 'Account update'))
const displayProduct = computed(() => state.value.products?.find((item) => item.product_type === 'CASH_LOAN') || state.value.products?.[0] || {})
const estimatedLimit = computed(() => Number(displayProduct.value.expected_credit_limit ?? displayProduct.value.nominal_loan_amount ?? 0))
const limitTitle = computed(() => status.value === 'REJECTED' ? 'Application status' : ['INIT', 'SETTLED'].includes(status.value) ? 'Estimated Credit Limit (GHS)' : status.value === 'REVIEWING' ? 'Maximum Available Credit (GHS)' : 'Available Credit (GHS)')
const limitAmount = computed(() => status.value === 'REJECTED' ? 'Please improve your credit record and apply again later.' : status.value === 'REVIEWING' ? 'Under review' : (['INIT', 'SETTLED'].includes(status.value) ? (estimatedLimit.value ? `${formatMoney(estimatedLimit.value)}+` : '--') : available.value ? formatMoney(available.value) : '--'))
const rateText = computed(() => {
  const rate = displayProduct.value?.min_daily_interest_rate ?? displayProduct.value?.fee_components?.min_daily_interest_rate ?? displayProduct.value?.fee_components?.interest_rate
  return rate === undefined || rate === null ? '--' : `${Number(rate) * 100}%`
})
const termText = computed(() => {
  const term = displayProduct.value?.max_loan_term_days || displayProduct.value?.repayment_due_day || displayProduct.value?.term_days || state.value.loan?.term_days
  return term === undefined || term === null ? '--' : `${term} days`
})

async function load() {
  if (!requireSession()) return
  state.value.loading = true
  try { const data = await loadHomeData(); state.value = { loading: false, error: '', ...data, loan: data.status } }
  catch (error) { state.value.loading = false; state.value.error = errorMessage(error, 'We could not load your credit centre.') }
}

function action() {
  uni.navigateTo({ url: applicationNextPage(status.value) })
}

onMounted(load)
usePageResume(load)
</script>

<template>
  <view class="gc-page home-page">
    <view class="gc-topbar"><BrandLockup /></view>
      <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="hero gc-card gc-card--brand"><view class="hero-content"><text class="gc-card__eyebrow">{{ limitTitle }}</text><text class="gc-card__value">{{ limitAmount }}</text></view><button class="hero__button" @click="action">{{ actionText }}</button><view class="hero-note"><view><text>{{ rateText }}</text><text>{{ termText }}</text></view><view><text>Min daily interest rate</text><text>Max loan period.</text></view></view></view>
      <view class="service-section"><text class="gc-section-title">More Services</text><view class="service-grid"><navigator url="/pages/support/index" class="service-card"><view class="service-copy"><text class="service-name">Customer Support</text><text class="service-desc">Help centre and assistance</text></view><view class="service-icon"><Icon name="support" :size="22" /></view></navigator><navigator url="/pages/orders/index" class="service-card"><view class="service-copy"><text class="service-name">My Applications</text><text class="service-desc">View application history</text></view><view class="service-icon service-icon-warm"><Icon name="applications" :size="22" /></view></navigator><navigator v-if="status === 'REVIEWING'" url="/pages/verification/index" class="service-card"><view class="service-copy"><text class="service-name">Update Identity</text><text class="service-desc">Resubmit your identity details</text></view><view class="service-icon service-icon-soft"><Icon name="shield-check" :size="22" /></view></navigator><navigator v-if="['DISBURSED', 'OVERDUE'].includes(status)" url="/pages/withdraw/index" class="service-card"><view class="service-copy"><text class="service-name">Loan Extension</text><text class="service-desc">Review available extension options</text></view><view class="service-icon service-icon-soft"><Icon name="plus" :size="22" /></view></navigator></view></view>
    </AsyncState>
  </view>
</template>

<style scoped>
.home-page { padding-top:calc(40px + env(safe-area-inset-top)); padding-left:16px; padding-right:16px; }
.home-page :deep(.gc-topbar) { margin-bottom:18px; }
.home-page :deep(.gc-brand) { gap:9px; }
.home-page :deep(.gc-brand__logo) { width:30px; height:30px; border-radius:0; background-color:transparent; background-size:100%; box-shadow:none; }
.home-page :deep(.gc-brand__name) { font-size:26px; line-height:33px; letter-spacing:-1px; font-weight:700; }
.home-page :deep(.gc-brand__tagline) { display:none; }
.hero { margin-top:0; padding:18px 18px 20px; background:radial-gradient(circle at top right,rgba(255,255,255,.22),transparent 34%),linear-gradient(135deg,rgba(200,111,12,.96) 0%,rgba(234,149,24,.94) 58%,rgba(242,165,61,.88) 100%); }
.hero-content { padding:20px 6px 28px; text-align:center; }
.hero__button { display:flex; align-items:center; justify-content:center; width:100%; height:50px; min-height:50px; margin-top:0; padding:0 12px; border:0; border-radius:14px; color:var(--gc-brand-deep); background:#fff; box-shadow:0 12px 28px rgba(16,43,88,.16); font-size:16px; font-weight:600; }
.hero__button::after { border:0; }
.hero-note { display:flex; flex-direction:column; gap:6px; margin:14px 4px 0; color:rgba(255,255,255,.84); font-size:12px; line-height:1.7; }
.hero-note view { display:flex; flex-direction:column; gap:4rpx; }
.hero-note view { flex-direction:row; align-items:center; justify-content:space-between; gap:16px; }
.hero-note view text:first-child { font-size:12px; font-weight:400; color:rgba(255,255,255,.84); }
.hero-note view:first-child text:first-child,.hero-note view:last-child text:first-child { font-size:12px; font-weight:400; }
.hero-note view::after { display:none; }
.hero-note view text:last-child { color:rgba(255,255,255,.84); }
.home-page .gc-card__eyebrow { font-size:14px; }
.home-page .gc-card__eyebrow { text-transform:none; letter-spacing:0; color:rgba(255,255,255,.84); }
.home-page .gc-card__value { margin-top:10px; font-size:46px; line-height:1; font-weight:700; }
.service-section { margin-top:18px; }
.service-section > .gc-section-title { margin:0; font-size:17px; line-height:20px; font-weight:700; }
.service-grid { display:grid; grid-template-columns:1fr; gap:12px; margin-top:18px; }
.service-card { display:flex; align-items:center; justify-content:space-between; gap:12px; height:106px; min-height:106px; padding:16px; border:1rpx solid #e8eef8; border-radius:18px; background:linear-gradient(180deg,#fff 0%,#f8fbff 100%); box-shadow:0 18px 38px rgba(23,32,51,.08); color:var(--gc-ink); text-decoration:none; text-align:left; }
.service-copy { display:flex; flex:1; flex-direction:column; gap:8px; min-width:0; }
.service-name,.service-desc { display:block; }
.service-name { font-size:16px; font-weight:700; }
.service-desc { margin-top:0; color:var(--gc-muted); font-size:13px; line-height:1.6; }
.service-icon { display:flex; align-items:center; justify-content:center; width:42px; height:42px; flex:none; border-radius:50%; color:var(--gc-brand-deep); background:rgba(234,149,24,.1); }
.service-icon-warm { color:var(--gc-warning); background:rgba(255,155,61,.12); }
.service-icon-soft { color:#0c9f7b; background:rgba(48,215,169,.14); }
/* 窄屏设备上品牌锁定块与问候语不能挤出视口，否则首页会出现整页横向偏移。 */
@media screen and (max-width: 390px) {
  .home-page .gc-topbar { min-width: 0; }
  .home-page .gc-topbar :deep(.gc-brand) { min-width: 0; flex: 1; gap: 12rpx; }
  .home-page .gc-topbar :deep(.gc-brand__logo) { width: 92rpx; height: 92rpx; border-radius: 0; }
  .home-page .gc-topbar :deep(.gc-brand__name) { font-size: 42rpx; }
  .home-page .gc-topbar :deep(.gc-brand__tagline) { margin-top: 6rpx; font-size: 20rpx; }
  .home-greeting { max-width: 112rpx; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
}
</style>
