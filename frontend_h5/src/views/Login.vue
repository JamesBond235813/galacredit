<template>
  <div class="login-container" ref="loginContainerRef">
    <div class="login-stage" ref="loginStageRef">
      <div class="logo-box brand-header">
        <img src="../assets/logo.svg" class="brand-logo" alt="GalaCredit logo" />
        <div class="brand-copy">
          <h1 class="brand-title">GalaCredit</h1>
          <p class="brand-slogan">Credit when it matters</p>
        </div>
      </div>

      <section class="login-main">
        <van-form @submit="onSubmit" class="login-form">
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
          <div class="submit-wrap">
            <van-button round block type="primary" native-type="submit" :loading="loading" class="submit-btn">
              Sign In
            </van-button>
          </div>
        </van-form>
      </section>

    </div>

    <div v-if="captchaVisible" class="captcha-layer" @click.self="captchaVisible = false">
      <div class="captcha-popup">
        <div class="captcha-box" ref="captchaContainerRef">
          <div class="captcha-title">Complete the security check</div>
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
            <button type="button" class="captcha-refresh-link" @click="refreshCaptcha">Refresh</button>
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
import { createSliderCaptcha, sendCode, smsLogin, verifySliderCaptcha } from '../api';
import { clearEntryChannel, getEntryInviteCode } from '../utils/channel';
import { GHANA_PHONE_DIGITS, isValidPhone, normalizePhone, toGhanaPhone } from '../utils/passwordAuth';
import { getSmsButtonText, isValidSmsCode, normalizeSmsCode } from '../utils/smsLogin';

const router = useRouter();
const phone = ref('');
const smsCode = ref('');
const loading = ref(false);
const entryInviteCode = ref(getEntryInviteCode());
const smsSending = ref(false);
const cooldownSeconds = ref(0);
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
const dragging = ref(false);
const dragStartClientX = ref(0);
const dragStartOffsetX = ref(0);
let keyboardResizeHandler = null;
let keyboardFocusHandler = null;
let keyboardBlurHandler = null;

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
  const target = Math.floor(containerWidth);
  return Math.min(Math.max(target, 280), 420);
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
    if (detail.includes('expired') || detail.includes('invalid') || detail.includes('\u8fc7\u671f') || detail.includes('\u5931\u6548')) {
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

const onSubmit = async () => {
  if (!isValidPhone(phone.value)) {
    showToast('Enter a valid mobile number');
    return;
  }

  smsCode.value = normalizeSmsCode(String(smsCode.value || ''));
  if (!isValidSmsCode(smsCode.value)) {
    showToast('Enter the 6-digit verification code');
    return;
  }

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
    sessionStorage.removeItem('h5_location_authorized');
    sessionStorage.removeItem('h5_location_attempted');
    clearEntryChannel();
    showToast('Signed in successfully');
    router.replace('/home');
  } catch (error) {
    if (error.response?.data?.detail === '\u6e20\u9053\u94fe\u63a5\u4e0d\u5b58\u5728\u6216\u5df2\u505c\u7528') {
      clearEntryChannel();
      entryInviteCode.value = '';
    }
  } finally {
    loading.value = false;
  }
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
  // Move the form as one unit so the input and submit action keep their alignment.
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
  background: var(--app-gradient);
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
  justify-content: flex-start;
}

.brand-header {
  margin: clamp(28px, 8vh, 72px) 0 0;
  padding: 8px 0;
  transform: translateX(-10px);
}

.login-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: clamp(72px, 13vh, 132px);
  transform: translateY(calc(var(--keyboard-offset, 0px) * -1));
  transition: transform 160ms ease-out;
}

.login-form {
  width: 100%;
}

.login-fields {
  --field-bg-lock: rgba(221, 233, 246, 0.62);
  background: rgba(221, 233, 246, 0.62) !important;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 16px;
  box-shadow: 0 10px 22px rgba(28, 71, 142, 0.08);
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

.submit-wrap {
  margin: 26px 0 0;
}

.captcha-box {
  width: 100%;
  max-width: 420px;
  margin: 0 auto;
}

.captcha-layer {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 18, 34, 0.2);
  padding: 16px;
}

.captcha-popup {
  width: 100%;
  max-width: 452px;
  background: rgba(236, 244, 255, 0.98);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 12px 28px rgba(21, 42, 78, 0.18);
}

.captcha-title {
  font-size: 15px;
  color: var(--app-primary);
  margin-bottom: 14px;
  font-weight: 600;
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
  letter-spacing: 0;
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

.captcha-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.captcha-refresh-link {
  border: none;
  background: transparent;
  color: var(--app-primary);
  font-size: 13px;
  padding: 0;
  line-height: 1.4;
  cursor: pointer;
}

.logo-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

@media (max-height: 760px) {
  .login-main {
    padding-top: 56px;
  }
}

.brand-logo {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
}

.brand-copy {
  text-align: left;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(8, 34, 76, 0.28);
  box-shadow: 0 6px 18px rgba(8, 34, 76, 0.12);
}

.brand-title {
  font-size: 28px;
  color: #ffffff;
  margin: 0;
  font-weight: 700;
  letter-spacing: 2px;
  text-shadow: 0 2px 8px rgba(8, 34, 76, 0.28);
}

.brand-slogan {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.92);
  margin: 8px 0 0;
  letter-spacing: 1px;
}

.van-cell-group--inset {
  margin: 0 !important;
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
</style>
