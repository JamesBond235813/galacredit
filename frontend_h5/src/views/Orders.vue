<template>
  <div class="page-shell orders-page">
    <van-nav-bar left-arrow title="My Applications" @click-left="router.back()" />

    <div class="page-inner orders-inner">
      <div v-if="loading" class="loading-box">
        <van-loading type="spinner" color="#ea9518" />
      </div>

      <template v-else>
        <section class="page-card order-card">
          <div class="order-head">
            <div>
              <p class="order-label">{{ loan?.status === 'INIT' ? 'Credit Application' : 'Current Loan' }}</p>
              <h1 class="order-title">{{ loan?.status === 'INIT' ? 'Estimated Credit Limit' : 'Loan Details' }}</h1>
            </div>
            <span class="status-chip" :class="statusClass">{{ statusLabel }}</span>
          </div>

          <div class="order-amount">
            <span>GHS</span>
            <strong>{{ amountText }}</strong>
          </div>

          <div class="order-notice" v-if="!loan || loan?.status === 'INIT'">
            <van-icon name="info-o" /> Complete your application to receive an approved credit limit
          </div>

          <div class="order-meta">
            <div class="meta-row">
              <span>Application Date</span>
              <span>{{ createdAtText }}</span>
            </div>
            <div class="meta-row" v-if="loan?.product_name">
              <span>Loan Option</span>
              <span>{{ loan.product_name }}</span>
            </div>
            <div class="meta-row" v-if="currentInstallmentText">
              <span>Current Instalment</span>
              <span>{{ currentInstallmentText }}</span>
            </div>
            <div class="meta-row meta-row-dates" v-if="repaymentDates.length">
              <span>Repayment Dates</span>
              <span class="meta-date-list">
                <span v-for="item in repaymentDates" :key="item.key" class="meta-date-item">
                  {{ item.label }}
                </span>
              </span>
            </div>
            <div class="meta-row" v-if="loan?.disbursed_at">
              <span>Disbursement Date</span>
              <span>{{ disbursedAtText }}</span>
            </div>
            <div v-if="loan?.has_issued_ecard" class="meta-ecard-list">
              <div v-for="item in ecardItems" :key="item.key" class="meta-ecard-item">
                <div class="meta-ecard-title">
                  <span>{{ item.title }}</span>
                  <strong v-if="item.faceValue">GHS {{ Number(item.faceValue).toLocaleString('en-GH') }}</strong>
                </div>
                <div class="meta-row meta-row-card">
                  <span>Card Number</span>
                  <span class="meta-card-value">
                    {{ item.accountDisplay }}
                    <button class="meta-copy-btn" type="button" :disabled="copyingKey === copyKey(item, 'account')" @click="copyEcardSecret('account', item)">
                      Copy
                    </button>
                  </span>
                </div>
                <div class="meta-row meta-row-card">
                  <span>Card PIN</span>
                  <span class="meta-card-value">
                    {{ item.passwordDisplay }}
                    <button class="meta-copy-btn" type="button" :disabled="copyingKey === copyKey(item, 'password')" @click="copyEcardSecret('password', item)">
                      Copy
                    </button>
                  </span>
                </div>
                <div class="meta-row" v-if="item.expiresAt">
                  <span>Expiry Date</span>
                  <span>{{ formatDate(item.expiresAt) }}</span>
                </div>
              </div>
            </div>
          </div>

          <p class="order-desc">{{ statusDescription }}</p>

          <van-button block type="primary" class="primary-action order-btn" @click="handleOrderAction">
            {{ actionText }}
          </van-button>
        </section>

        <section class="page-card timeline-card">
          <h2 class="page-section-title">Application Progress</h2>
          <div class="timeline-list">
            <div
              v-for="item in timeline"
              :key="item.key"
              class="timeline-item"
              :class="{ 'timeline-item-active': item.active }"
            >
              <span class="timeline-dot"></span>
              <div class="timeline-body">
                <p class="timeline-title">{{ item.title }}</p>
                <p class="timeline-desc">{{ item.desc }}</p>
              </div>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { getEcardSecret } from '../api';
import { createLoanSnapshotSubscriber } from '../api/loanSocket';
import { copyTextSafely } from '../utils/clipboard';
import { buildEcardDisplayItems, buildEcardSecretParams } from '../utils/ecardDisplay';

const router = useRouter();
const loading = ref(true);
const loan = ref(null);
const copyingKey = ref('');
let loanSnapshotSubscriber = null;

const statusMap = {
  INIT: {
    label: 'Not Started',
    description: 'Complete identity verification and provide the required information to receive a credit decision.',
    actionText: 'Start Application',
    actionRoute: '/ocr',
    chipClass: 'status-chip-primary',
    amount: '--'
  },
  REVIEWING: {
    label: 'Under Review',
    description: 'Your application has been submitted and is being reviewed.',
    actionText: 'View Review Status',
    actionRoute: '/review',
    chipClass: 'status-chip-primary'
  },
  REJECTED: {
    label: 'Not Approved',
    description: 'Update your information and submit the application again.',
    actionText: 'Resubmit Application',
    actionRoute: '/application-form',
    chipClass: 'status-chip-danger'
  },
  APPROVED: {
    label: 'Approved',
    description: 'Your credit application is approved. Select a loan option to continue.',
    actionText: 'Choose a Loan',
    actionRoute: '/withdraw',
    chipClass: 'status-chip-success'
  },
  WITHDRAWING: {
    label: 'Disbursing',
    description: 'Your loan is being processed for MoMo disbursement.',
    actionText: 'View Bill',
    actionRoute: '/bill',
    chipClass: 'status-chip-primary'
  },
  DISBURSED: {
    label: 'Repayment Due',
    description: 'Your loan has been disbursed. View the repayment amount and due date.',
    actionText: 'View Bill',
    actionRoute: '/bill',
    chipClass: 'status-chip-success'
  },
  OVERDUE: {
    label: 'Overdue',
    description: 'This loan is overdue. Open the bill and arrange repayment immediately.',
    actionText: 'Resolve Repayment',
    actionRoute: '/bill',
    chipClass: 'status-chip-danger'
  },
  SETTLED: {
    label: 'Settled',
    description: 'This loan has been fully repaid.',
    actionText: 'Return Home',
    actionRoute: '/home',
    chipClass: 'status-chip-success'
  }
};

const currentStatus = computed(() => statusMap[loan.value?.status] || statusMap.INIT);
const statusLabel = computed(() => currentStatus.value.label);
const statusDescription = computed(() => currentStatus.value.description);
const actionText = computed(() => currentStatus.value.actionText);
const statusClass = computed(() => currentStatus.value.chipClass);
const amountText = computed(() => {
  if (!loan.value) {
    return '0';
  }

  if (loan.value.status === 'INIT') {
    return currentStatus.value.amount;
  }

  if (loan.value.status === 'REVIEWING') {
    return 'Under review';
  }

  return Number(loan.value.product_total_price || loan.value.total_repayment_amount || loan.value.credit_limit || 0).toLocaleString();
});

const createdAtText = computed(() => formatDateTime(loan.value?.created_at));
const disbursedAtText = computed(() => formatDateTime(loan.value?.disbursed_at));
const currentInstallmentText = computed(() => {
  const currentPeriod = loan.value?.fund_flow_summary?.current_installment_period;
  if (!currentPeriod) {
    return '';
  }
  return `Instalment ${currentPeriod} · GHS ${Number(loan.value?.fund_flow_summary?.remaining_amount || 0).toLocaleString('en-GH')} remaining`;
});
const repaymentDates = computed(() => {
  const installments = Array.isArray(loan.value?.installments) ? loan.value.installments : [];
  if (!installments.length) {
    return loan.value?.due_date
      ? [{ key: 'repayment-final', label: formatDate(loan.value.due_date) }]
      : [];
  }

  return installments.map((item) => {
    const labelPrefix = installments.length > 1 ? `Instalment ${item.period_no}: ` : '';
    return {
      key: `repayment-${item.period_no}`,
      label: `${labelPrefix}${formatDate(item.due_date)}`,
    };
  });
});
const ecardItems = computed(() => buildEcardDisplayItems(loan.value));

const timeline = computed(() => {
  const status = loan.value?.status || 'INIT';
  const steps = [
    { key: 'INIT', title: 'Application Created', desc: 'Your initial credit application is ready' },
    { key: 'REVIEWING', title: 'Information Review', desc: 'Your identity and application details are being reviewed' },
    { key: 'APPROVED', title: 'Credit Approved', desc: 'Choose a loan option after approval' },
    { key: 'DISBURSED', title: 'MoMo Disbursement', desc: 'Funds are sent and the repayment bill is created' }
  ];

  const activeIndexMap = {
    INIT: 0,
    REVIEWING: 1,
    REJECTED: 1,
    APPROVED: 2,
    WITHDRAWING: 2,
    DISBURSED: 3,
    OVERDUE: 3,
    SETTLED: 3
  };

  const activeIndex = activeIndexMap[status] ?? 0;

  return steps.map((item, index) => ({
    ...item,
    active: index <= activeIndex
  }));
});

const formatDate = (value) => {
  if (!value) {
    return '';
  }
  return new Date(value).toLocaleDateString('en-GH');
};

const formatDateTime = (value) => {
  if (!value) {
    return '--';
  }
  return new Date(value).toLocaleString('en-GH');
};

const applyLoanSnapshot = (snapshot) => {
  loan.value = snapshot || null;
  loading.value = false;
};

const copyKey = (item, field) => `${field}-${item?.id ?? item?.index ?? 0}`;

const showManualCopyValue = (field, value) => {
  const label = field === 'account' ? 'card number' : 'card PIN';
  window.prompt(`Automatic copy failed. Press and hold to copy the ${label}.`, value);
};

const copyEcardSecret = async (field, item = {}) => {
  copyingKey.value = copyKey(item, field);
  try {
    const res = await getEcardSecret(field, buildEcardSecretParams(item));
    const copied = await copyTextSafely(res.value || '');
    if (copied) {
      showToast('Copied');
    } else {
      showManualCopyValue(field, res.value || '');
    }
  } catch (error) {
    // handled by interceptor
  } finally {
    copyingKey.value = '';
  }
};

const handleOrderAction = () => {
  router.push(currentStatus.value.actionRoute);
};

onMounted(() => {
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
.orders-inner {
  min-height: calc(100vh - 48px);
}

.loading-box {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.order-card,
.timeline-card {
  padding: 18px;
}

.timeline-card {
  margin-top: 16px;
}

.order-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.order-label {
  margin: 0;
  font-size: 13px;
  color: var(--app-text-faint);
}

.order-title {
  margin: 8px 0 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--app-text);
}

.order-amount {
  margin-top: 20px;
  line-height: 1;
  color: var(--app-primary-deep);
}

.order-amount span {
  font-size: 22px;
}

.order-amount strong {
  font-size: 42px;
  font-weight: 700;
}

.order-notice {
  margin-top: 14px;
  padding: 8px 12px;
  background: rgba(234, 149, 24, 0.05);
  border-radius: 8px;
  font-size: 13px;
  color: var(--app-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.order-meta {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px dashed #dbe4f2;
}

.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: var(--app-text-soft);
}

.meta-row + .meta-row {
  margin-top: 10px;
}

.meta-row-card {
  align-items: flex-start;
}

.meta-ecard-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.meta-ecard-item {
  padding: 10px;
  border: 1px solid rgba(234, 149, 24, 0.12);
  border-radius: 14px;
  background: rgba(247, 250, 255, 0.78);
}

.meta-ecard-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--app-text);
}

.meta-ecard-title strong {
  color: var(--app-primary-deep);
  font-size: 12px;
}

.meta-card-value {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.meta-copy-btn {
  height: 26px;
  padding: 0 10px;
  border: 1px solid rgba(234, 149, 24, 0.24);
  border-radius: 999px;
  background: #f5f9ff;
  color: var(--app-primary-deep);
  font-size: 12px;
}

.meta-copy-btn:disabled {
  opacity: 0.6;
}

.meta-row-dates {
  align-items: flex-start;
}

.meta-date-list {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.meta-date-item {
  display: block;
  line-height: 1.4;
}

.order-desc {
  margin: 18px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--app-text-soft);
}

.order-btn {
  margin-top: 24px;
}

.timeline-list {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-item {
  display: flex;
  gap: 12px;
  opacity: 0.55;
}

.timeline-item-active {
  opacity: 1;
}

.timeline-dot {
  position: relative;
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  margin-top: 4px;
  border-radius: 50%;
  background: #d5dfed;
}

.timeline-item-active .timeline-dot {
  background: var(--app-primary);
}

.timeline-item:not(:last-child) .timeline-dot::after {
  content: '';
  position: absolute;
  top: 14px;
  left: 50%;
  width: 2px;
  height: 34px;
  transform: translateX(-50%);
  background: #e5edf8;
}

.timeline-body {
  min-width: 0;
}

.timeline-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
}

.timeline-desc {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text-soft);
}
</style>
