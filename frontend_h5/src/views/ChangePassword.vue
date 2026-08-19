<template>
  <div class="page-shell change-password-page">
    <section class="page-card form-card">
      <h2 class="section-title">Change Sign-in Password</h2>
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="form.oldPassword"
            type="password"
            name="oldPassword"
            placeholder="Current password"
            maxlength="50"
          />
          <van-field
            v-model="form.newPassword"
            type="password"
            name="newPassword"
            placeholder="New password (at least 6 characters)"
            maxlength="50"
          />
          <van-field
            v-model="form.confirmPassword"
            type="password"
            name="confirmPassword"
            placeholder="Confirm new password"
            maxlength="50"
          />
        </van-cell-group>

        <div class="submit-wrap">
          <van-button block round type="primary" native-type="submit" :loading="loading">Update Password</van-button>
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
    showToast('Enter your current password');
    return;
  }
  if (!form.newPassword || form.newPassword.length < 6) {
    showToast('Enter a new password with at least 6 characters');
    return;
  }
  if (form.newPassword !== form.confirmPassword) {
    showToast('The new passwords do not match');
    return;
  }

  loading.value = true;
  try {
    await changePassword({
      old_password: form.oldPassword,
      new_password: form.newPassword,
      confirm_password: form.confirmPassword
    });
    showToast('Password updated. Please sign in again.');
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
  width: min(100%, 430px);
  min-height: calc(100dvh - 88px);
  margin: 0 auto;
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
