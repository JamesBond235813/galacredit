<template>
  <div class="page-shell about-page">
    <van-nav-bar title="About Us" left-arrow @click-left="router.back()" />

    <div class="about-content">
      <section class="about-card page-card brand-card">
        <div class="brand-header">
          <img :src="brandLogo" class="brand-logo" alt="GalaCredit logo" />
          <h1 class="brand-title">GalaCredit</h1>
        </div>
        <p class="brand-desc">
          GalaCredit provides eligible customers with cash loan applications, MoMo disbursement and repayment bill services.
        </p>
      </section>

      <section class="about-card page-card info-card">
        <div class="info-row">
          <span class="info-label">Service</span>
          <span class="info-value">Credit applications and repayment information</span>
        </div>
        <div class="info-row">
          <span class="info-label">Support Hours</span>
          <span class="info-value">Weekdays, 09:00 - 18:00</span>
        </div>
        <div class="info-row">
          <span class="info-label">Security Notice</span>
          <span class="info-value">Never transfer funds to a private account</span>
        </div>
      </section>

      <van-button block class="primary-action logout-btn" @click="handleLogout">
        Sign Out
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { logout } from '../api';
import brandLogo from '../assets/logo.svg';

const router = useRouter();

const handleLogout = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  try {
    if (refreshToken) {
      await logout({ refresh_token: refreshToken });
    }
  } catch (error) {
    // Always clear local authentication so the customer cannot remain in a stale session.
  } finally {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    router.replace('/login');
  }
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
