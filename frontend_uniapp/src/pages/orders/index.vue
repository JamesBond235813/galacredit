<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import Icon from '../../components/Icon.vue'
import { getLoanHistory } from '../../api/index.js'
import { errorMessage, formatDateTime, formatMoney, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'
import { applicationNextPage } from '../../utils/application-flow.js'

const state = ref({ loading: true, error: '', loan: null })
const statusLabel = computed(() => ({ INIT: 'Not Started', REVIEWING: 'Under Review', APPROVED: 'Approved', WITHDRAWING: 'Preparing Disbursement', DISBURSED: 'Repayment in Progress', OVERDUE: 'Overdue', SETTLED: 'Settled', REJECTED: 'Needs an Update' }[state.value.loan?.status] || 'Account Update'))
const amount = computed(() => state.value.loan?.nominal_loan_amount || state.value.loan?.credit_limit || 0)

async function load() {
  if (!requireSession()) return
  try { state.value = { loading: false, error: '', loan: await getLoanHistory() } }
  catch (error) { state.value = { loading: false, error: errorMessage(error), loan: null } }
}

function openNext() {
  uni.navigateTo({ url: applicationNextPage(state.value.loan?.status) })
}
onMounted(load)
usePageResume(load)
</script>

<template>
  <view class="gc-page orders-page">
    <PageHeader title="My Applications" :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="!state.loan" empty-text="No application yet." @retry="load">
      <view class="gc-card order-card">
        <view class="order-head"><view><text class="order-label">{{ state.loan?.status === 'INIT' ? 'Credit Application' : 'Current Loan' }}</text><text class="order-title">{{ state.loan?.status === 'INIT' ? 'Estimated Credit Limit' : 'Loan Details' }}</text></view><text class="status-chip">{{ statusLabel }}</text></view>
        <view class="order-amount"><text>GHS</text><text>{{ amount ? formatMoney(amount).replace(/^GHS\s*/, '') : '--' }}</text></view>
        <view v-if="!state.loan || state.loan?.status === 'INIT'" class="order-notice"><Icon name="info" :size="14" /><text>Complete your application to receive an approved credit limit</text></view>
        <view class="order-meta"><view class="meta-row"><text>Application Date</text><text>{{ formatDateTime(state.loan.created_at) }}</text></view><view v-if="state.loan?.product_name" class="meta-row"><text>Loan Option</text><text>{{ state.loan.product_name }}</text></view><view v-if="state.loan?.disbursed_at" class="meta-row"><text>Disbursement Date</text><text>{{ formatDateTime(state.loan.disbursed_at) }}</text></view></view>
        <text class="order-desc">Complete identity verification and provide the required information to receive a credit decision.</text>
        <button class="gc-button order-btn" @click="openNext">{{ state.loan?.status === 'INIT' ? 'Start Application' : 'Open next step' }}</button>
      </view>
      <view class="gc-card timeline-card">
        <text class="gc-section-title">Application Progress</text>
        <view class="timeline-list"><view class="timeline-item active"><view class="timeline-dot" /><view><text class="timeline-title">Application Created</text><text class="timeline-desc">Your initial credit application is ready</text></view></view><view class="timeline-item" :class="{ active: state.loan?.status !== 'INIT' }"><view class="timeline-dot" /><view><text class="timeline-title">Information Review</text><text class="timeline-desc">Your identity and application details are being reviewed</text></view></view><view class="timeline-item" :class="{ active: ['APPROVED','WITHDRAWING','DISBURSED','OVERDUE','SETTLED'].includes(state.loan?.status) }"><view class="timeline-dot" /><view><text class="timeline-title">Credit Approved</text><text class="timeline-desc">Choose a loan option after approval</text></view></view><view class="timeline-item" :class="{ active: ['DISBURSED','OVERDUE','SETTLED'].includes(state.loan?.status) }"><view class="timeline-dot" /><view><text class="timeline-title">MoMo Disbursement</text><text class="timeline-desc">Funds are sent and the repayment bill is created</text></view></view></view>
      </view>
      <view v-if="state.loan.latest_settled_loan" class="gc-card"><text class="gc-section-title">Previous settled loan</text><view class="gc-list-row"><text class="gc-list-row__label">Amount</text><text class="gc-list-row__value">{{ formatMoney(state.loan.latest_settled_loan.credit_limit) }}</text></view><view class="gc-list-row"><text class="gc-list-row__label">Settled</text><text class="gc-list-row__value">{{ formatDateTime(state.loan.latest_settled_loan.actual_repayment_date) }}</text></view></view>
    </AsyncState>
  </view>
</template>

<style scoped>
.orders-page { padding-top:calc(24px + env(safe-area-inset-top)); padding-left:16px; padding-right:16px; }
.orders-page :deep(.gc-page-header) { margin-bottom:10px; }
.orders-page :deep(.gc-card) { margin-top:0; }
.order-card,.timeline-card { padding:18px; }
.order-head { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; }
.order-label { display:block; color:#9aa4b3; font-size:13px; }
.order-title { display:block; margin-top:8px; font-size:24px; font-weight:700; }
.status-chip { display:inline-flex; align-items:center; min-height:28px; padding:0 10px; border-radius:999px; color:#b96f00; background:#fff3dc; font-size:12px; font-weight:700; white-space:nowrap; }
.order-amount { display:flex; align-items:baseline; height:42px; margin-top:20px; color:var(--gc-brand-deep); line-height:42px; }
.order-amount text:first-child { font-size:22px; }
.order-amount text:last-child { display:block; margin-left:5px; font-size:42px; line-height:42px; font-weight:700; }
.order-notice { display:flex; align-items:center; gap:6px; height:48px; min-height:48px; margin-top:14px; padding:8px 12px; border-radius:8px; color:var(--gc-brand); background:rgba(234,149,24,.05); font-size:13px; line-height:1.45; }
.order-meta { margin-top:22px; padding-top:18px; border-top:1px dashed #dbe4f2; }
.meta-row { display:flex; align-items:center; justify-content:space-between; gap:12px; color:var(--gc-muted); font-size:13px; }
.meta-row + .meta-row { margin-top:10px; }
.order-desc { display:block; margin:18px 0 0; color:var(--gc-muted); font-size:13px; line-height:1.7; }
.order-btn { margin-top:24px; min-height:50px; }
.orders-page :deep(.timeline-card) { margin-top:16px; }
.timeline-card .gc-section-title { margin:0; font-size:17px; line-height:21px; }
.timeline-list { display:flex; flex-direction:column; gap:16px; margin-top:18px; }
.timeline-item { display:flex; gap:12px; opacity:.55; }
.timeline-item.active { opacity:1; }
.timeline-dot { position:relative; width:12px; height:12px; flex:none; margin-top:4px; border-radius:50%; background:#d5dfed; }
.timeline-item.active .timeline-dot { background:var(--gc-brand); }
.timeline-item:not(:last-child) .timeline-dot::after { content:''; position:absolute; top:14px; left:5px; width:2px; height:34px; background:#e5edf8; }
.timeline-title,.timeline-desc { display:block; }
.timeline-title { font-size:14px; font-weight:600; }
.timeline-desc { margin-top:6px; color:var(--gc-muted); font-size:12px; line-height:1.6; }
</style>
