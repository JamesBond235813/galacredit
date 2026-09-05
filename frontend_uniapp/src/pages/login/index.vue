<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import BrandLockup from '../../components/BrandLockup.vue'
import { createSliderCaptcha, sendCode, smsLogin, submitRiskSignals, verifySliderCaptcha } from '../../api/index.js'
import { errorMessage, isValidGhanaPhone, normalizeGhanaPhone } from '../../utils/app.js'
import { getAppChannel, getPlatform, getStorage, setStorage } from '../../utils/platform.js'
import { collectRiskSignals } from '../../utils/risk.js'
import { canVerifySlider } from '../../utils/captcha.js'

const phone = ref('')
const smsCode = ref('')
const consent = ref(false)
const smsConsent = ref(false)
const busy = ref(false)
const captchaBusy = ref(false)
const captchaVisible = ref(false)
const captcha = ref(null)
const sliderValue = ref(0)
const cooldown = ref(0)
let timer = null
let sliderStartedAt = 0
let captchaVerificationSubmitted = false

const normalizedPhone = computed(() => normalizeGhanaPhone(phone.value))
const canRequest = computed(() => isValidGhanaPhone(phone.value) && consent.value && !busy.value && cooldown.value <= 0)
const canSignIn = computed(() => /^\d{6}$/.test(smsCode.value) && isValidGhanaPhone(phone.value) && consent.value && !busy.value)

function notify(message) { uni.showToast({ title: message, icon: 'none', duration: 2600 }) }

function openAgreement() {
  uni.navigateTo({ url: '/pages/agreement/index' })
}

/**
 * 开始发送登录验证码前创建滑块挑战。
 *
 * :return: 无
 */
async function openCaptcha() {
  if (!canRequest.value) return notify('Enter a valid Ghana number and accept the terms.')
  captchaBusy.value = true
  captchaVerificationSubmitted = false
  captcha.value = null
  try {
    captcha.value = await createSliderCaptcha({ phone: normalizedPhone.value, width: 620 })
    sliderValue.value = 0
    sliderStartedAt = Date.now()
    captchaVisible.value = true
  } catch (error) { notify(errorMessage(error, 'Unable to start security check.')) }
  finally { captchaBusy.value = false }
}

/**
 * 完成滑块后换取短信发送票据。
 *
 * :param event: 滑块变化事件
 * :return: 无
 */
async function verifyCaptcha(event) {
  sliderValue.value = Number(event.detail.value || 0)
  if (!canVerifySlider(sliderValue.value, { busy: captchaBusy.value, visible: captchaVisible.value, hasCaptcha: Boolean(captcha.value), submitted: captchaVerificationSubmitted })) return
  captchaBusy.value = true
  try {
    const offset = Math.max(Number(captcha.value.width || 420) - Number(captcha.value.block_size || 44), 0)
    const elapsed = Math.max(Date.now() - sliderStartedAt, Number(captcha.value.min_elapsed_ms || 1200))
    const result = await verifySliderCaptcha({ phone: normalizedPhone.value, captcha_id: captcha.value.captcha_id, offset_x: offset, elapsed_ms: elapsed })
    const response = await sendCode({ phone: normalizedPhone.value, captcha_ticket: result.captcha_ticket })
    captchaVerificationSubmitted = true
    captcha.value = null
    cooldown.value = Number(response.cooldown_seconds || 60)
    timer = setInterval(() => { cooldown.value -= 1; if (cooldown.value <= 0) { cooldown.value = 0; clearInterval(timer); timer = null } }, 1000)
    captchaVisible.value = false
    notify('Verification code sent.')
  } catch (error) { sliderValue.value = 0; captchaVerificationSubmitted = false; notify(errorMessage(error, 'Security check failed. Please retry.')) }
  finally { captchaBusy.value = false }
}

/**
 * 关闭滑块挑战并清理一次性状态，避免旧挑战被重复提交。
 *
 * :return: 无
 */
function closeCaptcha() {
  captchaVisible.value = false
  captchaVerificationSubmitted = false
  captcha.value = null
  sliderValue.value = 0
}

/**
 * 校验短信验证码并保存登录态。
 *
 * :return: 无
 */
async function signIn() {
  if (!canSignIn.value) return notify('Complete the phone, code and consent fields.')
  busy.value = true
  try {
    const result = await smsLogin({ phone: normalizedPhone.value, sms_code: smsCode.value })
    // 登录切换账号时不能沿用上一位用户的风控任务号。
    setStorage('galacredit_risk_task', '')
    const loginToken = result.access_token || result.token
    setStorage('token', loginToken)
    // 登录成功后仅在 App 端补传设备风险摘要；短信读取仍需内部渠道、单独同意和系统授权。
    if (getPlatform() !== 'h5') {
      const includeSms = getPlatform() === 'android' && getAppChannel() === 'internal' && smsConsent.value
      const submitRisk = async () => {
        try {
          const riskPayload = await collectRiskSignals({ consentSms: includeSms, windowDays: 90 })
          const riskResult = await submitRiskSignals({ phone: normalizedPhone.value, ...riskPayload })
          // 用户可能在弱网请求完成前退出；只允许写回仍属于本次登录的任务摘要。
          if (riskResult?.task_number && getStorage('token') === loginToken) setStorage('galacredit_risk_task', riskResult)
        } catch (error) {
          // 风控补传失败不阻断已完成的登录；页面后续可在安全检查中重试。
        }
      }
      // 只有 internal Android 勾选短信时需要等待系统权限流程；其他渠道后台补传，避免弱网阻塞进入首页。
      if (includeSms) await submitRisk()
      else void submitRisk()
    }
    uni.reLaunch({ url: '/pages/home/index' })
  } catch (error) { notify(errorMessage(error, 'Sign in failed. Check your code.')) }
  finally { busy.value = false }
}

onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <view class="gc-page login-page">
    <view class="login-page__hero"><BrandLockup /><text class="login-page__headline">A clearer path to your next step.</text><text class="login-page__intro">Secure access to your credit application, identity checks and repayment plan.</text></view>
    <view class="gc-card login-card">
      <text class="gc-section-title">Sign in securely</text>
      <view class="phone-wrap"><text class="phone-prefix">🇬🇭 +233</text><input v-model="phone" class="gc-field phone-field" type="number" maxlength="9" placeholder="Mobile number" /></view>
      <view class="code-row"><input v-model="smsCode" class="gc-field code-field" type="number" maxlength="6" placeholder="6-digit code" /><button class="gc-button gc-button--secondary code-button" :disabled="!canRequest || captchaBusy" @click="openCaptcha">{{ cooldown > 0 ? `${cooldown}s` : captchaBusy ? 'Checking…' : 'Send code' }}</button></view>
      <label class="consent-row"><checkbox :checked="consent" color="#ea9518" @click="consent = !consent" /><text>I agree to GalaCredit's <text class="gc-link" @click.stop="openAgreement">User Agreement</text>, <text class="gc-link" @click.stop="openAgreement">Privacy Policy</text> and <text class="gc-link" @click.stop="openAgreement">Personal Data Authorization</text>.</text></label>
      <label v-if="getPlatform() === 'android' && getAppChannel() === 'internal'" class="consent-row consent-row--optional"><checkbox :checked="smsConsent" color="#ea9518" @click="smsConsent = !smsConsent" /><text>I allow an optional 90-day SMS risk review. Only messages matching the published keywords are uploaded.</text></label>
      <text class="gc-safe-note">We use only the information needed to provide and protect the service. Sensitive device permissions are requested only when required and supported.</text>
      <button class="gc-button" :disabled="!canSignIn" :loading="busy" @click="signIn">{{ busy ? 'Signing in…' : 'Continue' }}</button>
    </view>
    <view class="login-page__footer"><text>GalaCredit · Responsible credit, made clear.</text></view>
    <view v-if="captchaVisible" class="captcha-mask"><view class="captcha-modal gc-card"><text class="gc-section-title">Complete security check</text><text class="captcha-copy">Slide all the way to confirm you are human.</text><slider :value="sliderValue" :disabled="captchaBusy" activeColor="#ea9518" backgroundColor="#f1e9dc" block-size="24" :show-value="false" @change="verifyCaptcha" /><button class="gc-button gc-button--ghost" :disabled="captchaBusy" @click="closeCaptcha">Cancel</button></view></view>
  </view>
</template>

<style scoped>
.login-page { display:flex; flex-direction:column; padding-top:74rpx; background:linear-gradient(180deg,#fffaf2 0,#f6f8fb 56%); }
.login-page__hero { padding:0 6rpx; }
.login-page__headline { display:block; margin-top:60rpx; font-size:52rpx; line-height:1.12; font-weight:800; letter-spacing:0; }
.login-page__intro { display:block; margin-top:18rpx; color:var(--gc-muted); font-size:26rpx; line-height:1.55; }
.login-card { margin-top:34rpx; }
.phone-wrap { position:relative; display:flex; align-items:center; }
.phone-prefix { position:absolute; z-index:1; left:24rpx; font-size:27rpx; font-weight:650; }
.phone-field { padding-left:210rpx; margin-top:18rpx; }
.code-row { display:flex; gap:16rpx; align-items:center; }
.code-field { flex:1; }
.code-button { width:210rpx; min-height:94rpx; margin-top:18rpx; padding:0 12rpx; font-size:23rpx; }
.consent-row { display:flex; gap:12rpx; align-items:flex-start; margin-top:26rpx; color:var(--gc-muted); font-size:22rpx; line-height:1.5; }
.consent-row checkbox { transform:scale(.78); transform-origin:top left; }
.login-page__footer { margin-top:auto; padding:48rpx 0 12rpx; text-align:center; color:#9aa4b3; font-size:21rpx; }
.captcha-mask { position:fixed; z-index:20; inset:0; display:flex; align-items:flex-end; padding:24rpx; background:rgba(19,26,39,.52); }
.captcha-modal { width:100%; padding:34rpx; margin:0; }
.captcha-copy { display:block; color:var(--gc-muted); font-size:24rpx; }
.captcha-modal slider { margin:40rpx 0 20rpx; }
</style>
