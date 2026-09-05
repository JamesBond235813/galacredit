<template>
  <div class="login-container" ref="loginContainerRef">
    <div class="login-stage" ref="loginStageRef">
      <header class="brand-header">
        <div class="brand-mark">
          <img src="../assets/logo.svg" class="brand-logo" alt="GalaCredit logo" />
        </div>
        <div class="brand-copy">
          <h1 class="brand-title">GalaCredit</h1>
          <p class="brand-slogan">Credit when it matters</p>
        </div>
      </header>

      <section class="login-main">
        <van-form class="login-form" @submit="onSubmit">
          <van-cell-group inset class="login-fields">
            <div class="phone-field-wrapper">
              <div class="phone-zero-placeholder" aria-hidden="true">
                <span
                  v-for="index in GHANA_PHONE_DIGITS"
                  :key="index"
                  :class="{ 'phone-digit-entered': index <= phone.length }"
                >{{ phone[index - 1] || '0' }}</span>
              </div>
              <van-field
                v-model="phone"
                name="phone"
                type="tel"
                :maxlength="GHANA_PHONE_DIGITS"
                :formatter="normalizePhone"
                clearable
                class="login-field phone-field"
              >
                <template #left-icon>
                  <span class="ghana-phone-prefix" aria-label="Ghana country code">
                    <span class="ghana-flag" aria-hidden="true">🇬🇭</span>
                    <span>+233</span>
                  </span>
                </template>
                <template #right-icon>
                  <span class="phone-counter" aria-label="Mobile number digit count">{{ phone.length }}/9</span>
                </template>
              </van-field>
            </div>

            <van-field
              v-model="smsCode"
              name="smsCode"
              type="digit"
              maxlength="6"
              placeholder="Enter the 6-digit code"
              clearable
              class="login-field"
            >
              <template #button>
                <van-button
                  size="small"
                  type="primary"
                  plain
                  class="sms-send-btn"
                  :disabled="smsSending || cooldownSeconds > 0"
                  @click.prevent="openCaptchaDialog"
                >
                  {{ smsButtonText }}
                </van-button>
              </template>
            </van-field>
          </van-cell-group>

          <section class="agreement-panel">
            <van-checkbox v-model="consentAccepted" icon-size="16px" class="agreement-check">
              <span class="consent-text">
                I agree to GalaCredit's
                <a href="/agreement" @click.prevent="openLegalPage('/agreement')">User Agreement</a>,
                <a href="/personal-info-authorization" @click.prevent="openLegalPage('/personal-info-authorization')">Privacy Policy</a>
                and
                <a href="/personal-info-authorization" @click.prevent="openLegalPage('/personal-info-authorization')">Personal Data Authorization</a>.
              </span>
            </van-checkbox>
            <p class="agreement-note">
              Sensitive device permissions are requested only when needed for risk review.
            </p>
            <van-checkbox v-if="smsReviewAvailable" v-model="smsConsent" icon-size="16px" class="agreement-check sms-consent-check">
              <span class="consent-text">
                I allow an optional 90-day SMS risk review. Only messages matching the published keywords are uploaded after Android permission.
              </span>
            </van-checkbox>
          </section>

          <div class="submit-wrap">
            <van-button round block type="primary" native-type="submit" :loading="loading" class="submit-btn">
              Sign In
            </van-button>
          </div>
        </van-form>
      </section>
    </div>

    <div v-if="policyVisible" class="popup-layer" @click.self="closePolicyDialog">
      <div class="popup-card policy-popup">
        <div class="popup-title">{{ policyTitle }}</div>
        <div v-if="policyLoading" class="policy-loading">Loading...</div>
        <div v-else class="policy-content">
          <p v-for="(item, index) in policyParagraphs" :key="index">{{ item }}</p>
        </div>
        <div class="captcha-actions">
          <button type="button" class="text-button" @click="closePolicyDialog">Close</button>
        </div>
      </div>
    </div>

    <div v-if="captchaVisible" class="popup-layer" @click.self="captchaVisible = false">
      <div class="popup-card captcha-popup">
        <div class="popup-title">Complete the security check</div>
        <div class="captcha-box" ref="captchaContainerRef">
          <div
            class="simple-slider"
            :class="{ 'simple-slider--done': sliderVerified }"
            :style="{ width: `${captcha.width}px` }"
          >
            <div class="simple-slider-fill" :style="{ width: `${sliderProgressWidth}px` }"></div>
            <div class="simple-slider-text">{{ sliderHintText }}</div>
            <button
              ref="sliderPieceRef"
              type="button"
              class="simple-slider-thumb"
              :style="{ transform: `translateX(${sliderOffsetX}px)` }"
              :disabled="captchaVerifying"
              aria-label="Slide right to verify"
              @mousedown.prevent="onSliderDragStart"
              @touchstart.prevent="onSliderDragStart"
            >
              →
            </button>
          </div>
          <div class="captcha-actions">
            <button type="button" class="text-button" @click="refreshCaptcha">Refresh</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { createSliderCaptcha, sendCode, smsLogin, submitRiskSignals, verifySliderCaptcha } from '../api';
import { clearEntryChannel, getEntryInviteCode } from '../utils/channel';
import { GHANA_PHONE_DIGITS, isValidPhone, normalizePhone, toGhanaPhone } from '../utils/passwordAuth';
import { getSmsButtonText, isValidSmsCode, normalizeSmsCode } from '../utils/smsLogin';
import { buildRiskSignalPayload } from '../utils/riskSignals';

const router = useRouter();
const phone = ref('');
const smsCode = ref('');
const loading = ref(false);
const smsSending = ref(false);
const cooldownSeconds = ref(0);
const entryInviteCode = ref(getEntryInviteCode());
const consentAccepted = ref(false);
const smsConsent = ref(false);
const pendingRiskPayload = ref(null);
const policyVisible = ref(false);
const policyLoading = ref(false);
const policyTitle = ref('');
const policyContent = ref('');
const captchaVisible = ref(false);
const captchaVerifying = ref(false);
const captchaContainerRef = ref(null);
const loginContainerRef = ref(null);
const loginStageRef = ref(null);
const sliderPieceRef = ref(null);
const sliderOffsetX = ref(0);
const sliderMoveStartedAt = ref(0);
const sliderMoveElapsedMs = ref(0);
const sliderVerified = ref(false);
const captcha = ref({
  captchaId: '',
  width: 0,
  height: 160,
  blockSize: 44,
  blockY: 0,
  minElapsedMs: 1200,
  backgroundImage: '',
  sliderImage: ''
});

let cooldownTimer = null;
let keyboardResizeHandler = null;
let keyboardFocusHandler = null;
let keyboardBlurHandler = null;
const dragging = ref(false);
const dragStartClientX = ref(0);
const dragStartOffsetX = ref(0);

const smsReviewAvailable = computed(() => {
  if (typeof window === 'undefined') return false;
  try {
    const info = window.GalaCreditNativeInfo || {};
    const channel = info.app_channel || window.GalaCreditRisk?.getAppChannel?.() || 'play';
    return (info.platform === 'android' || typeof window.GalaCreditRisk?.startSmsReview === 'function') && channel === 'internal';
  } catch (error) {
    return false;
  }
});

const smsButtonText = computed(() => getSmsButtonText(smsSending.value, cooldownSeconds.value));
const apiPhone = computed(() => toGhanaPhone(phone.value));
const maxSliderOffset = computed(() => Math.max(captcha.value.width - captcha.value.blockSize, 0));
const sliderProgressWidth = computed(() => Math.min(sliderOffsetX.value + captcha.value.blockSize, captcha.value.width));
const sliderHintText = computed(() => {
  if (captchaVerifying.value) {
    return 'Verifying...';
  }
  return sliderVerified.value ? 'Verified' : 'Slide right to send the code';
});

const startCooldown = (seconds) => {
  if (cooldownTimer) {
    window.clearInterval(cooldownTimer);
  }
  cooldownSeconds.value = Number(seconds || 0);
  cooldownTimer = window.setInterval(() => {
    cooldownSeconds.value = Math.max(cooldownSeconds.value - 1, 0);
    if (cooldownSeconds.value <= 0 && cooldownTimer) {
      window.clearInterval(cooldownTimer);
      cooldownTimer = null;
    }
  }, 1000);
};

const getCaptchaRequestWidth = () => {
  const containerWidth = Number(loginStageRef.value?.clientWidth || document.documentElement.clientWidth || 360);
  return Math.min(Math.max(Math.floor(containerWidth), 280), 420);
};

const refreshCaptcha = async () => {
  if (!isValidPhone(phone.value)) {
    showToast('Enter a valid mobile number');
    return;
  }
  const payload = await createSliderCaptcha({ phone: apiPhone.value, width: getCaptchaRequestWidth() });
  captcha.value = {
    captchaId: payload.captcha_id,
    width: payload.width,
    height: payload.height,
    blockSize: payload.block_size,
    blockY: payload.block_y,
    minElapsedMs: payload.min_elapsed_ms || 1200,
    backgroundImage: payload.background_image,
    sliderImage: payload.slider_image
  };
  sliderOffsetX.value = 0;
  sliderMoveStartedAt.value = 0;
  sliderMoveElapsedMs.value = 0;
  sliderVerified.value = false;
};

const openCaptchaDialog = async () => {
  if (!isValidPhone(phone.value)) {
    showToast('Enter a valid mobile number');
    return;
  }
  captchaVisible.value = true;
  await refreshCaptcha();
};

const onSliderInput = () => {
  const now = Date.now();
  if (!sliderMoveStartedAt.value) {
    sliderMoveStartedAt.value = now;
  }
  sliderMoveElapsedMs.value = now - sliderMoveStartedAt.value;
};

const verifyCaptchaAndSendSms = async () => {
  captchaVerifying.value = true;
  try {
    const verifyRes = await verifySliderCaptcha({
      phone: apiPhone.value,
      captcha_id: captcha.value.captchaId,
      offset_x: sliderOffsetX.value,
      elapsed_ms: Math.max(sliderMoveElapsedMs.value, captcha.value.minElapsedMs || 0)
    });
    smsSending.value = true;
    const smsRes = await sendCode({
      phone: apiPhone.value,
      captcha_ticket: verifyRes.captcha_ticket
    });
    startCooldown(smsRes.cooldown_seconds || 60);
    showToast('Verification code sent');
    captchaVisible.value = false;
  } catch (error) {
    sliderOffsetX.value = 0;
    sliderMoveStartedAt.value = 0;
    sliderMoveElapsedMs.value = 0;
    sliderVerified.value = false;
    const detail = String(error?.response?.data?.detail || '');
    if (detail.includes('expired') || detail.includes('invalid') || detail.includes('timeout') || detail.includes('stale')) {
      await refreshCaptcha();
    }
  } finally {
    smsSending.value = false;
    captchaVerifying.value = false;
  }
};

const onSliderRelease = async () => {
  if (!captchaVisible.value || captchaVerifying.value) {
    return;
  }
  await verifyCaptchaAndSendSms();
};

const onDragMove = (event) => {
  if (!dragging.value) {
    return;
  }
  const clientX = Number(event.touches?.[0]?.clientX ?? event.clientX ?? 0);
  const delta = clientX - dragStartClientX.value;
  sliderOffsetX.value = Math.min(Math.max(dragStartOffsetX.value + delta, 0), maxSliderOffset.value);
  onSliderInput();
};

const onDragEnd = async () => {
  if (!dragging.value) {
    return;
  }
  dragging.value = false;
  window.removeEventListener('mousemove', onDragMove);
  window.removeEventListener('mouseup', onDragEnd);
  window.removeEventListener('touchmove', onDragMove);
  window.removeEventListener('touchend', onDragEnd);
  if (sliderOffsetX.value >= maxSliderOffset.value - 2) {
    sliderOffsetX.value = maxSliderOffset.value;
    sliderVerified.value = true;
    await onSliderRelease();
    return;
  }
  sliderOffsetX.value = 0;
  sliderMoveStartedAt.value = 0;
  sliderMoveElapsedMs.value = 0;
};

const onSliderDragStart = (event) => {
  if (captchaVerifying.value) {
    return;
  }
  const clientX = Number(event.touches?.[0]?.clientX ?? event.clientX ?? 0);
  dragging.value = true;
  dragStartClientX.value = clientX;
  dragStartOffsetX.value = sliderOffsetX.value;
  onSliderInput();
  window.addEventListener('mousemove', onDragMove);
  window.addEventListener('mouseup', onDragEnd);
  window.addEventListener('touchmove', onDragMove, { passive: false });
  window.addEventListener('touchend', onDragEnd);
};

const policyParagraphs = computed(() =>
  String(policyContent.value || '')
    .split(/\n\s*\n/g)
    .map((item) => item.replace(/\n/g, ' ').trim())
    .filter(Boolean)
);

const closePolicyDialog = () => {
  policyVisible.value = false;
  policyTitle.value = '';
  policyContent.value = '';
  policyLoading.value = false;
};

const openLegalPage = async (path) => {
  const docMap = {
    '/agreement': {
      title: 'User Agreement',
      url: '/user-agreement.txt'
    },
    '/personal-info-authorization': {
      title: 'Personal Data Authorization',
      url: '/personal-info-authorization.txt'
    }
  };
  const doc = docMap[path];
  if (!doc) {
    return;
  }
  policyVisible.value = true;
  policyLoading.value = true;
  policyTitle.value = doc.title;
  policyContent.value = '';
  try {
    const resp = await fetch(doc.url, { cache: 'no-cache' });
    policyContent.value = await resp.text();
  } catch (error) {
    policyContent.value = `${doc.title} could not be loaded. Please try again later.`;
  } finally {
    policyLoading.value = false;
  }
};

const submitRiskSignal = async () => {
  if (!pendingRiskPayload.value) {
    return;
  }
  await submitRiskSignals({
    phone: apiPhone.value,
    accepted_user_agreement: consentAccepted.value,
    accepted_personal_authorization: consentAccepted.value,
    accepted_sensitive_collection: consentAccepted.value,
    device_payload: pendingRiskPayload.value
  });
};

const performLogin = async () => {
  smsCode.value = normalizeSmsCode(String(smsCode.value || ''));
  loading.value = true;
  try {
    const res = await smsLogin({
      phone: apiPhone.value,
      sms_code: smsCode.value,
      invite_code: entryInviteCode.value || undefined
    });
    localStorage.setItem('token', res.access_token);
    if (res.refresh_token) {
      localStorage.setItem('refresh_token', res.refresh_token);
    }
    if (pendingRiskPayload.value) {
      try {
        await submitRiskSignal();
      } catch (error) {
        showToast('Signed in, but risk signal capture was not completed');
      }
    }
    sessionStorage.removeItem('h5_location_authorized');
    sessionStorage.removeItem('h5_location_attempted');
    clearEntryChannel();
    showToast('Signed in successfully');
    router.replace('/home');
  } catch (error) {
    if (error.response?.data?.code === 404) {
      clearEntryChannel();
      entryInviteCode.value = '';
    }
  } finally {
    loading.value = false;
    pendingRiskPayload.value = null;
  }
};

const onSubmit = async () => {
  if (!isValidPhone(phone.value)) {
    showToast('Enter a valid mobile number');
    return;
  }
  if (!consentAccepted.value) {
    showToast('Please accept the agreement and authorization');
    return;
  }
  if (!isValidSmsCode(normalizeSmsCode(String(smsCode.value || '')))) {
    showToast('Enter the 6-digit verification code');
    return;
  }
  try {
    pendingRiskPayload.value = await buildRiskSignalPayload({
      phone: apiPhone.value,
      consentSms: smsReviewAvailable.value && smsConsent.value,
      consentAppList: false,
      consentDeviceFingerprint: true
    });
  } catch (error) {
    pendingRiskPayload.value = null;
  }
  await performLogin();
};

const updateKeyboardOffset = async (target = document.activeElement) => {
  await nextTick();
  const viewport = window.visualViewport;
  const container = loginContainerRef.value;
  const stage = loginStageRef.value;
  if (!container || !stage || !viewport || !target || !target.getBoundingClientRect) {
    return;
  }

  const keyboardTop = viewport.height + viewport.offsetTop;
  const rect = target.getBoundingClientRect();
  const overlap = Math.max(rect.bottom + 18 - keyboardTop, 0);
  stage.style.setProperty('--keyboard-offset', `${overlap}px`);
  container.style.setProperty('--keyboard-space', `${Math.max(keyboardTop - window.innerHeight, 0)}px`);
};

const resetKeyboardOffset = () => {
  if (loginStageRef.value) {
    loginStageRef.value.style.setProperty('--keyboard-offset', '0px');
  }
};

onMounted(() => {
  const viewport = window.visualViewport;
  keyboardResizeHandler = () => updateKeyboardOffset();
  keyboardFocusHandler = (event) => updateKeyboardOffset(event.target);
  keyboardBlurHandler = () => window.setTimeout(resetKeyboardOffset, 120);
  viewport?.addEventListener('resize', keyboardResizeHandler);
  viewport?.addEventListener('scroll', keyboardResizeHandler);
  loginContainerRef.value?.addEventListener('focusin', keyboardFocusHandler);
  loginContainerRef.value?.addEventListener('focusout', keyboardBlurHandler);
});

onBeforeUnmount(() => {
  if (cooldownTimer) {
    window.clearInterval(cooldownTimer);
    cooldownTimer = null;
  }
  window.removeEventListener('mousemove', onDragMove);
  window.removeEventListener('mouseup', onDragEnd);
  window.removeEventListener('touchmove', onDragMove);
  window.removeEventListener('touchend', onDragEnd);
  const viewport = window.visualViewport;
  viewport?.removeEventListener('resize', keyboardResizeHandler);
  viewport?.removeEventListener('scroll', keyboardResizeHandler);
  loginContainerRef.value?.removeEventListener('focusin', keyboardFocusHandler);
  loginContainerRef.value?.removeEventListener('focusout', keyboardBlurHandler);
});
</script>

<style scoped>
.login-container {
  min-height: 100dvh;
  display: flex;
  justify-content: center;
  position: relative;
  background:
    radial-gradient(circle at top left, rgba(234, 149, 24, 0.16), transparent 28%),
    radial-gradient(circle at top right, rgba(242, 165, 61, 0.14), transparent 30%),
    linear-gradient(180deg, #fffaf2 0%, #f6f8fb 56%, #f6f8fb 100%);
  padding: 18px 20px calc(28px + var(--keyboard-space, 0px));
  overflow-y: auto;
  overscroll-behavior: contain;
}

.login-stage {
  width: 100%;
  max-width: 400px;
  min-height: calc(100dvh - 46px);
  display: flex;
  flex-direction: column;
}

.brand-header {
  display: flex;
  align-items: center;
  gap: 18px;
  margin: clamp(22px, 7vh, 58px) 0 0;
  padding: 10px 2px 14px;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  border-radius: 22px;
  background: rgba(255, 250, 242, 0.46);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: 0 10px 26px rgba(23, 32, 51, 0.04);
  backdrop-filter: blur(10px);
  flex-shrink: 0;
}

.brand-logo {
  width: 62px;
  height: 62px;
}

.brand-copy {
  display: grid;
  gap: 5px;
  min-width: 0;
  position: relative;
  padding: 2px 0 0;
}

.brand-copy::after {
  content: '';
  width: 64px;
  height: 3px;
  margin-top: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, #f2a53d 0%, rgba(200, 111, 12, 0.72) 100%);
  box-shadow: 0 6px 14px rgba(201, 111, 12, 0.12);
}

.brand-title {
  margin: 0;
  color: #0d1b31;
  font-size: clamp(38px, 11vw, 54px);
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -0.06em;
}

.brand-slogan {
  margin: 0;
  color: #5d7694;
  font-size: clamp(13px, 3.4vw, 16px);
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: 0.02em;
}

.login-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: clamp(40px, 8vh, 92px);
  transform: translateY(calc(var(--keyboard-offset, 0px) * -1));
  transition: transform 160ms ease-out;
}

.login-form {
  width: 100%;
}

.login-fields {
  --field-bg-lock: rgba(247, 249, 252, 0.94);
  background: rgba(247, 249, 252, 0.94) !important;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 16px;
  box-shadow: 0 10px 22px rgba(23, 32, 51, 0.08);
  backdrop-filter: blur(8px);
}

.phone-field-wrapper {
  position: relative;
}

.phone-zero-placeholder {
  position: absolute;
  z-index: 1;
  top: 50%;
  left: 102px;
  display: flex;
  transform: translateY(-50%);
  color: rgba(116, 132, 151, 0.42);
  font-size: 16px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  letter-spacing: 0;
  pointer-events: none;
  white-space: pre;
}

.phone-field {
  position: relative;
  z-index: 2;
}

:deep(.phone-field .van-field__control) {
  position: relative;
  z-index: 2;
  background: transparent;
  color: transparent;
  caret-color: #23344f;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  letter-spacing: 0;
  -webkit-text-fill-color: transparent;
}

:deep(.phone-field .van-field__left-icon) {
  display: flex;
  align-items: center;
  align-self: stretch;
  height: auto !important;
}

.ghana-phone-prefix {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 84px;
  color: #23344f;
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}

.phone-digit-entered {
  color: #23344f;
}

.ghana-flag {
  font-size: 18px;
  line-height: 1;
}

.phone-counter {
  min-width: 24px;
  color: #7a8ba1;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  text-align: right;
  white-space: nowrap;
}

.agreement-panel {
  margin-top: 16px;
  padding: 14px 14px 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.68);
  box-shadow: 0 10px 24px rgba(28, 71, 142, 0.06);
  backdrop-filter: blur(10px);
}

.agreement-check {
  align-items: flex-start;
  color: #30445f;
  font-size: 12px;
  line-height: 1.5;
}

.agreement-check :deep(.van-checkbox__label) {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px;
}

.consent-text {
  display: inline;
}

.agreement-check a {
  color: var(--app-primary-deep);
  font-weight: 600;
  text-decoration: none;
}

.agreement-note {
  margin: 10px 0 0;
  color: #6a7c92;
  font-size: 12px;
  line-height: 1.55;
}

.submit-wrap {
  margin: 18px 0 0;
}

.submit-btn {
  height: 50px;
  font-size: 16px;
}

.popup-layer {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 18, 34, 0.2);
  padding: 16px;
}

.popup-card {
  width: 100%;
  max-width: 452px;
  background: rgba(236, 244, 255, 0.98);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 12px 28px rgba(21, 42, 78, 0.18);
}

.popup-title {
  font-size: 15px;
  color: var(--app-primary);
  margin-bottom: 14px;
  font-weight: 700;
}

.policy-popup {
  max-height: min(72dvh, 640px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.policy-loading {
  color: #4d6684;
  font-size: 14px;
}

.policy-content {
  display: grid;
  gap: 10px;
  overflow: auto;
  padding-right: 2px;
}

.policy-content p {
  margin: 0;
  color: #2d4158;
  font-size: 13px;
  line-height: 1.7;
  white-space: normal;
  word-break: break-word;
  text-align: justify;
}

.risk-consent-desc {
  margin: 0 0 14px;
  color: #48617f;
  font-size: 13px;
  line-height: 1.6;
}

.risk-consent-list {
  display: grid;
  gap: 10px;
}

.risk-consent-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  color: #2d4158;
  font-size: 13px;
  line-height: 1.5;
}

.risk-consent-item input {
  margin-top: 2px;
}

.risk-consent-actions,
.captcha-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 14px;
}

.text-button,
.confirm-button {
  border: none;
  background: transparent;
  color: var(--app-primary);
  font-size: 13px;
  padding: 0;
  line-height: 1.4;
  cursor: pointer;
}

.confirm-button {
  color: #ffffff;
  background: var(--app-gradient);
  border-radius: 12px;
  padding: 0 14px;
  min-height: 34px;
}

.captcha-box {
  width: 100%;
  max-width: 420px;
  margin: 0 auto;
}

.simple-slider {
  position: relative;
  max-width: 100%;
  height: 46px;
  border: 1px solid rgba(47, 119, 204, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.78);
  overflow: hidden;
  touch-action: none;
  user-select: none;
}

.simple-slider-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: linear-gradient(90deg, rgba(47, 119, 204, 0.18), rgba(35, 176, 169, 0.28));
  transition: width 0.12s ease;
}

.simple-slider-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4d6684;
  font-size: 14px;
  pointer-events: none;
}

.simple-slider-thumb {
  position: absolute;
  left: 0;
  top: 0;
  width: 46px;
  height: 44px;
  border: none;
  border-right: 1px solid rgba(47, 119, 204, 0.22);
  background: #ffffff;
  color: var(--app-primary);
  font-size: 20px;
  line-height: 1;
  box-shadow: 0 2px 8px rgba(30, 89, 157, 0.12);
  cursor: grab;
  touch-action: none;
}

.simple-slider-thumb:disabled {
  cursor: default;
  opacity: 0.9;
}

.simple-slider--done .simple-slider-fill {
  background: linear-gradient(90deg, rgba(35, 176, 169, 0.3), rgba(47, 119, 204, 0.28));
}

.simple-slider--done .simple-slider-text {
  color: var(--app-primary);
  font-weight: 600;
}

:deep(.login-field) {
  min-height: 64px;
  padding: 0 14px;
  background: transparent !important;
}

:deep(.login-field.van-cell),
:deep(.login-field.van-field) {
  background: transparent !important;
}

:deep(.login-field .van-field__body) {
  min-height: 64px;
  background: transparent !important;
}

:deep(.login-field .van-field__control) {
  min-height: 64px;
  font-size: 16px;
  line-height: 64px;
  background: transparent !important;
}

:deep(.login-field input),
:deep(.login-field textarea),
:deep(.login-field .van-field__control:focus) {
  background: transparent !important;
}

:deep(.login-field input:-webkit-autofill),
:deep(.login-field input:-webkit-autofill:hover),
:deep(.login-field input:-webkit-autofill:focus),
:deep(.login-field textarea:-webkit-autofill),
:deep(.login-field textarea:-webkit-autofill:hover),
:deep(.login-field textarea:-webkit-autofill:focus) {
  -webkit-text-fill-color: #0f1b2d;
  -webkit-box-shadow: 0 0 0 1000px var(--field-bg-lock) inset !important;
  box-shadow: 0 0 0 1000px var(--field-bg-lock) inset !important;
  transition: background-color 99999s ease-out 0s;
}

:deep(.login-field .van-field__control::placeholder) {
  color: #7289a5;
  font-size: 16px;
}

:deep(.sms-send-btn.van-button) {
  border-radius: 10px;
  height: 32px;
  padding: 0 12px;
  font-size: 12px;
}

@media (max-height: 760px) {
  .login-main {
    padding-top: 56px;
  }
}
</style>
