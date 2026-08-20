<template>
  <el-container class="layout-container">
    <el-aside width="248px" class="aside-menu">
      <div class="logo">
        <img :src="brandLogo" class="brand-logo" alt="GalaCredit logo" />
        <div class="logo-copy">
          <strong>GalaCredit</strong>
          <span>{{ t('brandSubtitle') }}</span>
        </div>
      </div>

      <el-menu :default-active="route.path" :default-openeds="openGroupKeys" class="el-menu-vertical" router>
        <el-sub-menu v-for="group in visibleMenuGroups" :key="group.key" :index="group.key">
          <template #title>
            <el-icon><component :is="iconMap[group.iconKey]" /></el-icon>
            <span>{{ t(group.key) }}</span>
          </template>
          <el-menu-item v-for="item in group.items" :key="item.key" :index="item.route">
            <el-icon><component :is="iconMap[item.iconKey]" /></el-icon>
            <div class="menu-item-content">
              <span>{{ getMenuLabel(item.key) }}</span>
              <span v-if="getMenuBadgeCount(item.key) > 0" class="menu-badge">
                {{ getMenuBadgeCount(item.key) }}
              </span>
            </div>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="main-header">
        <div class="header-left">
          <h2 class="page-title">{{ getPageTitle(route.meta.permission || 'overview') }}</h2>
          <p class="page-subtitle">{{ pageSubtitle }}</p>
        </div>

        <div class="header-right">
          <el-select v-model="selectedLocale" class="locale-select" size="small" :aria-label="t('language')" @change="handleLocaleChange">
            <el-option label="中文" value="zh-CN" />
            <el-option label="English" value="en-GH" />
          </el-select>
          <div class="header-date">{{ currentDateText }}</div>
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar size="small" class="admin-avatar">{{ adminLocale === 'en-GH' ? 'A' : '管' }}</el-avatar>
              {{ adminDisplayName }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="change-password">{{ t('changePassword') }}</el-dropdown-item>
                <el-dropdown-item command="logout">{{ t('logout') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>

      <el-dialog v-model="passwordDialogVisible" width="460px" :title="t('changePassword')" destroy-on-close>
        <el-form label-position="top">
          <el-form-item :label="t('oldPassword')" required>
            <el-input v-model="passwordForm.oldPassword" type="password" show-password maxlength="50" />
          </el-form-item>
          <el-form-item :label="t('newPassword')" required>
            <el-input v-model="passwordForm.newPassword" type="password" show-password maxlength="50" />
          </el-form-item>
          <el-form-item :label="t('confirmPassword')" required>
            <el-input v-model="passwordForm.confirmPassword" type="password" show-password maxlength="50" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="passwordDialogVisible = false">{{ t('cancel') }}</el-button>
          <el-button type="primary" :loading="changingPassword" @click="submitChangePassword">{{ t('confirm') }}</el-button>
        </template>
      </el-dialog>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useRoute, useRouter } from 'vue-router';
import {
  ArrowDown,
  BellFilled,
  Connection,
  CreditCard,
  DataAnalysis,
  DocumentChecked,
  Document,
  Goods,
  Money,
  Monitor,
  Notebook,
  Setting,
  Tickets,
  User,
  WalletFilled,
  WarnTriangleFilled
} from '@element-plus/icons-vue';
import { changeAdminPassword, getAdminInfo, getAdminStats } from '../api';
import brandLogo from '../assets/logo.svg';
import {
  ADMIN_MENU_GROUPS,
  ADMIN_PAGE_OPTIONS,
  clearStoredAdminAuth,
  getFirstAccessibleRoute,
  hasAdminPermission,
  readStoredAdminProfile,
  getStoredAdminPermissions,
  writeStoredAdminProfile
} from '../constants/adminPages';
import { adminLocale, getMenuLabel, getPageTitle, setAdminLocale, t } from '../i18n/adminLocale';

const route = useRoute();
const router = useRouter();
const adminProfile = ref(readStoredAdminProfile());
const menuBadgeStats = ref({
  reviewing_loans: 0,
  withdrawing_loans: 0,
  due_today_users: 0,
  repay_attempt_total: 0
});
const STATS_WS_RECONNECT_MS = 3000;
let statsSocket = null;
let statsReconnectTimer = null;
const passwordDialogVisible = ref(false);
const changingPassword = ref(false);
const passwordForm = ref({ oldPassword: '', newPassword: '', confirmPassword: '' });
const selectedLocale = ref(adminLocale.value);

const iconMap = {
  overview: DataAnalysis,
  monitoring: Monitor,
  messageCenter: BellFilled,
  users: User,
  kycReview: Notebook,
  applications: DocumentChecked,
  disbursements: Money,
  disbursementFailures: WarnTriangleFilled,
  repayments: CreditCard,
  collections: WarnTriangleFilled,
  financials: WalletFilled,
  auditLog: Document,
  riskSingleQuery: DataAnalysis,
  riskStrategy: Setting,
  overdueConfig: Setting,
  contentConfig: Tickets,
  products: Goods,
  ecardPool: Tickets,
  channels: Connection,
  adminUsers: Setting
};

const currentDateText = computed(() => new Date().toLocaleString(adminLocale.value, { hour12: false }));
const pageSubtitle = computed(() => adminLocale.value === 'en-GH'
  ? t('defaultSubtitle')
  : route.meta.description || t('defaultSubtitle'));
const adminDisplayName = computed(() => adminProfile.value?.username || (adminLocale.value === 'en-GH' ? 'Administrator' : '后台用户'));
const visibleMenuGroups = computed(() => ADMIN_MENU_GROUPS.map((group) => ({
  ...group,
  items: group.itemKeys
    .map((key) => ADMIN_PAGE_OPTIONS.find((item) => item.key === key))
    .filter((item) => item && (!adminProfile.value?.permissions?.length || hasAdminPermission(adminProfile.value.permissions, item.key)))
})).filter((group) => group.items.length));
const openGroupKeys = computed(() => {
  const activeGroup = visibleMenuGroups.value.find((group) => group.items.some((item) => item.route === route.path));
  return activeGroup ? [activeGroup.key] : visibleMenuGroups.value.map((group) => group.key);
});

const handleLocaleChange = (locale) => {
  setAdminLocale(locale);
  selectedLocale.value = locale;
};

const canReadStats = () => {
  const permissions = getStoredAdminPermissions();
  if (!Array.isArray(permissions) || permissions.length === 0) {
    return true;
  }
  return ['overview', 'applications', 'disbursements', 'repayments', 'collections', 'financials']
    .some((key) => permissions.includes(key));
};

const syncAdminProfile = async () => {
  const token = localStorage.getItem('admin_token');
  if (!token) {
    return;
  }

  const profile = await getAdminInfo();
  adminProfile.value = profile;
  writeStoredAdminProfile(profile);

  if (route.meta.permission && !hasAdminPermission(profile.permissions, route.meta.permission)) {
    router.replace(getFirstAccessibleRoute(profile.permissions));
  }
};

const syncMenuBadgeStats = async () => {
  const token = localStorage.getItem('admin_token');
  if (!token || !canReadStats()) {
    return;
  }
  try {
    const stats = await getAdminStats();
    menuBadgeStats.value = {
      reviewing_loans: Number(stats.reviewing_loans || 0),
      withdrawing_loans: Number(stats.withdrawing_loans || 0),
      due_today_users: Number(stats.due_today_users || stats.due_today_loans || 0),
      repay_attempt_total: Number(stats.repay_attempt_total || 0)
    };
  } catch (error) {
    // Ignore sidebar badge fetch errors to avoid interrupting route rendering
  }
};

const applyMenuBadgeStats = (stats) => {
  menuBadgeStats.value = {
    reviewing_loans: Number(stats.reviewing_loans || 0),
    withdrawing_loans: Number(stats.withdrawing_loans || 0),
    due_today_users: Number(stats.due_today_users || stats.due_today_loans || 0),
    repay_attempt_total: Number(stats.repay_attempt_total || 0)
  };
};

const buildStatsWsUrl = () => {
  const token = localStorage.getItem('admin_token');
  if (!token) {
    return null;
  }
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
  const resolvedApiBase = apiBaseUrl ? new URL(apiBaseUrl, window.location.origin) : new URL('/api', window.location.origin);
  const wsProtocol = resolvedApiBase.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = new URL('/api/admin/ws/stats', `${wsProtocol}//${resolvedApiBase.host}`);
  wsUrl.searchParams.set('token', token);
  return wsUrl.toString();
};

const scheduleStatsSocketReconnect = () => {
  if (statsReconnectTimer || !localStorage.getItem('admin_token')) {
    return;
  }
  statsReconnectTimer = window.setTimeout(() => {
    statsReconnectTimer = null;
    connectStatsSocket();
  }, STATS_WS_RECONNECT_MS);
};

const closeStatsSocket = () => {
  if (statsSocket) {
    statsSocket.onopen = null;
    statsSocket.onmessage = null;
    statsSocket.onclose = null;
    statsSocket.onerror = null;
    statsSocket.close();
    statsSocket = null;
  }
};

const handleStatsSocketAuthFailed = () => {
  closeStatsSocket();
  clearStoredAdminAuth();
  router.replace('/login');
};

const connectStatsSocket = () => {
  if (!canReadStats()) {
    return;
  }
  const wsUrl = buildStatsWsUrl();
  if (!wsUrl) {
    return;
  }

  closeStatsSocket();
  const socket = new WebSocket(wsUrl);
  statsSocket = socket;

  socket.onopen = () => {
    // 首次连上后同步一次，避免首帧前菜单角标为空。
    syncMenuBadgeStats();
  };

  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data || '{}');
      if (payload?.type === 'admin_stats' && payload?.data) {
        applyMenuBadgeStats(payload.data);
      }
    } catch (error) {
      // Ignore malformed websocket messages.
    }
  };

  socket.onerror = () => {
    socket.close();
  };

  socket.onclose = (event) => {
    if (statsSocket === socket) {
      statsSocket = null;
    }
    if (event?.code === 1008) {
      handleStatsSocketAuthFailed();
      return;
    }
    scheduleStatsSocketReconnect();
  };
};

const getMenuBadgeCount = (menuKey) => {
  if (menuKey === 'applications') {
    return Number(menuBadgeStats.value.reviewing_loans || 0);
  }
  if (menuKey === 'disbursements') {
    return Number(menuBadgeStats.value.withdrawing_loans || 0);
  }
  if (menuKey === 'repayments') {
    return Number(menuBadgeStats.value.repay_attempt_total || 0);
  }
  return 0;
};

const handleRepayAttemptAck = (event) => {
  const cleared = Number(event?.detail?.cleared || 0);
  if (!cleared) {
    return;
  }
  const current = Number(menuBadgeStats.value.repay_attempt_total || 0);
  menuBadgeStats.value = {
    ...menuBadgeStats.value,
    repay_attempt_total: Math.max(0, current - cleared)
  };
};

const handleCommand = (command) => {
  if (command === 'change-password') {
    passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' };
    passwordDialogVisible.value = true;
    return;
  }
  if (command === 'logout') {
    closeStatsSocket();
    clearStoredAdminAuth();
    router.replace('/login');
  }
};

const submitChangePassword = async () => {
  if (!passwordForm.value.oldPassword || !passwordForm.value.newPassword || !passwordForm.value.confirmPassword) {
    ElMessage.warning('请完整填写密码信息');
    return;
  }
  if (passwordForm.value.newPassword.length < 6) {
    ElMessage.warning('新密码至少 6 位');
    return;
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致');
    return;
  }
  changingPassword.value = true;
  try {
    await changeAdminPassword({
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword,
      confirm_password: passwordForm.value.confirmPassword
    });
    ElMessage.success('密码修改成功');
    passwordDialogVisible.value = false;
  } finally {
    changingPassword.value = false;
  }
};

onMounted(() => {
  syncAdminProfile();
  syncMenuBadgeStats();
  connectStatsSocket();
  window.addEventListener('admin-repay-attempt-ack', handleRepayAttemptAck);
});

onBeforeUnmount(() => {
  if (statsReconnectTimer) {
    window.clearTimeout(statsReconnectTimer);
    statsReconnectTimer = null;
  }
  closeStatsSocket();
  window.removeEventListener('admin-repay-attempt-ack', handleRepayAttemptAck);
});
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(21, 117, 255, 0.08), transparent 28%),
    linear-gradient(180deg, #f5f8fd 0%, #eff4fb 100%);
}

.aside-menu {
  border-right: 1px solid rgba(13, 63, 131, 0.08);
  background: linear-gradient(180deg, #0f2747 0%, #17375f 100%);
  z-index: 10;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 22px 20px;
  color: #fff;
}

.brand-logo {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.logo-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.logo-copy strong {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
}

.logo-copy span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.76);
  letter-spacing: 0.8px;
}

.locale-select {
  width: 112px;
}

.el-menu-vertical {
  border-right: none;
  background: transparent;
}

.el-menu-vertical :deep(.el-sub-menu .el-menu) {
  background: transparent;
}

.el-menu-vertical :deep(.el-sub-menu__title) {
  height: 48px;
  line-height: 48px;
  margin: 4px 10px 0;
  border-radius: 8px;
  color: #9aabc2;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0;
}

.el-menu-vertical :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.el-menu-vertical :deep(.el-sub-menu .el-menu-item) {
  padding-left: 50px !important;
}

.el-menu-vertical :deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin: 4px 14px;
  border-radius: 14px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 15px;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.menu-item-content {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.menu-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(240, 68, 56, 0.72);
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}

.el-menu-vertical :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.el-menu-vertical :deep(.el-menu-item:hover .el-icon) {
  color: #ffffff;
}

.el-menu-vertical :deep(.el-menu-item.is-active) {
  background: #f19e2e;
  color: #142b4d;
  font-weight: 700;
  box-shadow: 0 6px 14px rgba(241, 158, 46, 0.22);
}

.el-menu-vertical :deep(.el-menu-item.is-active .el-icon) {
  color: #142b4d;
}

.main-header {
  height: 74px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(13, 63, 131, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #16233a;
}

.page-subtitle {
  margin: 6px 0 0;
  font-size: 12px;
  color: #6b7a90;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-date {
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(13, 63, 131, 0.08);
  color: #5f7188;
  font-size: 12px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #405066;
  font-weight: 600;
}

.admin-avatar {
  background: linear-gradient(135deg, #2c72e5 0%, #67d7b4 100%);
}

.main-content {
  padding: 24px;
  overflow: auto;
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.24s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateY(14px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(-14px);
}
</style>
