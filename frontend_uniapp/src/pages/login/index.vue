<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { loginFormLift } from '../../utils/login-layout.js'
import BrandLockup from '../../components/BrandLockup.vue'
import { createSliderCaptcha, sendCode, smsLogin, submitRiskSignals, verifySliderCaptcha } from '../../api/index.js'
import { errorMessage, isValidGhanaPhone, normalizeGhanaPhone } from '../../utils/app.js'
import { getAppChannel, getPlatform, getStorage, setStorage } from '../../utils/platform.js'
import { collectRiskSignals } from '../../utils/risk.js'
import { canVerifySlider } from '../../utils/captcha.js'

const formLift = ref(0)

/**
 * 窗口随键盘缩小时仅移动表单，品牌区不参与位移。
 * :param event: UniApp 窗口尺寸事件
 * :return: 无
 */
async function resizeLoginForm(event) {
  await nextTick()
  const height = event?.size?.windowHeight || (typeof window !== 'undefined' ? (window.visualViewport?.height || window.innerHeight) : 0)
  if (!height) return
  const applyBounds = (rect) => {
    if (rect) formLift.value = loginFormLift(rect.bottom, height, formLift.value)
  }
  if (typeof uni.createSelectorQuery === 'function') {
    uni.createSelectorQuery().select('.sign-in-button').boundingClientRect(applyBounds).exec()
  } else if (typeof document !== 'undefined') {
    applyBounds(document.querySelector('.sign-in-button')?.getBoundingClientRect())
  }
}

onMounted(() => {
  if (typeof uni.onWindowResize === 'function') uni.onWindowResize(resizeLoginForm)
  else if (typeof window !== 'undefined') window.visualViewport?.addEventListener('resize', resizeLoginForm)
})
onBeforeUnmount(() => {
  if (typeof uni.offWindowResize === 'function') uni.offWindowResize(resizeLoginForm)
  else if (typeof window !== 'undefined') window.visualViewport?.removeEventListener('resize', resizeLoginForm)
})

const phone = ref('')
const smsCode = ref('')
const codeInputRef = ref(null)
const consent = ref(false)
const smsConsent = ref(false)
const busy = ref(false)
const captchaBusy = ref(false)
const captchaVisible = ref(false)
const captcha = ref(null)
const sliderValue = ref(0)
const sliderDragging = ref(false)
const sliderRef = ref(null)
const sliderTrackWidth = ref(0)
let sliderStartX = 0
let sliderStartValue = 0
let sliderPointerId = null
let sliderMoveFrame = null
let sliderPendingX = null
const scheduleFrame = (callback) => typeof requestAnimationFrame === 'function' ? requestAnimationFrame(callback) : setTimeout(callback, 16)
const cancelFrame = (frame) => typeof cancelAnimationFrame === 'function' ? cancelAnimationFrame(frame) : clearTimeout(frame)
const cooldown = ref(0)
let timer = null
let sliderStartedAt = 0
let captchaVerificationSubmitted = false

const normalizedPhone = computed(() => normalizeGhanaPhone(phone.value))
const phoneHintDigits = computed(() => Array.from({ length: 9 }, (_, index) => ({ value: phone.value[index] || '0' })))
function onPhoneInput(event) { phone.value = String(event.detail?.value ?? event.target?.value ?? '').replace(/\D/g, '').slice(0, 9) }
function onSmsInput(event) { smsCode.value = String(event.detail?.value ?? event.target?.value ?? '').replace(/\D/g, '').slice(0, 6) }
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
    await nextTick()
    measureSlider()
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
    // 验证成功后直接回到验证码输入框，不再弹出阻塞式提示框。
    await nextTick()
    codeInputRef.value?.focus?.()
  } catch (error) { sliderValue.value = 0; captchaVerificationSubmitted = false; notify(errorMessage(error, 'Security check failed. Please retry.')) }
  finally { captchaBusy.value = false }
}

function touchX(event) {
  const point = event?.touches?.[0] || event?.changedTouches?.[0] || event
  return Number(point?.clientX ?? point?.pageX ?? point?.screenX ?? 0)
}
function sliderThumbWidth() { return typeof uni.upx2px === 'function' ? uni.upx2px(92) : 46 }
function measureSlider() {
  const rect = sliderRef.value?.getBoundingClientRect?.()
  if (rect?.width) {
    sliderTrackWidth.value = rect.width
    return
  }
  if (typeof uni.createSelectorQuery === 'function') {
    uni.createSelectorQuery().select('.captcha-slider').boundingClientRect((result) => {
      if (result?.width) sliderTrackWidth.value = result.width
    }).exec()
  }
}
function sliderUsableWidth() {
  const systemInfo = typeof uni.getSystemInfoSync === 'function' ? uni.getSystemInfoSync() : {}
  const trackWidth = sliderTrackWidth.value || Math.max((systemInfo.windowWidth || 390) - 96, 220)
  return Math.max(trackWidth - sliderThumbWidth(), 1)
}
const sliderThumbLeft = computed(() => sliderTrackWidth.value ? `${(sliderValue.value / 100) * sliderUsableWidth()}px` : `${sliderValue.value}%`)
function startSlider(event) {
  event?.preventDefault?.()
  if (captchaBusy.value) return
  sliderDragging.value = true
  sliderStartX = touchX(event)
  sliderStartValue = sliderValue.value
  sliderPointerId = event?.pointerId ?? null
  const target = event?.currentTarget
  if (sliderPointerId !== null) target?.setPointerCapture?.(sliderPointerId)
}
function moveSlider(event) {
  if (!sliderDragging.value || (sliderPointerId !== null && event?.pointerId !== sliderPointerId)) return
  event?.preventDefault?.()
  sliderPendingX = touchX(event)
  if (sliderMoveFrame !== null) return
  // 触摸事件频率高于渲染频率时只在下一帧提交一次，避免 Android WebView/iOS WKWebView 掉帧。
  sliderMoveFrame = scheduleFrame(() => {
    sliderMoveFrame = null
    if (!sliderDragging.value || sliderPendingX === null) return
    sliderValue.value = Math.min(100, Math.max(0, sliderStartValue + ((sliderPendingX - sliderStartX) / sliderUsableWidth()) * 100))
    sliderPendingX = null
  })
}
function endSlider(event) {
  if (sliderPointerId !== null && event?.pointerId !== sliderPointerId) return
  if (sliderMoveFrame !== null) {
    cancelFrame(sliderMoveFrame)
    sliderMoveFrame = null
  }
  if (sliderPendingX !== null) {
    sliderValue.value = Math.min(100, Math.max(0, sliderStartValue + ((sliderPendingX - sliderStartX) / sliderUsableWidth()) * 100))
    sliderPendingX = null
  }
  sliderDragging.value = false
  const target = event?.currentTarget
  if (sliderPointerId !== null) target?.releasePointerCapture?.(sliderPointerId)
  sliderPointerId = null
  if (sliderValue.value >= 98) verifyCaptcha({ detail: { value: 100 } })
}
function pointerSlider(event) { startSlider(event) }
function movePointerSlider(event) { moveSlider(event) }
function endPointerSlider(event) { endSlider(event) }

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
  sliderDragging.value = false
  sliderPointerId = null
  sliderPendingX = null
  if (sliderMoveFrame !== null) cancelFrame(sliderMoveFrame)
  sliderMoveFrame = null
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
    // 输入控件在部分 H5/WebView 中可能保留空格或非数字字符，提交前统一清洗，避免后端 Pydantic 直接返回 422。
    const loginCode = String(smsCode.value || '').replace(/\D/g, '').slice(0, 6)
    const result = await smsLogin({ phone: normalizedPhone.value, sms_code: loginCode })
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
    <view class="login-page__hero"><BrandLockup /><text class="login-page__headline">Get the money you need, faster.</text><text class="login-page__intro">Apply in minutes and move forward with confidence.</text></view>
    <view class="login-form" :style="{ transform: `translateY(-${formLift}px)` }">
    <view class="gc-card login-card">
      <view class="phone-wrap"><text class="phone-prefix">🇬🇭 +233</text><view class="phone-hint" :class="{ 'has-value': phone.length > 0 }" aria-hidden="true"><text v-for="(digit, index) in phoneHintDigits" :key="index" class="phone-hint__digit">{{ digit.value }}</text></view><input :value="phone" class="gc-field phone-field" type="text" inputmode="numeric" maxlength="9" placeholder="" @input="onPhoneInput" /><text class="phone-count">{{ phone.length }}/9</text></view>
      <view class="code-row"><input ref="codeInputRef" :value="smsCode" class="gc-field code-field" type="text" inputmode="numeric" maxlength="6" placeholder="Enter the 6-digit code" @input="onSmsInput" /><button class="gc-button gc-button--secondary code-button" :disabled="!canRequest || captchaBusy" @click="openCaptcha">{{ cooldown > 0 ? `${cooldown}s` : captchaBusy ? 'Checking…' : 'Send code' }}</button></view>
    </view>
    <view class="gc-card agreement-card">
      <label class="consent-row consent-row--first" @click="consent = !consent"><view :class="['consent-check', { checked: consent }]">{{ consent ? '✓' : '' }}</view><text>I agree to GalaCredit's <text class="gc-link" @click.stop="openAgreement">User Agreement</text>, <text class="gc-link" @click.stop="openAgreement">Privacy Policy</text> and <text class="gc-link" @click.stop="openAgreement">Personal Data Authorization</text>.</text></label>
      <label v-if="getPlatform() === 'android' && getAppChannel() === 'internal'" class="consent-row consent-row--optional"><checkbox :checked="smsConsent" color="#ea9518" @click="smsConsent = !smsConsent" /><text>I allow an optional 90-day SMS risk review. Only messages matching the published keywords are uploaded.</text></label>
      <text class="gc-safe-note">Sensitive device permissions are requested only when needed for risk review.</text>
    </view>
    <button class="gc-button sign-in-button" :disabled="!canSignIn" :loading="busy" @click="signIn">{{ busy ? 'Signing in…' : 'Sign In' }}</button>
    </view>
    <view v-if="captchaVisible" class="captcha-mask" @touchmove.stop.prevent @wheel.stop.prevent><view class="captcha-modal gc-card"><text class="gc-section-title">Complete security check</text><text class="captcha-copy">Slide all the way to confirm you are human.</text><view ref="sliderRef" class="captcha-slider" :class="{ 'is-dragging': sliderDragging }" role="slider" aria-label="Slide to verify" :aria-valuenow="Math.round(sliderValue)" aria-valuemin="0" aria-valuemax="100" @touchstart.stop.prevent="startSlider" @touchmove.stop.prevent="moveSlider" @touchend.stop.prevent="endSlider" @touchcancel.stop.prevent="endSlider" @pointerdown.stop.prevent="pointerSlider" @pointermove.stop.prevent="movePointerSlider" @pointerup.stop.prevent="endPointerSlider" @pointercancel.stop.prevent="endPointerSlider"><view class="captcha-slider__track" /><view class="captcha-slider__fill" :style="{ width: `${sliderValue}%` }" /><view class="captcha-slider__thumb" :style="{ left: sliderThumbLeft }">›</view><text class="captcha-slider__label">Slide to verify</text></view><button class="captcha-cancel gc-button gc-button--ghost" :disabled="captchaBusy" @click="closeCaptcha">Cancel</button></view></view>
  </view>
</template>

<style scoped>
.login-page { display:flex; flex-direction:column; width:100%; max-width:800rpx; min-height:100vh; margin:0 auto; padding:calc(24px + env(safe-area-inset-top)) 20px calc(28px + env(safe-area-inset-bottom)); background:radial-gradient(circle at top left,rgba(234,149,24,.16),transparent 28%),radial-gradient(circle at top right,rgba(242,165,61,.14),transparent 30%),linear-gradient(180deg,#fffaf2 0%,#f6f8fb 56%,#f6f8fb 100%); }
.login-page__hero { margin-top:48rpx; padding:10px 2px 14px; }
.login-page__hero :deep(.gc-brand) { gap:32rpx; }
.login-page__hero :deep(.gc-brand__logo) { width:126rpx; height:126rpx; border-radius:38rpx; }
.login-page__hero :deep(.gc-brand__logo-card) { inset:20rpx; }
.login-page__hero :deep(.gc-brand__name) { font-size:84rpx; letter-spacing:-2rpx; }
.login-page__hero :deep(.gc-brand__tagline) { margin-top:8rpx; font-size:26rpx; }
.login-page__hero :deep(.gc-brand > view:last-child) { position:relative; }
.login-page__hero :deep(.gc-brand > view:last-child)::after { content:''; display:block; width:64rpx; height:4rpx; margin-top:10rpx; border-radius:999rpx; background:linear-gradient(90deg,#f2a53d 0%,rgba(200,111,12,.72) 100%); }
.login-page__headline,.login-page__intro { display:none; }
.login-card { margin-top:24rpx; padding:0; border:1rpx solid rgba(255,255,255,.28); border-radius:28rpx; background:rgba(247,249,252,.94); box-shadow:0 10px 22px rgba(23,32,51,.08); overflow:hidden; }
.agreement-card { margin-top:16px; padding:14px 14px 16px; border-radius:18px; background:rgba(255,255,255,.62); border:1rpx solid rgba(255,255,255,.68); box-shadow:0 10px 24px rgba(28,71,142,.06); }
.phone-wrap { position:relative; display:flex; align-items:center; min-height:64px; }
.phone-prefix { position:absolute; z-index:1; left:24rpx; top:0; height:64px; display:flex; align-items:center; font-size:25rpx; font-weight:650; }
.phone-field { position:relative; z-index:2; height:64px; min-height:64px; padding-left:178rpx; margin-top:0; border:0; border-radius:0; background:transparent; font-family:monospace; letter-spacing:0; color:#23344f; -webkit-text-fill-color:#23344f; caret-color:#23344f; }
.phone-field:focus { background:transparent; box-shadow:0 0 0 2rpx rgba(234,149,24,.14); }
.phone-count { position:absolute; z-index:3; right:20rpx; top:0; height:64px; display:flex; align-items:center; color:#7a8ba1; font-size:21rpx; pointer-events:none; }
.phone-hint { position:absolute; z-index:1; left:178rpx; top:0; height:64px; display:flex; align-items:center; pointer-events:none; color:rgba(116,132,151,.42); font-size:25rpx; font-family:monospace; letter-spacing:0; transition:opacity .12s ease; }
.phone-hint.has-value { opacity:0; }
.phone-hint__digit { width:1ch; text-align:center; }
.code-row { display:flex; gap:8px; align-items:center; height:64px; padding:0 14px; }
.code-field { flex:1; height:64px; min-height:64px; margin-top:0; padding:0; border:0; border-radius:0; background:transparent; }
.code-button { width:88px; height:32px; min-height:32px; margin-top:0; padding:0 4px; border:1px solid rgba(234,149,24,.44); border-radius:10px; color:var(--gc-brand-deep); background:rgba(255,244,228,.86); font-size:12px; white-space:nowrap; }
.consent-row { display:flex; gap:8px; align-items:flex-start; margin-top:10px; color:#30445f; font-size:12px; line-height:1.5; }
.consent-row--first { margin-top:0; }
.consent-check { flex:none; width:34rpx; height:34rpx; border:2rpx solid #c8cdd5; border-radius:50%; color:#fff; text-align:center; font-size:25rpx; line-height:30rpx; }
.consent-check.checked { border-color:var(--gc-brand); background:var(--gc-brand); }
.login-page .gc-safe-note { display:block; margin-top:10px; padding:0; border-radius:0; color:#6a7c92; background:transparent; font-size:12px; line-height:1.55; }
.sign-in-button { margin-top:18px; min-height:50px; border-radius:25px; background:linear-gradient(135deg,#f2a53d 0%,#d9790d 100%); font-size:16px; font-weight:800; }
.login-page__footer { margin-top:auto; padding:48rpx 0 12rpx; text-align:center; color:#9aa4b3; font-size:21rpx; }
.captcha-mask { position:fixed; z-index:20; inset:0; display:flex; align-items:flex-start; justify-content:center; padding:22vh 24rpx 24rpx; background:rgba(19,26,39,.52); touch-action:none; overscroll-behavior:contain; }
.captcha-modal { width:100%; max-width:620rpx; padding:34rpx; margin:0; }
.captcha-copy { display:block; color:var(--gc-muted); font-size:24rpx; }
.captcha-slider { position:relative; height:92rpx; margin:34rpx 0 20rpx; overflow:hidden; border-radius:46rpx; touch-action:none; user-select:none; -webkit-user-select:none; cursor:grab; }
.captcha-slider:active { cursor:grabbing; }
.captcha-slider__track { position:absolute; inset:20rpx 0; border-radius:26rpx; background:#f1e9dc; }
.captcha-slider__fill { position:absolute; left:0; top:20rpx; bottom:20rpx; border-radius:26rpx; background:#f7c477; }
.captcha-slider__thumb { position:absolute; top:0; width:92rpx; height:92rpx; border-radius:50%; color:#fff; background:#ea9518; text-align:center; font-size:64rpx; line-height:82rpx; box-shadow:0 6rpx 18rpx rgba(201,111,12,.28); transition:left .08s linear; will-change:left; }
.captcha-slider.is-dragging .captcha-slider__thumb { transition:none; }
.captcha-slider__label { position:absolute; left:112rpx; right:24rpx; color:#9b774a; text-align:center; font-size:24rpx; line-height:92rpx; pointer-events:none; }
.captcha-slider.is-dragging .captcha-slider__label { opacity:.2; }
.captcha-cancel { position:relative; display:flex; clear:both; width:100%; margin:18rpx 0 0; }
/* 表单作为整体移动，保留卡片间距；品牌区使用稳定尺寸，不随键盘窗口变高或变矮。 */
.login-form { display:flex; flex-direction:column; flex-shrink:0; }
</style>
