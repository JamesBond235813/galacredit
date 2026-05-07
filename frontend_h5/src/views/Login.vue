<template>
  <div class="login-container" ref="loginContainerRef">
    <div class="login-stage" ref="loginStageRef">
      <section class="login-main">
        <van-form @submit="onSubmit" class="login-form">
          <van-cell-group inset class="login-fields">
            <van-field
              v-model="phone"
              name="phone"
              type="tel"
              maxlength="11"
              placeholder="请输入手机号"
              :formatter="normalizePhone"
              clearable
              class="login-field"
            />
            <van-field
              v-model="smsCode"
              name="smsCode"
              type="digit"
              maxlength="6"
              placeholder="请输入短信验证码"
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
              登录
            </van-button>
          </div>
        </van-form>
      </section>

      <div class="logo-box brand-footer">
        <img src="../assets/logo.svg" class="brand-logo" alt="小荷包 logo" />
        <div class="brand-copy">
          <h1 class="brand-title">小荷包</h1>
          <p class="brand-slogan">解生活之所急</p>
        </div>
      </div>
    </div>

    <div v-if="captchaVisible" class="captcha-layer" @click.self="captchaVisible = false">
      <div class="captcha-popup">
        <div class="captcha-box" ref="captchaContainerRef">
        <div class="captcha-title">请完成滑块验证</div>
        <div class="captcha-bg-wrap" v-if="captcha.backgroundImage" :style="{ width: `${captcha.width}px`, height: `${captcha.height}px` }">
          <img class="captcha-bg" :src="captcha.backgroundImage" alt="captcha-background" />
          <img
            ref="sliderPieceRef"
            class="captcha-slider-piece"
            :src="captcha.sliderImage"
            alt="captcha-slider"
            :style="{ left: `${sliderOffsetX}px`, top: `${captcha.blockY}px`, width: `${captcha.blockSize}px`, height: `${captcha.blockSize}px` }"
            @mousedown.prevent="onSliderDragStart"
            @touchstart.prevent="onSliderDragStart"
          />
        </div>
        <div class="captcha-actions">
          <button type="button" class="captcha-refresh-link" @click="refreshCaptcha">刷新</button>
        </div>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { createSliderCaptcha, sendCode, smsLogin, verifySliderCaptcha } from '../api';
import { clearEntryChannel, getEntryInviteCode } from '../utils/channel';
import { isValidPhone, normalizePhone } from '../utils/passwordAuth';
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
const captcha = ref({
  captchaId: '',
  width: 0,
  height: 160,
  blockSize: 44,
  blockY: 0,
  backgroundImage: '',
  sliderImage: ''
});
let cooldownTimer = null;
const dragging = ref(false);
const dragStartClientX = ref(0);
const dragStartOffsetX = ref(0);

const smsButtonText = computed(() => getSmsButtonText(smsSending.value, cooldownSeconds.value));

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
    showToast('请输入11位手机号');
    return;
  }
  const payload = await createSliderCaptcha({ phone: phone.value, width: getCaptchaRequestWidth() });
  captcha.value = {
    captchaId: payload.captcha_id,
    width: payload.width,
    height: payload.height,
    blockSize: payload.block_size,
    blockY: payload.block_y,
    backgroundImage: payload.background_image,
    sliderImage: payload.slider_image
  };
  sliderOffsetX.value = 0;
  sliderMoveStartedAt.value = 0;
  sliderMoveElapsedMs.value = 0;
};

const openCaptchaDialog = async () => {
  if (!isValidPhone(phone.value)) {
    showToast('请输入11位手机号');
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
      phone: phone.value,
      captcha_id: captcha.value.captchaId,
      offset_x: sliderOffsetX.value,
      elapsed_ms: sliderMoveElapsedMs.value
    });
    smsSending.value = true;
    const smsRes = await sendCode({
      phone: phone.value,
      captcha_ticket: verifyRes.captcha_ticket
    });
    startCooldown(smsRes.cooldown_seconds || 60);
    showToast('验证码已发送');
    captchaVisible.value = false;
  } catch (error) {
    sliderOffsetX.value = 0;
    sliderMoveStartedAt.value = 0;
    sliderMoveElapsedMs.value = 0;
    const detail = String(error?.response?.data?.detail || '');
    if (detail.includes('过期') || detail.includes('失效')) {
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
  const maxOffset = Math.max(captcha.value.width - captcha.value.blockSize, 0);
  sliderOffsetX.value = Math.min(Math.max(dragStartOffsetX.value + delta, 0), maxOffset);
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
  await onSliderRelease();
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
    showToast('请输入11位手机号');
    return;
  }

  smsCode.value = normalizeSmsCode(String(smsCode.value || ''));
  if (!isValidSmsCode(smsCode.value)) {
    showToast('请输入6位短信验证码');
    return;
  }

  loading.value = true;
  try {
    const res = await smsLogin({
      phone: phone.value,
      sms_code: smsCode.value,
      invite_code: entryInviteCode.value || undefined
    });
    localStorage.setItem('token', res.access_token);
    if (res.refresh_token) {
      localStorage.setItem('refresh_token', res.refresh_token);
    }
    clearEntryChannel();
    showToast('登录成功');
    // 通过授权方式获取地理位置；失败不阻断登录流程。
    // captureAndUploadLocation().catch(() => {});
    router.replace('/home');
  } catch (error) {
    if (error.response?.data?.detail === '渠道链接不存在或已停用') {
      clearEntryChannel();
      entryInviteCode.value = '';
    }
  } finally {
    loading.value = false;
  }
};

onBeforeUnmount(() => {
  if (cooldownTimer) {
    window.clearInterval(cooldownTimer);
    cooldownTimer = null;
  }
  window.removeEventListener('mousemove', onDragMove);
  window.removeEventListener('mouseup', onDragEnd);
  window.removeEventListener('touchmove', onDragMove);
  window.removeEventListener('touchend', onDragEnd);
});
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  position: relative;
  background: var(--app-gradient);
  padding: 18px 20px 28px;
}

.login-stage {
  width: 100%;
  max-width: 400px;
  min-height: calc(100vh - 46px);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.login-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: clamp(148px, 26vh, 260px);
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

.submit-wrap {
  margin: 26px 0 0;
}

.captcha-box {
  width: 100%;
  max-width: 420px;
  margin: 0 auto;
}

.captcha-layer {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(8, 18, 34, 0.2);
  padding: 0;
}

.captcha-popup {
  width: 100%;
  max-width: none;
  background: rgba(236, 244, 255, 0.98);
  border-radius: 16px 16px 0 0;
  padding: 16px;
  box-shadow: 0 12px 28px rgba(21, 42, 78, 0.18);
}

.captcha-title {
  font-size: 15px;
  color: var(--app-primary);
  margin-bottom: 10px;
  font-weight: 600;
}

.captcha-bg-wrap {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
}

.captcha-bg {
  display: block;
  width: 100%;
}

.captcha-slider-piece {
  position: absolute;
  cursor: grab;
  user-select: none;
  touch-action: none;
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

.brand-footer {
  margin-top: 18px;
  margin-bottom: clamp(24px, 6vh, 56px);
  padding: 8px 0;
}

@media (max-height: 760px) {
  .login-main {
    padding-top: 118px;
  }

  .brand-footer {
    margin-bottom: 24px;
  }
}

.brand-logo {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
}

.brand-copy {
  text-align: left;
}

.brand-title {
  font-size: 28px;
  color: var(--app-primary);
  margin: 0;
  font-weight: 700;
  letter-spacing: 2px;
}

.brand-slogan {
  font-size: 14px;
  color: var(--app-text-soft);
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
