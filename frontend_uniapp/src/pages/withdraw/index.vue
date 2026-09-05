<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import { getLoanStatus, getProducts, previewPurchaseContract, sendOrderSmsCode, signPurchaseContract, submitWithdraw } from '../../api/index.js'
import { errorMessage, formatDate, formatMoney, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', loan: null, products: [] })
const selectedId = ref(null)
const contract = ref({ open: false, loading: false, content: '', id: null, agreed: false, readToEnd: false })
const sms = ref({ code: '', sent: false, cooldown: 0 })
const busy = ref(false)
const extensionSourceLoanId = ref(null)
let timer = null
let contractRequestId = 0

const selected = computed(() => state.value.products.find((item) => item.id === selectedId.value) || state.value.products[0] || null)
const displayAmount = computed(() => selected.value ? Number(selected.value.payment_amount || 0) : 0)

async function load() {
  if (!requireSession()) return
  try {
    extensionSourceLoanId.value = readExtensionSourceLoanId()
    const [loan, products] = await Promise.all([
      getLoanStatus(),
      getProducts(extensionSourceLoanId.value ? { extension_source_loan_id: extensionSourceLoanId.value } : {})
    ])
    state.value = { loading: false, error: '', loan, products: Array.isArray(products) ? products : [] }
    selectedId.value = state.value.products[0]?.id || null
  } catch (error) { state.value = { loading: false, error: errorMessage(error), loan: null, products: [] } }
}

/**
 * 从 App 路由或 H5 地址中读取展期原订单参数。
 *
 * :return: 合法的原订单 ID；不存在或非法时返回 null
 */
function readExtensionSourceLoanId() {
  let raw = ''
  if (typeof window !== 'undefined') raw = new URLSearchParams(window.location.search).get('extension_source_loan_id') || ''
  if (!raw && typeof getCurrentPages === 'function') {
    const pages = getCurrentPages()
    const current = pages?.[pages.length - 1]
    raw = current?.options?.extension_source_loan_id || current?.$page?.options?.extension_source_loan_id || ''
  }
  const value = Number.parseInt(raw, 10)
  return Number.isInteger(value) && value > 0 ? value : null
}

/**
 * 切换产品时清除旧合同和验证码，避免跨产品复用签署记录。
 *
 * :param productId: 新选中的产品 ID
 * :return: 无
 */
function selectProduct(productId) {
  if (selectedId.value === productId || busy.value || contract.value.loading) return
  contractRequestId += 1
  selectedId.value = productId
  contract.value = { open: false, loading: false, content: '', id: null, agreed: false, readToEnd: false }
  sms.value = { code: '', sent: false, cooldown: 0 }
}

async function openContract() {
  if (!selected.value || contract.value.loading) return
  const productId = selected.value.id
  const requestId = ++contractRequestId
  contract.value = { ...contract.value, open: true, loading: true, agreed: false, id: null, readToEnd: false }
  try {
    const result = await previewPurchaseContract({ product_id: productId, use_discount: true, extension_source_loan_id: extensionSourceLoanId.value || undefined })
    if (requestId !== contractRequestId || selected.value?.id !== productId) return
    const content = result.contract_content || ''
    // 内容无需滚动时直接视为已读完，避免短合同被 UI 锁死。
    contract.value = { ...contract.value, loading: false, content, readToEnd: content.length <= 1200 }
  } catch (error) {
    contract.value = { ...contract.value, open: false, loading: false }
    uni.showToast({ title: errorMessage(error, 'Unable to load the agreement.'), icon: 'none' })
  }
}

async function agreeContract() {
  if (!contract.value.content || contract.value.loading || !selected.value || !contract.value.readToEnd || !contract.value.agreed) return
  const productId = selected.value.id
  const requestId = ++contractRequestId
  contract.value.loading = true
  try {
    const result = await signPurchaseContract({ product_id: productId, use_discount: true, extension_source_loan_id: extensionSourceLoanId.value || undefined })
    if (requestId !== contractRequestId || selected.value?.id !== productId) return
    contract.value = { ...contract.value, loading: false, open: false, agreed: true, id: result.id }
    uni.showToast({ title: 'Agreement accepted', icon: 'none' })
  } catch (error) {
    contract.value.loading = false
    uni.showToast({ title: errorMessage(error, 'Unable to sign the agreement.'), icon: 'none' })
  }
}

function startCooldown(seconds) {
  if (timer) clearInterval(timer)
  sms.value.cooldown = Number(seconds || 60)
  timer = setInterval(() => {
    sms.value.cooldown = Math.max(0, sms.value.cooldown - 1)
    if (!sms.value.cooldown) { clearInterval(timer); timer = null }
  }, 1000)
}

async function sendSms() {
  if (busy.value || sms.value.cooldown) return
  busy.value = true
  try { const result = await sendOrderSmsCode(); sms.value.sent = true; startCooldown(result.cooldown_seconds); uni.showToast({ title: 'Confirmation code sent', icon: 'none' }) }
  catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to send confirmation code.'), icon: 'none' }) }
  finally { busy.value = false }
}

async function submit() {
  if (busy.value || !selected.value) return
  if (!contract.value.agreed || !contract.value.id) return openContract()
  if (!sms.value.sent) return sendSms()
  if (!/^\d{6}$/.test(sms.value.code)) return uni.showToast({ title: 'Enter the 6-digit confirmation code.', icon: 'none' })
  busy.value = true
  try {
    await submitWithdraw({ product_id: selected.value.id, sms_code: sms.value.code, contract_signature_id: contract.value.id, use_discount: true, extension_source_loan_id: extensionSourceLoanId.value || undefined })
    uni.showToast({ title: 'Application submitted', icon: 'none' })
    setTimeout(() => uni.reLaunch({ url: '/pages/bill/index' }), 700)
  } catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to submit this application.'), icon: 'none' }) }
  finally { busy.value = false }
}

onMounted(load)
usePageResume(() => { if (!busy.value && !contract.value.open) return load() })
onBeforeUnmount(() => {
  contractRequestId += 1
  if (timer) clearInterval(timer)
})
</script>

<template>
  <view class="gc-page">
    <PageHeader title="Choose a loan option" subtitle="Review the price, agreement and confirmation step." :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="!state.products.length" empty-text="No loan option is available for your current credit." @retry="load">
      <view class="gc-card"><text class="gc-section-title">Available credit</text><text class="available">{{ formatMoney(state.loan.available_credit_limit || state.loan.approved_credit_limit || 0) }}</text><text class="copy">Approved credit expires {{ formatDate(state.loan.approved_credit_expires_at) }}.</text></view>
      <view v-for="item in state.products" :key="item.id" class="gc-card product-card" :class="{ 'product-card--active': item.id === selected?.id, 'product-card--disabled': busy || contract.loading }" @click="selectProduct(item.id)"><view class="gc-row"><view><text class="product-name">{{ item.name }}</text><text class="product-desc">{{ item.rights_title || item.rights_desc || 'GalaCredit credit option' }}</text></view><radio :checked="item.id === selected?.id" color="#ea9518" /></view><view class="product-metrics"><view><text>Receive</text><strong>{{ formatMoney(item.nominal_loan_amount || item.ecard_face_value || item.payment_amount) }}</strong></view><view><text>Pay</text><strong>{{ formatMoney(item.payment_amount) }}</strong></view><view><text>Term</text><strong>{{ item.term_days }} days</strong></view></view></view>
      <view class="gc-card"><view class="gc-list-row"><text class="gc-list-row__label">Selected option</text><text class="gc-list-row__value">{{ selected?.name || '—' }}</text></view><view class="gc-list-row"><text class="gc-list-row__label">Amount to confirm</text><text class="gc-list-row__value">{{ formatMoney(displayAmount) }}</text></view><view class="gc-list-row"><text class="gc-list-row__label">Agreement</text><text class="gc-list-row__value">{{ contract.agreed ? 'Signed' : 'Read and sign' }}</text></view><button class="gc-button" :loading="busy" :disabled="busy || !selected" @click="submit">{{ !contract.agreed ? 'Read agreement' : !sms.sent ? 'Send confirmation code' : 'Confirm application' }}</button></view>
      <view v-if="sms.sent" class="gc-card"><text class="gc-section-title">Confirmation code</text><text class="copy">Enter the code sent to your registered phone.</text><input v-model="sms.code" class="gc-field" type="number" maxlength="6" placeholder="6-digit code" /><button class="gc-button gc-button--ghost" :disabled="busy || sms.cooldown > 0" @click="sendSms">{{ sms.cooldown ? `Resend in ${sms.cooldown}s` : 'Resend code' }}</button></view>
    </AsyncState>
    <view v-if="contract.open" class="modal-mask"><view class="modal gc-card"><text class="gc-section-title">GalaCredit Loan Agreement</text><scroll-view scroll-y class="contract-content" @scrolltolower="contract.readToEnd = true"><text>{{ contract.loading ? 'Loading agreement…' : contract.content }}</text></scroll-view><text class="contract-hint">{{ contract.readToEnd ? 'You have reached the end of the agreement.' : 'Scroll to the end to review the full agreement.' }}</text><label class="consent-row"><checkbox :disabled="!contract.readToEnd" :checked="contract.agreed" color="#ea9518" @click="contract.readToEnd && (contract.agreed = !contract.agreed)" /><text>I have read and agree to this agreement.</text></label><button class="gc-button" :disabled="contract.loading || !contract.readToEnd || !contract.agreed" @click="agreeContract">Sign agreement</button><button class="gc-button gc-button--ghost" :disabled="contract.loading" @click="contract.open = false">Cancel</button></view></view>
  </view>
</template>

<style scoped>
.available { display:block; font-size:52rpx; font-weight:800; }
.copy,.product-desc { display:block; color:var(--gc-muted); font-size:23rpx; line-height:1.5; }
.product-card { border:2rpx solid var(--gc-border); }
.product-card--active { border-color:var(--gc-brand); box-shadow:0 12rpx 30rpx rgba(234,149,24,.12); }
.product-card--disabled { opacity:.72; pointer-events:none; }
.product-name { display:block; font-size:29rpx; font-weight:750; }
.product-metrics { display:flex; gap:18rpx; margin-top:26rpx; }
.product-metrics view { flex:1; padding:16rpx; border-radius:16rpx; background:#f7f9fc; }
.product-metrics text,.product-metrics strong { display:block; }
.product-metrics text { color:var(--gc-muted); font-size:20rpx; }
.product-metrics strong { margin-top:6rpx; font-size:24rpx; }
.modal-mask { position:fixed; z-index:30; inset:0; display:flex; align-items:flex-end; padding:20rpx; background:rgba(19,26,39,.52); }
.modal { width:100%; max-height:88vh; margin:0; }
.contract-content { height:48vh; padding:22rpx; border-radius:18rpx; background:#f7f9fc; color:var(--gc-muted); font-size:23rpx; line-height:1.6; white-space:pre-wrap; }
.contract-hint { display:block; margin-top:12rpx; color:var(--gc-muted); font-size:21rpx; }
.consent-row { display:flex; gap:12rpx; align-items:flex-start; margin-top:20rpx; color:var(--gc-muted); font-size:22rpx; line-height:1.5; }
</style>
