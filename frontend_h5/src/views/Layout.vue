<template>
  <div class="app-layout">
    <!-- 顶部常态波纹渐变底色 -->
    <div class="layout-bg"></div>

    <div class="layout-content">
      <router-view v-slot="{ Component }">
        <transition name="van-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- Vant Tabbar -->
    <van-tabbar v-model="active" route active-color="#1A56A6" inactive-color="#C0C4CC">
      <van-tabbar-item replace to="/home" icon="balance-list-o">
        小荷包
      </van-tabbar-item>
      <van-tabbar-item replace to="/profile" icon="user-o">
        我的
      </van-tabbar-item>
    </van-tabbar>

    <div v-if="locationBlocked" class="location-lock">
      <div class="location-lock-panel">
        <div class="location-lock-head">
          <div class="location-lock-title">位置授权未完成</div>
          <div v-if="!locationRequesting" class="location-lock-actions">
            <button type="button" class="location-exit-btn" @click="exitService">退出服务</button>
            <button type="button" class="location-close-btn" aria-label="关闭" @click="closeLocationPanel">×</button>
          </div>
        </div>
        <div class="location-lock-text">{{ locationBlockMessage }}</div>
        <van-button round block type="primary" :loading="locationRequesting" @click="startLocationAuthorization">
          重新授权
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { showConfirmDialog, showToast } from 'vant';
import { captureAndUploadLocation, getLocationErrorMessage } from '../utils/location';

const route = useRoute();
const router = useRouter();
const active = computed({
  get: () => (route.meta.tab === 'profile' ? 1 : 0),
  set: () => {}
});

const locationBlocked = ref(false);
const locationRequesting = ref(false);
const locationBlockMessage = ref('请先授权获取当前位置，授权完成前暂不能继续操作。');

const closeLocationPanel = () => {
  if (locationRequesting.value) {
    return;
  }
  locationBlocked.value = false;
};

const exitService = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  sessionStorage.removeItem('h5_location_authorized');
  locationBlocked.value = false;
  router.replace('/login');
};

const startLocationAuthorization = async () => {
  if (locationRequesting.value) {
    return;
  }
  locationRequesting.value = true;
  locationBlocked.value = false;
  try {
    await showConfirmDialog({
      title: '位置授权',
      message: '为保障账户与额度使用安全，请同意获取当前地理位置。',
      confirmButtonText: '同意',
      cancelButtonText: '拒绝',
      confirmButtonColor: '#2f7ef7',
      closeOnClickOverlay: false
    });
  } catch {
    locationBlocked.value = true;
    locationBlockMessage.value = '您已拒绝位置授权，当前服务已冻结。请重新授权后继续使用。';
    locationRequesting.value = false;
    return;
  }

  try {
    locationBlocked.value = true;
    locationBlockMessage.value = '正在等待浏览器位置授权，请在系统弹窗中允许读取位置。';
    await captureAndUploadLocation();
    sessionStorage.setItem('h5_location_authorized', '1');
    locationBlocked.value = false;
    showToast('位置授权成功');
  } catch (error) {
    locationBlocked.value = true;
    locationBlockMessage.value = getLocationErrorMessage(error);
    showToast(locationBlockMessage.value);
  } finally {
    locationRequesting.value = false;
  }
};

onMounted(async () => {
  if (sessionStorage.getItem('h5_location_authorized') === '1') {
    return;
  }
  await nextTick();
  startLocationAuthorization();
});
</script>

<style>
/* 全局波纹纹理定义 */
.app-layout {
  min-height: 100vh;
  position: relative;
  background: transparent;
  padding-bottom: var(--app-tabbar-space);
}

/* 绘制参考图中的浅色拓扑网格波云纹理效果 */
.layout-bg {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 360px;
  background:
    radial-gradient(circle at top left, rgba(255,255,255,0.7) 0%, transparent 34%),
    radial-gradient(circle at top right, rgba(47,126,247,0.08) 0%, transparent 42%),
    repeating-radial-gradient(circle at top right, transparent, transparent 14px, rgba(44,95,183,0.04) 14px, rgba(44,95,183,0.04) 15px);
  z-index: 0;
  pointer-events: none;
}

.layout-content {
  position: relative;
  z-index: 1;
  height: 100%;
}

.van-tabbar {
  left: 14px;
  right: 14px;
  bottom: calc(10px + env(safe-area-inset-bottom, 0px));
  width: auto;
  height: var(--app-tabbar-height);
  border-radius: calc(var(--app-tabbar-height) / 2);
  border: 1px solid var(--app-border);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--app-shadow);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.van-tabbar::after {
  display: none;
}

.van-tabbar-item {
  color: var(--app-text-faint);
}

.van-tabbar-item--active {
  background: transparent;
}

.van-tabbar-item--active .van-tabbar-item__icon,
.van-tabbar-item--active .van-tabbar-item__text {
  color: var(--app-primary-deep);
  font-weight: 600;
}

.location-lock {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 22px;
  background: rgba(10, 22, 42, 0.38);
}

.location-lock-panel {
  position: relative;
  width: min(100%, 340px);
  border-radius: 16px;
  padding: 22px 20px;
  background: #fff;
  box-shadow: 0 18px 42px rgba(22, 52, 92, 0.2);
}

.location-lock-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.location-lock-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--app-text-main);
}

.location-lock-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.location-exit-btn,
.location-close-btn {
  border: 0;
  background: transparent;
  color: var(--app-primary-deep);
  cursor: pointer;
}

.location-exit-btn {
  padding: 1px 0;
  font-size: 13px;
  line-height: 20px;
}

.location-close-btn {
  width: 22px;
  height: 22px;
  padding: 0;
  color: #8a98aa;
  font-size: 22px;
  line-height: 20px;
}

.location-lock-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--app-text-muted);
  margin-bottom: 18px;
}
</style>
