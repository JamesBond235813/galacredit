<template>
  <div class="page-shell home-page">
    <div class="page-inner home-inner">
      <header class="home-header">
        <div>
          <p class="home-eyebrow">授信服务</p>
          <h1 class="home-title">小荷包</h1>
        </div>
      </header>

      <div v-if="loading" class="loading-box">
        <van-loading type="spinner" color="#2f7ef7" />
      </div>

      <template v-else>
        <section class="home-hero page-card">
          <div class="hero-tags">
            <span class="hero-tag"><van-icon name="gift-o" /> 京东E卡</span>
            <span class="hero-tag"><van-icon name="passed" /> 信用支付</span>
            <span class="hero-tag"><van-icon name="flag-o" /> 旅游权益</span>
          </div>

          <div class="hero-content">
            <p class="hero-label">{{ limitTitle }}</p>
            <div class="hero-amount">{{ limitAmount }}</div>
            <p class="hero-rate" v-if="['INIT', 'REJECTED', 'SETTLED'].includes(loanStatus)">
              <van-icon name="info-o" style="margin-right: 2px" /> 上传完全部资料后将获得真实信用额度
            </p>
            <p class="hero-rate" v-else>先享后付 · 商品总价按账期生成付款账单</p>
          </div>

          <van-button block class="primary-action hero-btn" @click="onActionClick">
            {{ actionText }}
          </van-button>

          <p class="hero-note">{{ limitSubtitle }}</p>
        </section>

        <section class="service-section">
          <div class="panel-head">
            <div>
              <h2 class="page-section-title">更多服务</h2>
            </div>
          </div>

          <div class="service-grid">
            <button type="button" class="service-card" @click="router.push('/support')">
              <span class="service-copy">
                <span class="service-name">客服帮助</span>
                <span class="service-desc">客服中心与在线客服</span>
              </span>
              <span class="service-icon">
                <van-icon name="service-o" />
              </span>
            </button>

            <button type="button" class="service-card" @click="router.push('/orders')">
              <span class="service-copy">
                <span class="service-name">我的订单</span>
                <span class="service-desc">历史申请订单信息</span>
              </span>
              <span class="service-icon service-icon-warm">
                <van-icon name="orders-o" />
              </span>
            </button>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { createLoanSnapshotSubscriber } from '../api/loanSocket';

const router = useRouter();
const loading = ref(true);
const loanStatus = ref('INIT');
const creditLimit = ref(0);
let loanSnapshotSubscriber = null;

const limitTitle = computed(() => {
  if (['INIT', 'REJECTED', 'SETTLED'].includes(loanStatus.value)) {
    return '拟授信额度（元）';
  }
  if (loanStatus.value === 'REVIEWING') {
    return '最高可用信用额度（元）';
  }
  return '当前可用额度（元）';
});

const limitAmount = computed(() => {
  if (loanStatus.value === 'INIT') {
    return '8,000';
  }
  if (loanStatus.value === 'REVIEWING') {
    return '审核中';
  }
  if (loanStatus.value === 'REJECTED') {
    return '重新提交';
  }
  if (loanStatus.value === 'SETTLED') {
    return '8,000';
  }
  return creditLimit.value.toLocaleString();
});

const limitSubtitle = computed(() => {
  if (loanStatus.value === 'INIT') {
    return '仅需 3 步完成授信申请，审批后即可在商品列表进行信用下单。';
  }
  if (loanStatus.value === 'REJECTED') {
    return '当前资料未通过审核，可修改补充资料后重新提交。';
  }
  if (loanStatus.value === 'SETTLED') {
    return '上一笔订单已结清，可重新发起新一轮授信申请。';
  }
  return '页面会实时同步您的额度、下单、发卡与账单状态。';
});

const actionText = computed(() => {
  const map = {
    INIT: '立即申请',
    REVIEWING: '查看审核进度',
    REJECTED: '重新提交资料',
    APPROVED: '立即选购',
    WITHDRAWING: '待发卡进度',
    DISBURSED: '我的账单',
    SETTLED: '立即申请',
    OVERDUE: '处理逾期账单'
  };
  return map[loanStatus.value] || '处理中';
});

const applyLoanSnapshot = (snapshot) => {
  loanStatus.value = snapshot?.status || 'INIT';
  creditLimit.value = snapshot?.credit_limit || 0;
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
      router.push('/application-form');
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
  min-height: calc(100vh - 88px);
}

.home-inner {
  padding-top: calc(env(safe-area-inset-top, 0px) + 20px);
}

.home-header {
  margin-bottom: 18px;
}

.home-eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--app-text-faint);
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

.hero-tags {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 12px;
}

.hero-content {
  padding: 28px 6px 22px;
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

.hero-rate {
  margin: 12px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.76);
}

.hero-btn {
  background: #ffffff !important;
  color: var(--app-primary-deep) !important;
  box-shadow: 0 12px 28px rgba(16, 43, 88, 0.16);
}

.hero-note {
  margin: 14px 0 0;
  text-align: center;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.84);
}

.service-section {
  margin-top: 18px;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
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
