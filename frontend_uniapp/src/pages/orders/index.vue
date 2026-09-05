<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import { getLoanHistory } from '../../api/index.js'
import { errorMessage, formatDate, formatMoney, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', loan: null })
const statusLabel = computed(() => ({ INIT: 'Not started', REVIEWING: 'Under review', APPROVED: 'Approved', WITHDRAWING: 'Preparing disbursement', DISBURSED: 'Repayment in progress', OVERDUE: 'Overdue', SETTLED: 'Settled', REJECTED: 'Needs an update' }[state.value.loan?.status] || 'Account update'))
const amount = computed(() => state.value.loan?.nominal_loan_amount || state.value.loan?.credit_limit || 0)

async function load() {
  if (!requireSession()) return
  try { state.value = { loading: false, error: '', loan: await getLoanHistory() } }
  catch (error) { state.value = { loading: false, error: errorMessage(error), loan: null } }
}

function openNext() {
  const status = state.value.loan?.status
  const url = ['DISBURSED', 'OVERDUE', 'SETTLED'].includes(status) ? '/pages/bill/index' : status === 'APPROVED' ? '/pages/withdraw/index' : '/pages/application/index'
  uni.navigateTo({ url })
}
onMounted(load)
usePageResume(load)
</script>

<template>
  <view class="gc-page">
    <PageHeader title="My applications" subtitle="A clear view of your current credit journey." :back="false" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="!state.loan" empty-text="No application yet." @retry="load">
      <view class="gc-card gc-card--brand"><text class="gc-card__eyebrow">{{ statusLabel }}</text><text class="gc-card__value">{{ amount ? formatMoney(amount) : '—' }}</text><text class="gc-card__hint">Application created {{ formatDate(state.loan.created_at) }}</text></view>
      <view class="gc-card">
        <text class="gc-section-title">Current status</text>
        <view class="gc-list-row"><text class="gc-list-row__label">Stage</text><text class="gc-list-row__value">{{ statusLabel }}</text></view>
        <view class="gc-list-row"><text class="gc-list-row__label">Available credit</text><text class="gc-list-row__value">{{ formatMoney(state.loan.available_credit_limit || 0) }}</text></view>
        <view class="gc-list-row"><text class="gc-list-row__label">Next due date</text><text class="gc-list-row__value">{{ formatDate(state.loan.due_date) }}</text></view>
        <button class="gc-button" @click="openNext">Open next step</button>
      </view>
      <view v-if="state.loan.latest_settled_loan" class="gc-card"><text class="gc-section-title">Previous settled loan</text><view class="gc-list-row"><text class="gc-list-row__label">Amount</text><text class="gc-list-row__value">{{ formatMoney(state.loan.latest_settled_loan.credit_limit) }}</text></view><view class="gc-list-row"><text class="gc-list-row__label">Settled</text><text class="gc-list-row__value">{{ formatDate(state.loan.latest_settled_loan.actual_repayment_date) }}</text></view></view>
    </AsyncState>
  </view>
</template>
