<template>
  <div class="page-shell orders-page">
    <van-nav-bar left-arrow title="我的订单" @click-left="router.back()" />

    <div class="page-inner orders-inner">
      <div v-if="loading" class="loading-box">
        <van-loading type="spinner" color="#2f7ef7" />
      </div>

      <template v-else>
        <section class="page-card order-card">
          <div class="order-head">
            <div>
              <p class="order-label">{{ loan?.status === 'INIT' ? '额度审批' : '当前订单' }}</p>
              <h1 class="order-title">{{ loan?.status === 'INIT' ? '拟授信额度' : '订单信息' }}</h1>
            </div>
            <span class="status-chip" :class="statusClass">{{ statusLabel }}</span>
          </div>

          <div class="order-amount">
            <span>¥</span>
            <strong>{{ amountText }}</strong>
          </div>

          <div class="order-notice" v-if="!loan || loan?.status === 'INIT'">
            <van-icon name="info-o" /> 上传完全部资料后将获得真实信用额度
          </div>

          <div class="order-meta">
            <div class="meta-row">
              <span>申请时间</span>
              <span>{{ createdAtText }}</span>
            </div>
            <div class="meta-row" v-if="loan?.product_name">
              <span>下单商品</span>
              <span>{{ loan.product_name }}</span>
            </div>
            <div class="meta-row" v-if="currentInstallmentText">
              <span>当前账期</span>
              <span>{{ currentInstallmentText }}</span>
            </div>
            <div class="meta-row meta-row-dates" v-if="repaymentDates.length">
              <span>还款日期</span>
              <span class="meta-date-list">
                <span v-for="item in repaymentDates" :key="item.key" class="meta-date-item">
                  {{ item.label }}
                </span>
              </span>
            </div>
            <div class="meta-row" v-if="loan?.disbursed_at">
              <span>发卡时间</span>
              <span>{{ disbursedAtText }}</span>
            </div>
            <div class="meta-row meta-row-card" v-if="loan?.has_issued_ecard">
              <span>京东E卡卡号</span>
              <span class="meta-card-value">
                {{ loan.ecard_account_masked || '--' }}
                <button class="meta-copy-btn" type="button" :disabled="copyingField === 'account'" @click="copyEcardSecret('account')">
                  复制
                </button>
              </span>
            </div>
            <div class="meta-row meta-row-card" v-if="loan?.has_issued_ecard">
              <span>京东E卡卡密</span>
              <span class="meta-card-value">
                {{ loan.ecard_password_masked || '--' }}
                <button class="meta-copy-btn" type="button" :disabled="copyingField === 'password'" @click="copyEcardSecret('password')">
                  复制
                </button>
              </span>
            </div>
            <div class="meta-row" v-if="loan?.has_issued_ecard && loan?.ecard_expires_at">
              <span>E卡有效期</span>
              <span>{{ formatDate(loan.ecard_expires_at) }}</span>
            </div>
          </div>

          <p class="order-desc">{{ statusDescription }}</p>

          <van-button block type="primary" class="primary-action order-btn" @click="handleOrderAction">
            {{ actionText }}
          </van-button>
        </section>

        <section class="page-card timeline-card">
          <h2 class="page-section-title">订单进度</h2>
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
import { getEcardSecret, getLoanStatus } from '../api';

const router = useRouter();
const loading = ref(true);
const loan = ref(null);
const copyingField = ref('');
let pollTimer = null;

const statusMap = {
  INIT: {
    label: '待申请',
    description: '当前额度为拟授信额度，完成实名认证与资料上传后即可获得真实信用额度。',
    actionText: '去申请真实额度',
    actionRoute: '/ocr',
    chipClass: 'status-chip-primary',
    amount: '8,000'
  },
  REVIEWING: {
    label: '审核中',
    description: '订单资料已提交，系统正在审核中，请稍后查看最新进度。',
    actionText: '查看审核进度',
    actionRoute: '/review',
    chipClass: 'status-chip-primary'
  },
  REJECTED: {
    label: '未通过',
    description: '当前订单资料未通过审核，请修改补充资料后重新提交。',
    actionText: '重新提交资料',
    actionRoute: '/application-form',
    chipClass: 'status-chip-danger'
  },
  APPROVED: {
    label: '待下单',
    description: '您的订单已审批通过，请在商品列表中选择组合并完成信用支付下单。',
    actionText: '立即选购',
    actionRoute: '/withdraw',
    chipClass: 'status-chip-success'
  },
  WITHDRAWING: {
    label: '待发卡',
    description: '订单已提交，后台正在从卡池分配京东E卡，请稍后刷新查看。',
    actionText: '查看账单',
    actionRoute: '/bill',
    chipClass: 'status-chip-primary'
  },
  DISBURSED: {
    label: '待付款',
    description: '订单已发卡成功，可进入账单查看付款金额与付款日期。',
    actionText: '查看账单',
    actionRoute: '/bill',
    chipClass: 'status-chip-success'
  },
  OVERDUE: {
    label: '已逾期',
    description: '当前订单已逾期，请尽快进入账单页处理还款事宜。',
    actionText: '处理还款',
    actionRoute: '/bill',
    chipClass: 'status-chip-danger'
  },
  SETTLED: {
    label: '已结清',
    description: '当前订单已完成结清，您可以返回首页查看其他服务。',
    actionText: '返回首页',
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
    return '审核中';
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
  return `第${currentPeriod}期 · 剩余待还 ${Number(loan.value?.fund_flow_summary?.remaining_amount || 0).toLocaleString('zh-CN')}元`;
});
const repaymentDates = computed(() => {
  const installments = Array.isArray(loan.value?.installments) ? loan.value.installments : [];
  if (!installments.length) {
    return loan.value?.due_date
      ? [{ key: 'repayment-final', label: formatDate(loan.value.due_date) }]
      : [];
  }

  return installments.map((item) => {
    const labelPrefix = installments.length > 1 ? `第${item.period_no}期 ` : '';
    return {
      key: `repayment-${item.period_no}`,
      label: `${labelPrefix}${formatDate(item.due_date)}`,
    };
  });
});

const timeline = computed(() => {
  const status = loan.value?.status || 'INIT';
  const steps = [
    { key: 'INIT', title: '订单创建', desc: '用户登录后生成初始订单' },
    { key: 'REVIEWING', title: '资料审核', desc: '实名认证完成后进入审核阶段' },
    { key: 'APPROVED', title: '授信审批', desc: '审批通过后可在商品页下单' },
    { key: 'DISBURSED', title: '发卡/付款', desc: '后台发卡后进入账单付款阶段' }
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
  return new Date(value).toLocaleDateString('zh-CN');
};

const formatDateTime = (value) => {
  if (!value) {
    return '--';
  }
  return new Date(value).toLocaleString('zh-CN');
};

const loadLoan = async () => {
  try {
    loan.value = await getLoanStatus();
  } finally {
    loading.value = false;
    clearPollTimer();
    pollTimer = setTimeout(loadLoan, 3000);
  }
};

const clearPollTimer = () => {
  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
};

const copyText = async (value) => {
  if (!value) {
    return false;
  }
  if (navigator?.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return true;
  }
  const textarea = document.createElement('textarea');
  textarea.value = value;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  const copied = document.execCommand('copy');
  document.body.removeChild(textarea);
  return copied;
};

const copyEcardSecret = async (field) => {
  copyingField.value = field;
  try {
    const res = await getEcardSecret(field);
    const copied = await copyText(res.value || '');
    showToast(copied ? '复制成功' : '复制失败，请手动复制');
  } catch (error) {
    // handled by interceptor
  } finally {
    copyingField.value = '';
  }
};

const handleOrderAction = () => {
  router.push(currentStatus.value.actionRoute);
};

onMounted(() => {
  loadLoan();
});

onBeforeUnmount(() => {
  clearPollTimer();
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
  background: rgba(47, 126, 247, 0.05);
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

.meta-card-value {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.meta-copy-btn {
  height: 26px;
  padding: 0 10px;
  border: 1px solid rgba(47, 126, 247, 0.24);
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
