<template>
  <div class="page-shell change-password-page">
    <section class="page-card form-card">
      <h2 class="section-title">修改登录密码</h2>
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="form.oldPassword"
            type="password"
            name="oldPassword"
            placeholder="请输入原密码"
            maxlength="50"
          />
          <van-field
            v-model="form.newPassword"
            type="password"
            name="newPassword"
            placeholder="请输入新密码（至少6位）"
            maxlength="50"
          />
          <van-field
            v-model="form.confirmPassword"
            type="password"
            name="confirmPassword"
            placeholder="请再次输入新密码"
            maxlength="50"
          />
        </van-cell-group>

        <div class="submit-wrap">
          <van-button block round type="primary" native-type="submit" :loading="loading">确认修改</van-button>
        </div>
      </van-form>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { changePassword } from '../api';

const router = useRouter();
const loading = ref(false);
const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const onSubmit = async () => {
  if (!form.oldPassword || form.oldPassword.length < 6) {
    showToast('请输入原密码');
    return;
  }
  if (!form.newPassword || form.newPassword.length < 6) {
    showToast('请输入至少6位新密码');
    return;
  }
  if (form.newPassword !== form.confirmPassword) {
    showToast('两次输入的新密码不一致');
    return;
  }

  loading.value = true;
  try {
    await changePassword({
      old_password: form.oldPassword,
      new_password: form.newPassword,
      confirm_password: form.confirmPassword
    });
    showToast('密码修改成功，请重新登录');
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    router.replace('/login');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.change-password-page {
  min-height: calc(100vh - 88px);
  padding: calc(env(safe-area-inset-top, 0px) + 22px) 12px 24px;
  box-sizing: border-box;
}

.form-card {
  padding: 16px 0 20px;
}

.section-title {
  margin: 0 16px 14px;
  font-size: 18px;
  color: var(--app-text);
}

.submit-wrap {
  margin: 20px 16px 0;
}
</style>
