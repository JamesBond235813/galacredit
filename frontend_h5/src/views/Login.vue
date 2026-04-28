<template>
  <div class="login-container">
    <div class="login-stage">
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
              v-model="code"
              name="code"
              center
              clearable
              type="digit"
              maxlength="6"
              placeholder="请输入6位验证码"
              :formatter="normalizeCode"
              class="login-field"
            >
              <template #button>
                <van-button
                  size="small"
                  type="primary"
                  native-type="button"
                  class="code-btn"
                  :loading="codeLoading"
                  :disabled="codeLoading || cooldownSeconds > 0"
                  @click="requestSmsCode"
                >
                  {{ codeButtonText }}
                </van-button>
              </template>
            </van-field>
          </van-cell-group>
          <div class="submit-wrap">
            <van-button round block type="primary" native-type="submit" :loading="loading" class="submit-btn">
              登录 / 注册
            </van-button>
          </div>
        </van-form>
      </section>

      <div class="logo-box brand-footer">
        <img src="../assets/logo.svg" class="brand-logo" alt="小钱包 logo" />
        <div class="brand-copy">
          <h1 class="brand-title">小钱包</h1>
          <p class="brand-slogan">解生活之所急</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { sendCode, login } from '../api';
import { clearEntryChannel, getEntryChannel } from '../utils/channel';
import { captureAndUploadLocation } from '../utils/location';
import {
  getSmsButtonText,
  isValidSmsCode,
  normalizeSmsCode,
  SMS_COOLDOWN_SECONDS
} from '../utils/smsLogin';

const router = useRouter();
const phone = ref('');
const code = ref('');
const loading = ref(false);
const codeLoading = ref(false);
const cooldownSeconds = ref(0);
let cooldownTimer = null;
const entryChannel = ref(getEntryChannel());

const codeButtonText = computed(() => getSmsButtonText(codeLoading.value, cooldownSeconds.value));

const normalizePhone = (value) => value.replace(/\D/g, '').slice(0, 11);
const normalizeCode = (value) => normalizeSmsCode(value);
const isValidPhone = (value) => /^\d{11}$/.test(value);
const isValidCode = (value) => isValidSmsCode(value);

watch(phone, () => {
  code.value = '';
});

const clearCooldownTimer = () => {
  if (cooldownTimer) {
    window.clearInterval(cooldownTimer);
    cooldownTimer = null;
  }
};

const startCooldown = (seconds = SMS_COOLDOWN_SECONDS) => {
  clearCooldownTimer();
  cooldownSeconds.value = Math.max(Number(seconds) || 0, 0);
  if (cooldownSeconds.value <= 0) {
    return;
  }
  cooldownTimer = window.setInterval(() => {
    if (cooldownSeconds.value <= 1) {
      cooldownSeconds.value = 0;
      clearCooldownTimer();
      return;
    }
    cooldownSeconds.value -= 1;
  }, 1000);
};

const requestSmsCode = async () => {
  if (!isValidPhone(phone.value)) {
    showToast('请输入11位手机号');
    return;
  }

  if (codeLoading.value || cooldownSeconds.value > 0) {
    return;
  }

  try {
    codeLoading.value = true;
    const res = await sendCode({ phone: phone.value });
    startCooldown(res?.cooldown_seconds || SMS_COOLDOWN_SECONDS);
  } catch (error) {
    // Handled by interceptor
  } finally {
    codeLoading.value = false;
  }
};

const onSubmit = async () => {
  if (!isValidPhone(phone.value)) {
    showToast('请输入11位手机号');
    return;
  }

  if (!isValidCode(code.value)) {
    showToast('请输入6位验证码');
    return;
  }

  loading.value = true;
  try {
    const res = await login({
      phone: phone.value,
      code: code.value,
      channel_name: entryChannel.value?.channel_name || undefined
    });
    localStorage.setItem('token', res.access_token);
    if (res.refresh_token) {
      localStorage.setItem('refresh_token', res.refresh_token);
    }
    showToast('登录成功');
    // 通过授权方式获取地理位置；失败不阻断登录流程。
    captureAndUploadLocation().catch(() => {});
    router.replace('/home');
  } catch (error) {
    if (error.response?.data?.detail === '渠道链接不存在或已停用') {
      clearEntryChannel();
      entryChannel.value = null;
    }
  } finally {
    loading.value = false;
  }
};

onBeforeUnmount(() => {
  clearCooldownTimer();
});
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
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

:deep(.login-field .van-field__button) {
  display: flex;
  align-items: center;
  height: 64px;
}

.code-btn {
  min-width: 84px;
  height: 38px;
  padding: 0 14px;
  background: var(--app-gradient);
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.submit-btn {
  height: 56px;
  background: var(--app-gradient);
  border: none;
  font-size: 18px;
  font-weight: 600;
  box-shadow: 0 14px 28px rgba(42, 120, 227, 0.24);
  transition: transform 0.2s;
}
.submit-btn:active {
  transform: scale(0.98);
}
</style>
