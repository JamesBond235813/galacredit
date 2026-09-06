<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import Icon from '../../components/Icon.vue'
import { getLoanStatus } from '../../api/index.js'
import { errorMessage, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', phone: '' })

async function load() {
  if (!requireSession()) return
  try {
    const loan = await getLoanStatus()
    state.value = { loading: false, error: '', phone: String(loan?.rights_contact_phone || '').trim() }
  } catch (error) {
    state.value = { loading: false, error: errorMessage(error, 'Support details are temporarily unavailable.'), phone: '' }
  }
}

function callSupport() {
  if (!state.value.phone) {
    uni.showToast({ title: 'No support number is available for this account yet.', icon: 'none' })
    return
  }
  uni.makePhoneCall({ phoneNumber: state.value.phone })
}

onMounted(load)
usePageResume(load)
</script>

<template>
  <view class="gc-page support-page">
    <PageHeader title="Customer Support" :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="gc-card hero-card"><view class="hero-icon"><Icon name="support" :size="28" /></view><view><text class="hero-title">How Can We Help?</text><text class="hero-desc">Find answers, review your applications and contact support.</text></view></view>
      <view class="gc-card quick-card"><text class="gc-section-title">Quick Access</text><view class="quick-actions"><navigator url="/pages/orders/index" class="quick-action"><view class="quick-icon"><Icon name="document" :size="20" /></view><view class="quick-copy"><text class="quick-title">View My Applications</text><text class="quick-desc">Review applications, decisions and repayment status</text></view><Icon name="chevron-right" :size="18" /></navigator><view class="quick-action" @click="load"><view class="quick-icon quick-icon-refresh"><Icon name="refresh" :size="20" /></view><view class="quick-copy"><text class="quick-title">Refresh Status</text><text class="quick-desc">Load the latest review, disbursement and repayment information</text></view><Icon name="chevron-right" :size="18" /></view></view></view>
      <view class="gc-card faq-card"><text class="gc-section-title">Frequently Asked Questions</text><view class="faq-list"><view class="faq"><text class="q">How do I apply for credit?</text><text class="a">Open the home page, select Apply Now, and complete identity and face verification.</text></view><view class="faq"><text class="q">Why is my application still under review?</text><text class="a">Review time depends on the completeness of your information and the applicable credit rules. Check My Applications for updates.</text></view><view class="faq"><text class="q">Where can I find repayment information?</text><text class="a">Open My Applications and select View Bill once your loan is disbursed or overdue.</text></view></view></view>
      <view class="gc-card support-hours-card"><text class="gc-section-title">Support Hours</text><text class="copy">Weekdays, 09:00 - 18:00. Requests submitted outside these hours will be handled during the next service period.</text></view>
    </AsyncState>
  </view>
</template>

<style scoped>
.support-page { padding-top:calc(40px + env(safe-area-inset-top)); padding-left:16px; padding-right:16px; }
.support-page :deep(.gc-page-header) { margin:0 -16px 10px; }
.support-page :deep(.gc-card) { margin-top:0; padding:18px; }
.support-page .quick-card,
.support-page .faq-card,
.support-page .support-hours-card { margin-top:16px; }
.support-page .gc-section-title { margin:0; font-size:17px; line-height:20px; }
.hero-card { display:flex; align-items:center; gap:12px; }
.hero-icon { display:flex; align-items:center; justify-content:center; width:56px; height:56px; flex:none; border-radius:18px; color:var(--gc-brand-deep); background:rgba(234,149,24,.12); }
.hero-title { display:block; font-size:20px; font-weight:700; }
.hero-desc,.copy,.a { display:block; margin-top:8px; color:var(--gc-muted); font-size:13px; line-height:1.7; }
.support-hours-card .copy { line-height:1.6; }
.quick-actions { margin-top:16px; }
.quick-action { display:flex; align-items:center; gap:12px; width:100%; padding:14px 0; color:inherit; text-decoration:none; }
.quick-action + .quick-action { border-top:1px solid #eef3fb; }
.quick-icon { display:flex; align-items:center; justify-content:center; width:40px; height:40px; flex:none; border-radius:14px; color:var(--gc-brand-deep); background:rgba(234,149,24,.12); }
.quick-icon-refresh { color:#0daa79; background:rgba(48,215,169,.14); }
.quick-copy { flex:1; min-width:0; }
.quick-title,.quick-desc { display:block; }
.quick-title { font-size:15px; font-weight:600; }
.quick-action > .gc-vant-icon { color:var(--gc-muted); }
.quick-desc { margin-top:4px; color:var(--gc-muted); font-size:12px; line-height:1.6; }
.faq-list { display:flex; flex-direction:column; gap:16px; margin-top:16px; }
.faq { padding:0; }
.faq + .faq { padding-top:16px; border-top:1px solid #eef3fb; }
.q { display:block; font-size:15px; font-weight:600; }
.a { margin-top:8px; }
</style>
