<template>
  <div class="page-shell home-page">
    <div class="page-inner home-inner">
      <header class="home-header">
        <div class="brand-lockup">
          <img :src="brandLogo" class="home-brand-logo" alt="GalaCredit logo" />
          <h1 class="home-title">GalaCredit</h1>
        </div>
      </header>

      <div v-if="loading" class="loading-box">
        <van-loading type="spinner" color="#2f7ef7" />
      </div>

      <template v-else>
        <section v-if="blacklistHit || loanStatus === 'CARD_REJECTED'" class="home-hero page-card blocked-card">
          <div class="status-icon">
            <van-icon name="warning-o" />
          </div>
          <h1>{{ blacklistHit ? 'No credit is currently available' : 'This service is currently unavailable' }}</h1>
          <p>Please contact customer support for assistance.</p>
        </section>

        <template v-else>
        <section class="home-hero page-card">
          <div class="hero-content">
            <p class="hero-label">{{ limitTitle }}</p>
            <div class="hero-amount">{{ limitAmount }}</div>
          </div>

          <van-button block class="primary-action hero-btn" @click="onActionClick">
            {{ actionText }}
          </van-button>

          <div class="hero-note">
            <div class="hero-note-row">
              <span>{{ homeRateText }}</span>
              <span>{{ homeTermText }}</span>
            </div>
            <div class="hero-note-row">
              <span>Min daily interest rate</span>
              <span>Max loan period.</span>
            </div>
          </div>
        </section>

        <section class="service-section">
          <div class="panel-head">
            <div>
              <h2 class="page-section-title">More Services</h2>
            </div>
          </div>

          <div class="service-grid">
            <button type="button" class="service-card" @click="router.push('/support')">
              <span class="service-copy">
                <span class="service-name">Customer Support</span>
                <span class="service-desc">Help centre and assistance</span>
              </span>
              <span class="service-icon">
                <van-icon name="service-o" />
              </span>
            </button>

            <button type="button" class="service-card" @click="router.push('/orders')">
              <span class="service-copy">
                <span class="service-name">My Applications</span>
                <span class="service-desc">View application history</span>
              </span>
              <span class="service-icon service-icon-warm">
                <van-icon name="orders-o" />
              </span>
            </button>

            <button v-if="loanStatus === 'REVIEWING'" type="button" class="service-card" @click="router.push('/ocr')">
              <span class="service-copy">
                <span class="service-name">Update Identity</span>
                <span class="service-desc">Resubmit your identity details</span>
              </span>
              <span class="service-icon service-icon-soft">
                <van-icon name="idcard" />
              </span>
            </button>

            <button
              v-if="['DISBURSED', 'OVERDUE'].includes(loanStatus) && currentLoanId"
              type="button"
              class="service-card"
              @click="router.push({ path: '/withdraw', query: { extension_source_loan_id: String(currentLoanId) } })"
            >
              <span class="service-copy">
                <span class="service-name">Loan Extension</span>
                <span class="service-desc">Review available extension options</span>
              </span>
              <span class="service-icon service-icon-soft">
                <van-icon name="coupon-o" />
              </span>
            </button>
          </div>
        </section>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { getProducts, getUserInfo } from '../api';
import { createLoanSnapshotSubscriber } from '../api/loanSocket';
import brandLogo from '../assets/logo.svg';

const router = useRouter();
const loading = ref(true);
const loanStatus = ref('INIT');
const creditLimit = ref(0);
const homeProduct = ref(null);
const currentLoanId = ref(null);
const realNameStatus = ref('UNVERIFIED');
const blacklistHit = ref(false);
let loanSnapshotSubscriber = null;

const limitTitle = computed(() => {
  if (['INIT', 'REJECTED', 'SETTLED'].includes(loanStatus.value)) {
    return 'Estimated Credit Limit (GHS)';
  }
  if (loanStatus.value === 'REVIEWING') {
    return 'Maximum Available Credit (GHS)';
  }
  return 'Available Credit (GHS)';
});

const limitAmount = computed(() => {
  if (loanStatus.value === 'INIT') return creditLimit.value > 0 ? creditLimit.value.toLocaleString() : '--';
  if (loanStatus.value === 'REVIEWING') {
    return 'Under review';
  }
  if (loanStatus.value === 'REJECTED') {
    return 'Resubmit';
  }
  if (loanStatus.value === 'SETTLED') return creditLimit.value > 0 ? creditLimit.value.toLocaleString() : '--';
  return creditLimit.value.toLocaleString();
});

const homeRateText = computed(() => {
  const components = homeProduct.value?.fee_components;
  const rate = Number(components?.interest_rate ?? 0);
  return `${(rate * 100).toFixed(rate * 100 % 1 ? 2 : 0)}%`;
});
const homeTermText = computed(() => `${Number(homeProduct.value?.repayment_due_day || homeProduct.value?.term_days || 0)} days`);

const limitSubtitle = computed(() => {
  if (loanStatus.value === 'INIT') {
    return 'Complete the application steps to receive a credit decision.';
  }
  if (loanStatus.value === 'REJECTED') {
    return 'Your application was not approved. Update your information and try again.';
  }
  if (loanStatus.value === 'SETTLED') {
    return 'Your previous loan is settled. You may submit a new application.';
  }
  return 'Your credit, disbursement and repayment status updates automatically.';
});

const actionText = computed(() => {
  const map = {
    INIT: 'Apply Now',
    REVIEWING: 'View Review Status',
    REJECTED: 'Resubmit Application',
    APPROVED: 'Choose a Loan',
    WITHDRAWING: 'View Disbursement',
    DISBURSED: 'View Repayment Bill',
    SETTLED: 'Apply Again',
    OVERDUE: 'Resolve Overdue Bill',
    CARD_REJECTED: 'Unavailable'
  };
  return map[loanStatus.value] || 'Processing';
});

const applyLoanSnapshot = (snapshot) => {
  loanStatus.value = snapshot?.status || 'INIT';
  currentLoanId.value = snapshot?.id || null;
  creditLimit.value = snapshot?.available_credit_limit ?? snapshot?.credit_limit ?? 0;
  loading.value = false;
};

const onActionClick = () => {
  switch (loanStatus.value) {
    case 'INIT':
    case 'SETTLED':
      router.push('/ocr');
      break;
    case 'REVIEWING':
      router.push('/review');
      break;
    case 'REJECTED':
      router.push('/ocr');
      break;
    case 'APPROVED':
      router.push('/withdraw');
      break;
    default:
      router.push('/bill');
      break;
  }
};

onMounted(() => {
  Promise.all([getUserInfo(), getProducts()])
    .then(([user, products]) => {
      realNameStatus.value = user?.real_name_status || 'UNVERIFIED';
      blacklistHit.value = Boolean(user?.blacklist_hit);
      homeProduct.value = (Array.isArray(products) ? products : []).find((item) => item.product_type === 'CASH_LOAN') || null;
    })
    .catch(() => {
      realNameStatus.value = 'UNVERIFIED';
    });
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
.home-page {
  min-height: calc(100dvh - 88px);
}

.home-inner {
  padding-top: calc(env(safe-area-inset-top, 0px) + 20px);
}

.home-header {
  margin-bottom: 18px;
}

.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 9px;
}

.home-brand-logo {
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
}

.home-title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: var(--app-text);
}

.loading-box {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}

.home-hero {
  padding: 18px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.22), transparent 34%),
    linear-gradient(135deg, rgba(44, 95, 183, 0.94) 0%, rgba(47, 126, 247, 0.92) 58%, rgba(48, 215, 169, 0.84) 100%);
  color: #ffffff;
}

.blocked-card {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
}

.blocked-card h1 {
  margin: 0;
  font-size: 22px;
}

.blocked-card p {
  margin: 0;
  color: rgba(255, 255, 255, 0.86);
}

.hero-content {
  padding: 20px 6px 28px;
  text-align: center;
}

.hero-label {
  margin: 0 0 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.84);
}

.hero-amount {
  font-size: 46px;
  line-height: 1;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.hero-btn {
  background: #ffffff !important;
  color: var(--app-primary-deep) !important;
  box-shadow: 0 12px 28px rgba(16, 43, 88, 0.16);
}

.hero-note {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 14px 4px 0;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.84);
}

.hero-note-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  text-align: left;
}

.service-section {
  margin-top: 18px;
}

.service-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-top: 18px;
}

.service-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 106px;
  padding: 16px;
  border: 1px solid #e8eef8;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: var(--app-shadow);
  color: inherit;
  text-align: left;
}

.service-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.service-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  border-radius: 50%;
  background: rgba(47, 126, 247, 0.1);
  color: var(--app-primary-deep);
  font-size: 22px;
}

.service-icon-warm {
  background: rgba(255, 155, 61, 0.12);
  color: var(--app-warning);
}

.service-icon-soft {
  background: rgba(48, 215, 169, 0.14);
  color: #0c9f7b;
}

.service-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}

.service-desc {
  font-size: 13px;
  line-height: 1.6;
  color: var(--app-text-soft);
}
</style>
