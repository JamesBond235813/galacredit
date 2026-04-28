<template>
  <div class="page-shell profile-page">
    <header class="profile-header">
      <div class="user-copy">
        <h1 class="greeting">您好，{{ maskedPhone }}</h1>
        <div class="license-pill">
          <van-icon name="shield-o" />
          <span>信用消费服务，信息加密保护</span>
        </div>
      </div>

      <div class="avatar-box">
        <div class="avatar-inner">
          <van-icon name="user-o" />
        </div>
      </div>
    </header>

    <section class="notice-panel">
      <div class="notice-banner">
        <div class="notice-main">
          <van-icon name="volume-o" class="notice-icon" />
          <span class="notice-text">公告：{{ noticeText }}</span>
        </div>
        <span class="notice-brand">小荷包</span>
      </div>

      <div class="services-card page-card">
        <h2 class="section-title">我的服务</h2>
        <div class="services-grid">
          <button
            v-for="item in serviceItems"
            :key="item.key"
            type="button"
            class="service-item"
            :class="{ 'service-item-active': item.key === activeServiceKey }"
            @click="goToRoute(item.route)"
          >
            <span class="service-icon">
              <van-icon :name="item.icon" />
            </span>
            <span class="service-title">{{ item.title }}</span>
          </button>
        </div>
      </div>
    </section>

    <section class="menu-card page-card">
      <h2 class="section-title">更多服务</h2>
      <div class="menu-list">
        <button
          v-for="item in menuItems"
          :key="item.key"
          type="button"
          class="menu-item"
          @click="handleMenuAction(item.key)"
        >
          <span class="menu-icon">
            <van-icon :name="item.icon" />
          </span>
          <span class="menu-title">{{ item.title }}</span>
          <van-icon name="arrow" class="menu-arrow" />
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { getUserInfo } from '../api';
import { createLoanSnapshotSubscriber } from '../api/loanSocket';

const router = useRouter();
const phone = ref('');
const loanStatus = ref('INIT');
let loanSnapshotSubscriber = null;

const serviceItems = [
  { key: 'withdraw', title: '待下单', icon: 'balance-pay', route: '/withdraw' },
  { key: 'review', title: '审核中', icon: 'records', route: '/review' },
  { key: 'repayment', title: '待付款', icon: 'idcard', route: '/bill' }
];

const menuItems = [
  { key: 'service', title: '专属客服', icon: 'service-o' },
  { key: 'change-password', title: '修改密码', icon: 'shield-o' },
  { key: 'refresh', title: '点击更新', icon: 'replay' },
  { key: 'about', title: '关于我们', icon: 'info-o' },
  { key: 'agreement', title: '用户协议', icon: 'orders-o' },
  { key: 'feedback', title: '问题反馈', icon: 'comment-o' }
];

const maskedPhone = computed(() => formatMaskedPhone(phone.value));

const activeServiceKey = computed(() => {
  if (loanStatus.value === 'APPROVED') {
    return 'withdraw';
  }

  if (loanStatus.value === 'REVIEWING') {
    return 'review';
  }

  if (['WITHDRAWING', 'DISBURSED', 'OVERDUE'].includes(loanStatus.value)) {
    return 'repayment';
  }

  return '';
});

const noticeText = computed(() => {
  if (loanStatus.value === 'OVERDUE') {
    return '当前账单已逾期，请尽快联系专员处理。';
  }

  return '小荷包最新诈骗防范指南，请勿向私人账户转账。';
});

const formatMaskedPhone = (value) => {
  if (!value || typeof value !== 'string') {
    return '188******12';
  }

  if (/^\d{11}$/.test(value)) {
    return value.replace(/(\d{3})\d{6}(\d{2})/, '$1******$2');
  }

  return value;
};

const loadProfileData = async (showSuccessToast = false) => {
  try {
    const userInfo = await getUserInfo();
    phone.value = userInfo?.phone || '';
  } catch (error) {
    phone.value = '';
  }

  if (showSuccessToast) {
    showToast('页面信息已更新');
  }
};

const applyLoanSnapshot = (snapshot) => {
  loanStatus.value = snapshot?.status || 'INIT';
};

const goToRoute = (route) => {
  if (!route) {
    return;
  }

  router.push(route);
};

const handleMenuAction = async (key) => {
  if (key === 'refresh') {
    await loadProfileData(true);
    return;
  }

  if (key === 'about') {
    router.push('/about');
    return;
  }

  if (key === 'service') {
    router.push('/support');
    return;
  }

  if (key === 'change-password') {
    router.push('/change-password');
    return;
  }

  if (key === 'agreement') {
    router.push('/agreement');
    return;
  }

  if (key === 'feedback') {
    showToast('问题反馈入口正在完善');
  }
};

onMounted(() => {
  loadProfileData();
  loanSnapshotSubscriber = createLoanSnapshotSubscriber({
    onSnapshot: applyLoanSnapshot
  });
  loanSnapshotSubscriber.start();
});

onBeforeUnmount(() => {
  if (loanSnapshotSubscriber) {
    loanSnapshotSubscriber.stop();
    loanSnapshotSubscriber = null;
  }
});
</script>

<style scoped>
.profile-page {
  min-height: calc(100vh - 88px);
  padding: calc(env(safe-area-inset-top, 0px) + 22px) 10px 24px;
  box-sizing: border-box;
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 10px;
}

.user-copy {
  min-width: 0;
  flex: 1;
}

.greeting {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
  font-weight: 700;
  color: var(--app-text);
}

.license-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 8px 14px;
  border-radius: 999px;
  background: linear-gradient(180deg, #fff7dc 0%, #fff1cb 100%);
  color: #b37712;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 8px 18px rgba(224, 177, 64, 0.18);
}

.license-pill .van-icon {
  font-size: 16px;
}

.avatar-box {
  width: 70px;
  height: 70px;
  padding: 4px;
  flex-shrink: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: var(--app-shadow);
}

.avatar-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(180deg, #eef3ff 0%, #f8fbff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-primary-deep);
  font-size: 36px;
}

.notice-panel {
  margin-top: 28px;
}

.notice-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 78px;
  padding: 14px 16px 40px;
  border-radius: 18px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.12), transparent 34%),
    var(--app-gradient-deep);
  box-shadow: var(--app-shadow-strong);
}

.notice-main {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
}

.notice-icon {
  flex-shrink: 0;
  font-size: 16px;
}

.notice-text {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.notice-brand {
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 13px;
}

.services-card,
.menu-card {
  background: var(--app-surface);
}

.services-card {
  margin-top: -24px;
  position: relative;
  z-index: 1;
  padding: 22px 18px 20px;
  border-radius: 22px;
}

.menu-card {
  margin-top: 18px;
  padding: 22px 18px 12px;
  border-radius: 22px;
}

.section-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--app-text);
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 22px;
}

.service-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 92px;
  border-radius: 16px;
  color: var(--app-primary-deep);
}

.service-item-active {
  background: rgba(47, 126, 247, 0.08);
}

.service-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(47, 126, 247, 0.08);
  font-size: 23px;
}

.service-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
}

.menu-list {
  margin-top: 12px;
}

.menu-item {
  width: 100%;
  min-height: 60px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: inherit;
}

.menu-item + .menu-item {
  border-top: 1px solid #eef3fb;
}

.menu-icon {
  flex-shrink: 0;
  width: 22px;
  text-align: center;
  color: var(--app-text-soft);
  font-size: 21px;
}

.menu-title {
  flex: 1;
  text-align: left;
  font-size: 15px;
  font-weight: 500;
  color: var(--app-text);
}

.menu-arrow {
  flex-shrink: 0;
  color: var(--app-text-faint);
  font-size: 18px;
}

button {
  border: 0;
  padding: 0;
  font: inherit;
  background: transparent;
  outline: none;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
}

@media (max-width: 360px) {
  .greeting {
    font-size: 22px;
  }

  .services-grid {
    gap: 8px;
  }

  .service-title {
    font-size: 13px;
  }
}
</style>
