<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import { getLoanStatus, getProducts } from '../../api/index.js'
import { errorMessage, formatMoney, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', loan: null, products: [] })
let timer = null

const status = computed(() => String(state.value.loan?.status || 'REVIEWING').toUpperCase())
const creditLimit = computed(() => Number(state.value.loan?.available_credit_limit ?? state.value.loan?.approved_credit_limit ?? state.value.loan?.credit_limit ?? 0))
const recommended = computed(() => state.value.products.find((item) => Number(item.payment_amount || 0) <= creditLimit.value + 1e-6) || state.value.products[0] || null)
const others = computed(() => state.value.products.filter((item) => item.id !== recommended.value?.id))
const rejectReason = computed(() => state.value.loan?.review_note || 'Your application was not approved. Review your information and submit again.')

function routeByStatus(value) {
  if (value === 'INIT') return uni.reLaunch({ url: '/pages/application/index' })
  if (['WITHDRAWING', 'DISBURSED', 'OVERDUE'].includes(value)) return uni.reLaunch({ url: '/pages/bill/index' })
  if (value === 'SETTLED') return uni.reLaunch({ url: '/pages/home/index' })
  return false
}

async function load() {
  if (!requireSession()) return
  try {
    const loan = await getLoanStatus()
    if (routeByStatus(String(loan?.status || '').toUpperCase())) return
    let products = []
    if (String(loan?.status || '').toUpperCase() === 'APPROVED') {
      try { products = await getProducts() } catch { products = [] }
    }
    state.value = { loading: false, error: '', loan, products: Array.isArray(products) ? products : [] }
  } catch (error) {
    state.value = { loading: false, error: errorMessage(error, 'Unable to load your application status.'), loan: null, products: [] }
  }
}

function startPolling() {
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    if (status.value === 'REVIEWING') load()
    else { clearInterval(timer); timer = null }
  }, 10000)
}

function openProduct(productId) {
  if (!productId) return
  uni.navigateTo({ url: `/pages/withdraw/index?product_id=${encodeURIComponent(productId)}` })
}

function resubmit() {
  uni.navigateTo({ url: '/pages/application/index' })
}

onMounted(async () => { await load(); startPolling() })
usePageResume(() => { if (status.value === 'REVIEWING') load() })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <view class="gc-page">
    <PageHeader title="Application Review" :back="false" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view v-if="status === 'REVIEWING'" class="gc-card review-card"><view class="loading-orbit">◎</view><text class="card-title">Application Under Review</text><text class="copy">We are reviewing your information and determining your available credit limit.</text></view>
      <template v-else-if="status === 'APPROVED'">
        <view class="gc-card approval-card"><text class="approval-badge">Decision</text><view class="summary-grid"><view><text>Status</text><strong>Approved</strong></view><view><text>Valid For</text><strong>30 Days</strong></view><view><text>Credit Limit</text><strong>{{ formatMoney(creditLimit) }}</strong></view></view><text class="copy">This is your approved credit limit. Borrow responsibly.</text></view>
        <view v-if="recommended" class="gc-card product-card" @click="openProduct(recommended.id)"><view class="product-head"><view><text class="product-name">{{ recommended.name }}</text><text class="product-subtitle">{{ recommended.product_type === 'CASH_LOAN' ? 'Ghana short-term cash loan' : (recommended.rights_title || 'Service package') }}</text></view><text class="product-price">{{ formatMoney(recommended.payment_amount) }}</text></view><view class="product-tags"><text>Cash Received: {{ formatMoney(recommended.actual_disbursement_amount || (recommended.nominal_loan_amount - recommended.upfront_fee_amount) || recommended.ecard_face_value) }}</text><text>Term: {{ recommended.term_days }} days</text><text>Upfront Fees: {{ Number(recommended.upfront_fee_rate || 0) * 100 }}%</text></view><text class="rights-caption">Repayment</text><text class="copy">{{ recommended.product_type === 'CASH_LOAN' ? `Due on day ${recommended.repayment_due_day}, paid in ${recommended.installment_count} instalment(s)` : (recommended.rights_desc || 'Details are saved with your application') }}</text><button class="gc-button" @click.stop="openProduct(recommended.id)">View and Apply</button></view>
        <view v-for="item in others" :key="item.id" class="gc-card product-card" @click="openProduct(item.id)"><view class="product-head"><view><text class="product-name">{{ item.name }}</text><text class="product-subtitle">{{ item.product_type === 'CASH_LOAN' ? 'Ghana short-term cash loan' : (item.rights_title || 'Service package') }}</text></view><text class="product-price">{{ formatMoney(item.payment_amount) }}</text></view><view class="product-tags"><text>Term: {{ item.term_days }} days</text><text>Upfront Fees: {{ Number(item.upfront_fee_rate || 0) * 100 }}%</text></view><button class="gc-button gc-button--secondary" @click.stop="openProduct(item.id)">View and Apply</button></view>
      </template>
      <view v-else-if="status === 'REJECTED'" class="gc-card reject-card"><text class="card-title">Application Not Approved</text><text class="copy">{{ rejectReason }}</text><view class="summary-grid"><view><text>Decision</text><strong>Not Approved</strong></view><view><text>Next Step</text><strong>Update and Resubmit</strong></view></view><button class="gc-button" @click="resubmit">Resubmit Application</button></view>
      <view v-else class="gc-card review-card"><view class="loading-orbit">◎</view><text class="card-title">Updating Status</text><text class="copy">Loading the latest application status.</text></view>
    </AsyncState>
  </view>
</template>

<style scoped>
.review-heading { padding:28rpx 4rpx 10rpx; }
.review-title { display:block; font-size:42rpx; font-weight:800; }
.review-subtitle,.copy,.product-subtitle { display:block; margin-top:8rpx; color:var(--gc-muted); font-size:23rpx; line-height:1.6; }
.review-card { text-align:center; padding:52rpx 30rpx; }
.loading-orbit { display:flex; align-items:center; justify-content:center; width:108rpx; height:108rpx; margin:0 auto 20rpx; border:5rpx solid #f5d39d; border-top-color:var(--gc-brand); border-radius:50%; color:var(--gc-brand-deep); font-size:52rpx; animation:spin 1.2s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.card-title { display:block; font-size:31rpx; font-weight:800; }
.approval-badge { display:inline-block; padding:8rpx 18rpx; border-radius:999rpx; color:var(--gc-brand-deep); background:#fff0d7; font-size:21rpx; font-weight:750; }
.summary-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12rpx; margin-top:28rpx; }
.summary-grid view { min-width:0; padding:18rpx 10rpx; border-radius:16rpx; background:#f7f9fc; }
.summary-grid text,.summary-grid strong { display:block; }
.summary-grid text { color:var(--gc-muted); font-size:20rpx; }
.summary-grid strong { margin-top:8rpx; font-size:24rpx; word-break:break-word; }
.product-card { border:2rpx solid var(--gc-border); }
.product-card:active { border-color:var(--gc-brand); }
.product-head { display:flex; align-items:flex-start; justify-content:space-between; gap:18rpx; }
.product-name { display:block; font-size:29rpx; font-weight:800; }
.product-price { color:var(--gc-brand-deep); font-size:28rpx; font-weight:800; white-space:nowrap; }
.product-tags { display:flex; flex-wrap:wrap; gap:10rpx; margin-top:22rpx; }
.product-tags text { padding:8rpx 12rpx; border-radius:12rpx; color:var(--gc-muted); background:#f7f9fc; font-size:20rpx; }
.rights-caption { display:block; margin-top:20rpx; font-size:22rpx; font-weight:750; }
.reject-card { border-color:#f2c5c2; background:#fffafa; }
</style>
