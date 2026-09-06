<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import { getUserInfo, submitRiskSignals, queryRiskTask } from '../../api/index.js'
import { collectRiskSignals } from '../../utils/risk.js'
import { errorMessage, requireSession, riskTaskStatusLabel } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'
import { getAppChannel, getPlatform, getRiskTask, setStorage } from '../../utils/platform.js'

const state = ref({ loading: true, error: '', phone: '', task: null })
const consentSms = ref(false)
const manualSms = ref('')
const busy = ref(false)
const RISK_TASK_STORAGE_KEY = 'galacredit_risk_task'
const smsReviewAvailable = getPlatform() === 'android' && getAppChannel() === 'internal'

async function load() {
  if (!requireSession()) return
  try {
    const user = await getUserInfo()
    const savedTask = getRiskTask()
    state.value = { ...state.value, loading: false, phone: user.phone || '', task: savedTask?.task_number ? savedTask : null }
  } catch (error) {
    state.value = { ...state.value, loading: false, error: errorMessage(error) }
  }
}

/**
 * 提交设备授权和最小化风控信号。
 *
 * :return: 无
 */
async function submit() {
  if (busy.value || !state.value.phone) return
  busy.value = true
  try {
    const manualRows = manualSms.value.trim() ? [{ address: 'user-provided', body: manualSms.value, time: Date.now() }] : []
    const payload = await collectRiskSignals({ consentSms: consentSms.value, windowDays: 90, providedSms: manualRows })
    const result = await submitRiskSignals({ phone: state.value.phone, ...payload })
    state.value.task = result
    if (result?.task_number) setStorage(RISK_TASK_STORAGE_KEY, result)
    uni.showToast({ title: result.task_number ? 'Security review started' : 'Security review saved', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: errorMessage(error, 'Unable to submit security review.'), icon: 'none' })
  } finally { busy.value = false }
}

/**
 * 兜底查询第三方异步风控任务。
 *
 * :return: 无
 */
async function refreshTask() {
  if (!state.value.task?.task_number || busy.value) return
  busy.value = true
  try {
    state.value.task = await queryRiskTask({ task_number: state.value.task.task_number })
    setStorage(RISK_TASK_STORAGE_KEY, state.value.task)
  }
  catch (error) { uni.showToast({ title: errorMessage(error), icon: 'none' }) }
  finally { busy.value = false }
}

onMounted(load)
usePageResume(() => { if (!busy.value) return load() })
</script>

<template>
  <view class="gc-page">
    <PageHeader title="Security review" subtitle="Use only the signals needed to protect your application." :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="gc-card">
        <text class="gc-section-title">What we collect</text>
        <view class="gc-list-row"><text class="gc-list-row__label">Device basics</text><text class="gc-list-row__value">Always minimal</text></view>
        <view v-if="smsReviewAvailable">
          <view class="gc-list-row"><text class="gc-list-row__label">SMS review</text><text class="gc-list-row__value">Optional · last 90 days</text></view>
          <label class="consent-row"><checkbox :checked="consentSms" color="#ea9518" @click="consentSms = !consentSms" /><text>I allow GalaCredit to scan only recent SMS messages that match the published risk keywords. Messages are filtered on this device before upload.</text></label>
          <view class="gc-safe-note">Only the authorised internal Android build can request SMS access, and only after this separate consent and the system permission.</view>
        </view>
        <view v-else>
          <view class="gc-safe-note">This build cannot access the system SMS inbox. If you choose, paste a message below; it will be filtered on this device using the same published keywords.</view>
          <label class="consent-row"><checkbox :checked="consentSms" color="#ea9518" @click="consentSms = !consentSms" /><text>I confirm that I want to submit only keyword matches from the message I provide.</text></label>
          <textarea v-model="manualSms" class="gc-field sms-paste" maxlength="4000" placeholder="Optional: paste a relevant SMS message" />
        </view>
        <button class="gc-button" :loading="busy" :disabled="busy" @click="submit">{{ busy ? 'Submitting…' : 'Continue securely' }}</button>
      </view>
      <view v-if="state.task" class="gc-card">
        <text class="gc-section-title">Review status</text>
        <view class="gc-list-row"><text class="gc-list-row__label">Task</text><text class="gc-list-row__value">{{ state.task.task_number || 'Saved locally' }}</text></view>
        <view v-if="state.task.task_number" class="gc-list-row"><text class="gc-list-row__label">Result</text><text class="gc-list-row__value">{{ riskTaskStatusLabel(state.task.task_status) }}{{ state.task.task_score ? ` · ${state.task.task_score}` : '' }}</text></view>
        <button v-if="state.task.task_number" class="gc-button gc-button--ghost" :disabled="busy" @click="refreshTask">Refresh result</button>
      </view>
    </AsyncState>
  </view>
</template>

<style scoped>
.consent-row { display:flex; gap:12rpx; align-items:flex-start; margin-top:26rpx; color:var(--gc-muted); font-size:23rpx; line-height:1.5; }
.consent-row checkbox { transform:scale(.8); transform-origin:top left; }
.sms-paste { min-height: 180rpx; margin-top: 20rpx; }
</style>
