<template>
  <div class="login-wrapper">
    <el-card class="login-card">
      <div class="system-logo">
        <img :src="brandLogo" class="brand-logo" alt="小钱包 logo" />
        <div>
          <h2>小钱包管理后台</h2>
          <p>审批、发卡、付款提醒、催收统一处理</p>
        </div>
      </div>
      <el-form :model="form" ref="loginForm" label-position="top">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入管理员账号" prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password @keyup.enter="handleLogin" prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
          登录系统
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { getAdminInfo, login } from '../api';
import { ElMessage } from 'element-plus';
import brandLogo from '../assets/logo.svg';
import {
  clearStoredAdminAuth,
  getFirstAccessibleRoute,
  writeStoredAdminProfile
} from '../constants/adminPages';

const router = useRouter();
const loading = ref(false);
const loginForm = ref(null);

const form = reactive({
  username: 'xiaojiang',
  password: ''
});

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入账号和密码');
    return;
  }
  loading.value = true;
  try {
    const res = await login(form);
    localStorage.setItem('admin_token', res.access_token);
    const profile = await getAdminInfo();
    writeStoredAdminProfile(profile);
    ElMessage.success('登录成功');
    router.replace(getFirstAccessibleRoute(profile.permissions));
  } catch (err) {
    clearStoredAdminAuth();
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background:
    radial-gradient(circle at top left, rgba(85, 152, 255, 0.22), transparent 24%),
    radial-gradient(circle at bottom right, rgba(103, 215, 180, 0.2), transparent 26%),
    linear-gradient(135deg, #0f2747 0%, #17375f 54%, #0d1f37 100%);
  padding: 24px;
}
.login-card {
  width: 100%;
  max-width: 420px;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow: 0 28px 60px rgba(7, 19, 39, 0.26);
}
.system-logo {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 30px;
}

.brand-logo {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  display: block;
  filter: drop-shadow(0 14px 24px rgba(245, 167, 61, 0.18));
}

.system-logo h2 {
  color: #16233a;
  margin: 0;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.system-logo p {
  margin: 8px 0 0;
  color: #6b7a90;
  font-size: 13px;
}
.login-btn {
  width: 100%;
  margin-top: 20px;
  height: 46px;
  font-size: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #2c72e5 0%, #4d8fff 100%);
  border: 0;
}
</style>
