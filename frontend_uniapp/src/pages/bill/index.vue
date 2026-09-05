<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import { getBill, requestRepayment } from '../../api/index.js'
import { errorMessage, formatDate, formatMoney, installmentStatusLabel, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', loan: null })
const busy = ref(false)
const remaining = computed(() => Number(state.value.loan?.remaining_repayment_amount || 0))
const overdue = computed(() => state.value.loan?.status === 'OVERDUE' || Number(state.value.loan?.penalty_amount || 0) > 0)

async function load() {
  if (!requireSession()) return
  try { state.value = { loading: false, error: '', loan: await getBill() } }
  catch (error) { state.value = { loading: false, error: errorMessage(error), loan: null } }
}

async function requestPayment() {
  if (busy.value || remaining.value <= 0) return
  busy.value = true
  try { await requestRepayment({}); uni.showToast({ title: 'Repayment request received', icon: 'none' }) }
  catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to start repayment.'), icon: 'none' }) }
  finally { busy.value = false }
}
onMounted(load)
usePageResume(() => { if (!busy.value) return load() })
</script>

<template>
  <view class="gc-page">
    <PageHeader title="Repayment plan" subtitle="Know what is due before you make a payment." :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="!state.loan" empty-text="No repayment bill is available." @retry="load">
      <view class="gc-card" :class="{ 'bill-alert': overdue }"><text class="gc-card__eyebrow">{{ overdue ? 'Action required' : 'Remaining balance' }}</text><text class="gc-card__value">{{ formatMoney(remaining) }}</text><text class="gc-card__hint">{{ overdue ? 'Your bill includes an overdue amount or fee.' : 'Next due ' + formatDate(state.loan.due_date) }}</text></view>
      <view class="gc-card">
        <text class="gc-section-title">Summary</text>
        <view class="gc-list-row"><text class="gc-list-row__label">Total repayment</text><text class="gc-list-row__value">{{ formatMoney(state.loan.total_repayment_amount) }}</text></view>
        <view class="gc-list-row"><text class="gc-list-row__label">Paid</text><text class="gc-list-row__value">{{ formatMoney(state.loan.repaid_amount) }}</text></view>
        <view class="gc-list-row"><text class="gc-list-row__label">Penalty</text><text class="gc-list-row__value">{{ formatMoney(state.loan.penalty_amount) }}</text></view>
        <view class="gc-list-row"><text class="gc-list-row__label">Installments</text><text class="gc-list-row__value">{{ state.loan.installment_periods || state.loan.installment_count || 1 }}</text></view>
        <button class="gc-button" :disabled="busy || remaining <= 0" :loading="busy" @click="requestPayment">{{ remaining > 0 ? 'Arrange repayment' : 'Nothing due' }}</button>
      </view>
      <view v-if="state.loan.installments?.length" class="gc-card"><text class="gc-section-title">Installments</text><view v-for="item in state.loan.installments" :key="item.id || item.period_no" class="installment"><view><text class="installment__period">Period {{ item.period_no }}</text><text class="installment__date">Due {{ formatDate(item.due_date) }}</text></view><view class="installment__right"><text class="installment__amount">{{ formatMoney(item.remaining_amount || item.due_amount) }}</text><text class="gc-badge" :class="{ 'gc-badge--warning': item.status !== 'PAID' }">{{ installmentStatusLabel(item.status) }}</text></view></view></view>
    </AsyncState>
  </view>
</template>

<style scoped>
.bill-alert { border-color:#f2c5c2; background:#fff7f6; }
.installment { display:flex; align-items:center; justify-content:space-between; padding:22rpx 0; border-bottom:1rpx solid var(--gc-border); }
.installment:last-child { border-bottom:0; }
.installment__period,.installment__date,.installment__amount { display:block; }
.installment__period { font-size:26rpx; font-weight:700; }
.installment__date { margin-top:6rpx; color:var(--gc-muted); font-size:22rpx; }
.installment__right { display:flex; flex-direction:column; align-items:flex-end; gap:8rpx; }
.installment__amount { font-size:26rpx; font-weight:750; }
</style>
