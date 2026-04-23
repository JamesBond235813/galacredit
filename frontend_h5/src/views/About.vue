<template>
  <div class="page-shell about-page">
    <van-nav-bar title="关于我们" left-arrow @click-left="router.back()" />

    <div class="about-content">
      <section class="about-card page-card brand-card">
        <div class="brand-header">
          <img :src="brandLogo" class="brand-logo" alt="小钱包 logo" />
          <h1 class="brand-title">小钱包</h1>
        </div>
        <p class="brand-desc">
          小钱包为认证用户提供授信申请、信用下单、发卡进度与付款账单查询等服务，页面信息仅用于展示当前业务状态。
        </p>
      </section>

      <section class="about-card page-card info-card">
        <div class="info-row">
          <span class="info-label">服务说明</span>
          <span class="info-value">授信与账单信息查询</span>
        </div>
        <div class="info-row">
          <span class="info-label">客服时间</span>
          <span class="info-value">工作日 09:00 - 18:00</span>
        </div>
        <div class="info-row">
          <span class="info-label">安全提示</span>
          <span class="info-value">请勿向私人账户转账</span>
        </div>
      </section>

      <van-button block class="primary-action logout-btn" @click="handleLogout">
        退出登录
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import brandLogo from '../assets/logo.svg';

const router = useRouter();

const handleLogout = () => {
  localStorage.removeItem('token');
  router.replace('/login');
};
</script>

<style scoped>
.about-page {
  min-height: 100vh;
}

.about-content {
  padding: 18px 16px 28px;
}

.about-card {
  background: var(--app-surface);
}

.brand-card {
  padding: 28px 20px 24px;
}

.brand-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-bottom: 14px;
}

.brand-logo {
  width: 76px;
  height: 76px;
  display: block;
  filter: drop-shadow(0 12px 24px rgba(47, 94, 177, 0.18));
}

.brand-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--app-text);
}

.brand-desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--app-text-soft);
  text-align: center;
}

.info-card {
  margin-top: 16px;
  padding: 6px 18px;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 56px;
}

.info-row + .info-row {
  border-top: 1px solid #eef3fb;
}

.info-label {
  font-size: 14px;
  color: var(--app-text-soft);
}

.info-value {
  text-align: right;
  font-size: 14px;
  font-weight: 500;
  color: var(--app-text);
}

.logout-btn {
  margin-top: 28px;
}
</style>
