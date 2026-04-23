<template>
  <div class="channel-entry-page">
    <div class="channel-entry-card">
      <img src="../assets/logo.svg" class="entry-logo" alt="小钱包 logo" />
      <h1>专属邀请通道</h1>
      <p>{{ message }}</p>
      <van-loading size="24px" color="#1a56a6" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { bindUserChannel, getChannelEntryInfo } from '../api';
import { clearEntryChannel, saveEntryChannel } from '../utils/channel';

const route = useRoute();
const router = useRouter();
const message = ref('正在识别专属链接，请稍候...');

onMounted(async () => {
  const channelName = String(route.params.channelName || '').trim();
  if (!channelName) {
    clearEntryChannel();
    router.replace('/login');
    return;
  }

  try {
    const channel = await getChannelEntryInfo(channelName);
    saveEntryChannel(channel);
    message.value = `已进入 ${channel.sales_name} 的专属服务通道`;

    if (localStorage.getItem('token')) {
      await bindUserChannel({ channel_name: channel.channel_name });
      router.replace('/home');
      return;
    }

    router.replace('/login');
  } catch (error) {
    clearEntryChannel();
    router.replace('/login');
  }
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
