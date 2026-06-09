<template>
  <div class="channel-entry-page">
    <div class="channel-entry-card">
      <img src="../assets/logo.svg" class="entry-logo" alt="小荷包 logo" />
      <h1>专属邀请通道</h1>
      <p>{{ message }}</p>
      <van-loading size="24px" color="#1a56a6" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { saveEntryInviteCode, isValidInviteCode } from '../utils/channel';

const route = useRoute();
const message = ref('正在识别专属链接，请稍候...');

const redirectToLogin = () => {
  window.setTimeout(() => {
    window.location.replace('/login');
  }, 120);
};

onMounted(() => {
  const inviteCode = String(route.params.inviteCode || '').trim().toLowerCase();
  if (isValidInviteCode(inviteCode)) {
    saveEntryInviteCode(inviteCode);
    message.value = '已识别专属邀请码，正在跳转登录...';
  }
  redirectToLogin();
});
</script>

<style scoped>
.channel-entry-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--app-gradient);
}

.channel-entry-card {
  width: 100%;
  max-width: 360px;
  padding: 32px 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.24);
  box-shadow: 0 20px 42px rgba(28, 71, 142, 0.18);
  backdrop-filter: blur(14px);
  text-align: center;
}

.entry-logo {
  width: 68px;
  height: 68px;
}

.channel-entry-card h1 {
  margin: 18px 0 10px;
  font-size: 22px;
  color: var(--app-primary);
}

.channel-entry-card p {
  margin: 0 0 18px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--app-text-soft);
}
</style>
