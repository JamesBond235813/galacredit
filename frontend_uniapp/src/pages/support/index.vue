<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
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
  <view class="gc-page">
    <PageHeader title="Help centre" subtitle="Clear answers and human support when you need it." :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="gc-card">
        <text class="gc-section-title">Before you contact us</text>
        <text class="copy">Have your registered phone number and application stage ready. Never share your SMS login code or password with anyone.</text>
        <button class="gc-button" :disabled="!state.phone" @click="callSupport">{{ state.phone ? 'Call support' : 'Support number unavailable' }}</button>
      </view>
      <view class="gc-card">
        <text class="gc-section-title">Common questions</text>
        <view class="faq"><text class="q">Why is my application still under review?</text><text class="a">We may need to complete identity, location or responsible lending checks. Your status will update in the app.</text></view>
        <view class="faq"><text class="q">Where can I see fees and repayment dates?</text><text class="a">Open the loan option or repayment plan; the amount due is shown before confirmation.</text></view>
        <view class="faq"><text class="q">Can I decline a permission?</text><text class="a">Yes. We will use the remaining available signals or ask support for another way to complete the step.</text></view>
      </view>
    </AsyncState>
  </view>
</template>

<style scoped>.copy,.a { display:block; color:var(--gc-muted); font-size:24rpx; line-height:1.6; }.faq { padding:22rpx 0; border-bottom:1rpx solid var(--gc-border); }.faq:last-child { border-bottom:0; }.q { display:block; font-size:26rpx; font-weight:750; }.a { margin-top:8rpx; }</style>
