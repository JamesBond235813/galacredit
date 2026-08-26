<template>
  <div class="app-layout">
    <!-- Shared top background texture -->
    <div class="layout-bg"></div>

    <div class="layout-content">
      <router-view v-slot="{ Component }">
        <transition name="van-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- Vant Tabbar -->
    <van-tabbar v-model="active" route active-color="#2c5fb7" inactive-color="#9aa8bc">
      <van-tabbar-item replace to="/home" icon="balance-list-o">
        GalaCredit
      </van-tabbar-item>
      <van-tabbar-item replace to="/profile" icon="user-o">
        My Account
      </van-tabbar-item>
    </van-tabbar>

    <div v-if="locationBlocked" class="location-lock">
      <div class="location-lock-panel">
        <div class="location-lock-head">
          <div class="location-lock-title">Location Permission Required</div>
          <div v-if="!locationRequesting" class="location-lock-actions">
            <button type="button" class="location-exit-btn" @click="exitService">Exit</button>
            <button type="button" class="location-close-btn" aria-label="Close" @click="closeLocationPanel">×</button>
          </div>
        </div>
        <div class="location-lock-text">{{ locationBlockMessage }}</div>
        <van-button round block type="primary" :loading="locationRequesting" @click="startLocationAuthorization">
          Allow Location
        </van-button>
      </div>
    </div>
    <button v-if="showInstallButton" type="button" class="install-app-button" @click="installGalaCredit">Install GalaCredit</button>
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
const locationBlockMessage = ref('Please allow location access to continue using this service.');
const installPrompt = ref(null);
const showInstallButton = ref(window.isSecureContext && !window.matchMedia('(display-mode: standalone)').matches);

const installGalaCredit = async () => {
  if (!installPrompt.value) {
    showToast('Open the browser menu and choose Add to Home Screen or Install app. Trust the HTTPS certificate before first use.');
    return;
  }
  installPrompt.value.prompt();
  await installPrompt.value.userChoice;
  installPrompt.value = null;
  showInstallButton.value = false;
};

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
      title: 'Location Permission',
      message: 'Allow location access to help protect your account and credit usage.',
      confirmButtonText: 'Allow',
      cancelButtonText: 'Deny',
      confirmButtonColor: '#2f7ef7',
      closeOnClickOverlay: false
    });
  } catch {
    locationBlocked.value = true;
    locationBlockMessage.value = 'Location access was denied. Allow it to continue using this service.';
    locationRequesting.value = false;
    return;
  }

  try {
    locationBlocked.value = true;
    locationBlockMessage.value = 'Waiting for browser permission. Please allow location access in the system prompt.';
    await captureAndUploadLocation();
    sessionStorage.setItem('h5_location_authorized', '1');
    locationBlocked.value = false;
    showToast('Location access granted');
  } catch (error) {
    locationBlocked.value = true;
    locationBlockMessage.value = getLocationErrorMessage(error);
    // Record the result so the browser does not keep reopening the permission flow on remount.
    sessionStorage.setItem('h5_location_attempted', '1');
    showToast(locationBlockMessage.value);
  } finally {
    locationRequesting.value = false;
  }
};

onMounted(async () => {
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    installPrompt.value = event;
    showInstallButton.value = true;
  });
  if (sessionStorage.getItem('h5_location_authorized') === '1' || sessionStorage.getItem('h5_location_attempted') === '1') {
    return;
  }
  await nextTick();
  sessionStorage.setItem('h5_location_attempted', '1');
  startLocationAuthorization();
});
</script>

<style>
/* Shared background texture */
.app-layout {
  min-height: 100dvh;
  position: relative;
  background: transparent;
  padding-bottom: var(--app-tabbar-space);
}

/* Subtle topographic texture */
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

.install-app-button { position: fixed; right: 16px; bottom: 78px; z-index: 20; border: 0; border-radius: 999px; padding: 10px 16px; color: #fff; background: #f19e2e; box-shadow: 0 6px 16px rgba(0,0,0,.18); }

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
