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
              v-model="password"
              name="password"
              type="password"
              maxlength="50"
              placeholder="请输入登录密码"
              clearable
              class="login-field"
            />
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
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { login } from '../api';
import { clearEntryChannel, getEntryChannel } from '../utils/channel';
import { captureAndUploadLocation } from '../utils/location';
import { isValidPassword, isValidPhone, normalizePhone } from '../utils/passwordAuth';

const router = useRouter();
const phone = ref('');
const password = ref('');
const loading = ref(false);
const entryChannel = ref(getEntryChannel());

const onSubmit = async () => {
  if (!isValidPhone(phone.value)) {
    showToast('请输入11位手机号');
    return;
  }

  if (!isValidPassword(password.value)) {
    showToast('请输入至少6位密码');
    return;
  }

  loading.value = true;
  try {
    const res = await login({
      phone: phone.value,
      password: password.value,
      channel_name: entryChannel.value?.channel_name || undefined
    });
    localStorage.setItem('token', res.access_token);
    if (res.refresh_token) {
      localStorage.setItem('refresh_token', res.refresh_token);
    }
    showToast('登录成功');
    // 通过授权方式获取地理位置；失败不阻断登录流程。
    // captureAndUploadLocation().catch(() => {});
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
</style>
