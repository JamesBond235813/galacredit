<template>
  <div class="page-shell bill-page">
    <van-nav-bar left-arrow title="付款账单" @click-left="router.back()" />

    <div v-if="loading" class="page-inner bill-inner">
      <div class="loading-box">
        <van-loading type="spinner" color="#2f7ef7" />
      </div>
    </div>

    <div v-else class="page-inner bill-inner">
      <section v-if="loanStatus === 'WITHDRAWING'" class="page-card status-card">
        <div class="status-icon status-icon-warn">
          <van-icon name="underway" />
        </div>
        <h1 class="status-title">发卡中</h1>
        <p class="status-desc">您的订单已提交，正在为您配发京东E卡与权益确认，完成后即生成正式账单，敬请稍后。</p>
        <div class="pill-info">下单商品：{{ productName }}</div>
        <div class="detail-list status-detail-list">
          <div class="detail-item">
            <span>信用支付金额</span>
            <span>{{ formatAmount(totalAmount) }}元</span>
          </div>
        </div>
      </section>

      <section
        v-else-if="loanStatus === 'DISBURSED' || loanStatus === 'OVERDUE'"
        class="installment-section"
      >
        <section class="page-card payment-record-card" :class="{ 'payment-record-card-overdue': loanStatus === 'OVERDUE' }">
          <div class="payment-record-head">
            <div class="payment-record-head-line">
              <span class="payment-record-badge">{{ loanStatus === 'OVERDUE' ? '逾期账单' : '支付记录' }}</span>
              <h1>{{ loanStatus === 'OVERDUE' ? '账单已逾期，请尽快处理' : '信用支付已入账' }}</h1>
            </div>
            <p>
              {{ loanStatus === 'OVERDUE'
                ? '该笔信用支付账单已进入逾期状态，请尽快联系专属客服处理。'
                : '该笔订单已完成信用支付，正式账单已生成。' }}
            </p>
          </div>
          <div class="payment-record-amount">
            <span>信用支付金额</span>
            <strong>¥{{ formatAmount(totalAmount) }}</strong>
          </div>
        </section>

        <section v-if="hasIssuedEcard" class="page-card ecard-card">
          <h3>已发放京东E卡</h3>
          <div class="ecard-row">
            <span>卡号</span>
            <strong>{{ ecardAccountDisplay }}</strong>
            <van-button size="small" type="primary" plain class="copy-btn" :loading="copyingField === 'account'" @click="copyEcardSecret('account')">
              复制
            </van-button>
          </div>
          <div class="ecard-row">
            <span>卡密</span>
            <strong>{{ ecardPasswordDisplay }}</strong>
            <van-button size="small" type="primary" plain class="copy-btn" :loading="copyingField === 'password'" @click="copyEcardSecret('password')">
              复制
            </van-button>
          </div>
          <div class="ecard-row">
            <span>有效期</span>
            <strong>{{ ecardExpiresText }}</strong>
          </div>
          <p class="ecard-tip">页面仅展示脱敏卡密，复制后请妥善保管。</p>
        </section>

        <section class="page-card rights-service-card">
          <h3>权益服务信息</h3>
          <div class="rights-service-rows">
            <div class="rights-service-item">
              <span>权益内容</span>
              <p>{{ rightsContent }}</p>
            </div>
            <div class="rights-service-item">
              <span>服务商</span>
              <p>广东省韶关市丹霞山旅行社</p>
            </div>
            <div class="rights-service-item">
              <span>联系电话</span>
              <p><a href="tel:13800138000">13800138000</a></p>
            </div>
            <div class="rights-service-item">
              <span>行权提醒</span>
              <p>请联系旅行社时提供权益发放机构以及您注册时的真实身份信息。</p>
            </div>
          </div>
        </section>

        <article
          v-for="item in installmentCards"
          :key="item.key"
          class="page-card installment-card"
          :class="{
            'installment-card-overdue': item.status === 'OVERDUE',
            'installment-card-settled': item.status === 'SETTLED',
          }"
        >
          <div class="installment-body">
            <div class="installment-grid installment-grid-labels">
              <span>应还金额</span>
              <span>期数</span>
              <span>还款日</span>
            </div>

            <div class="installment-grid installment-grid-values">
              <strong :class="{ 'installment-danger': item.remainingAmount > 0 && item.status === 'OVERDUE' }">
                {{ formatAmount(item.remainingAmount) }}元
              </strong>
              <strong>第{{ item.index }}期</strong>
              <strong>{{ item.dueDateText }}</strong>
            </div>

            <van-button block type="primary" class="primary-action installment-btn" @click="onRepay(item)">
              立即还款
            </van-button>
          </div>
        </article>
      </section>

      <section v-else-if="loanStatus === 'SETTLED'" class="page-card status-card">
        <div class="status-icon status-icon-success">
          <van-icon name="passed" />
        </div>
        <h1 class="status-title">账单已结清</h1>
        <p class="status-desc">感谢您的守信，小荷包期待下次继续为您服务。</p>
        <div class="pill-info">信用支付金额：¥{{ formatAmount(totalAmount) }}</div>
        <section v-if="hasIssuedEcard" class="ecard-card settled-ecard-card">
          <h3>已发放京东E卡</h3>
          <div class="ecard-row">
            <span>卡号</span>
            <strong>{{ ecardAccountDisplay }}</strong>
            <van-button size="small" type="primary" plain class="copy-btn" :loading="copyingField === 'account'" @click="copyEcardSecret('account')">
              复制
            </van-button>
          </div>
          <div class="ecard-row">
            <span>卡密</span>
            <strong>{{ ecardPasswordDisplay }}</strong>
            <van-button size="small" type="primary" plain class="copy-btn" :loading="copyingField === 'password'" @click="copyEcardSecret('password')">
              复制
            </van-button>
          </div>
          <div class="ecard-row">
            <span>有效期</span>
            <strong>{{ ecardExpiresText }}</strong>
          </div>
        </section>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showDialog, showToast } from 'vant';
import { getEcardSecret, registerRepayAttempt } from '../api';
import { createLoanSnapshotSubscriber } from '../api/loanSocket';

const router = useRouter();
const loading = ref(true);
const loanData = ref(null);
let loanSnapshotSubscriber = null;

const loanStatus = computed(() => loanData.value?.status || '');
const totalAmount = computed(() => loanData.value?.total_repayment_amount || 0);
const productName = computed(() => loanData.value?.product_name || '未命名商品');
const hasIssuedEcard = computed(() => Boolean(loanData.value?.has_issued_ecard));
const ecardExpiresText = computed(() => formatDate(loanData.value?.ecard_expires_at));
const rightsContent = computed(() => loanData.value?.rights_desc || loanData.value?.rights_title || '权益内容以订单快照为准');
const copyingField = ref('');

const formatMaskedEcardValue = (value) => {
  const text = String(value || '').trim();
  if (!text || text === '--') {
    return '--';
  }

  const normalized = text.replace(/[^0-9A-Za-z]/g, '').toUpperCase();
  if (normalized.length >= 8) {
    const head = normalized.slice(0, 4);
    const tail = normalized.slice(-4);
    return `${head}-****-****-****-${tail}`;
  }

  return text.replace(/\*{5,}/g, '****');
};

const ecardAccountDisplay = computed(() => formatMaskedEcardValue(loanData.value?.ecard_account_masked));
const ecardPasswordDisplay = computed(() => formatMaskedEcardValue(loanData.value?.ecard_password_masked));

const formatDate = (value) => {
  if (!value) {
    return '--';
  }
  return new Date(value).toLocaleDateString('zh-CN');
};

const installmentCards = computed(() => {
  const list = Array.isArray(loanData.value?.installments) ? loanData.value.installments : [];
  return list.map((item) => ({
    key: `installment-${item.period_no}`,
    index: item.period_no,
    remainingAmount: Number(item.remaining_amount ?? item.due_amount ?? 0),
    dueAmount: Number(item.due_amount || 0),
    dueDateText: formatDate(item.due_date),
    status: item.status || 'PENDING',
    statusText: item.status === 'SETTLED'
      ? '已结清'
      : item.status === 'OVERDUE'
        ? '已逾期'
        : item.status === 'CURRENT'
          ? '待还款'
          : '待到期',
  }));
});

const formatAmount = (value) => Number(value || 0).toLocaleString('zh-CN', {
  minimumFractionDigits: Number(value || 0) % 1 === 0 ? 0 : 2,
  maximumFractionDigits: 2
});

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
    if (copied) {
      showToast('复制成功');
    } else {
      showToast('复制失败，请手动复制');
    }
  } catch (error) {
    // handled by interceptor
  } finally {
    copyingField.value = '';
  }
};

const applyLoanSnapshot = (snapshot) => {
  loanData.value = snapshot || null;
  if (['INIT', 'REVIEWING', 'APPROVED', 'REJECTED'].includes(snapshot?.status || '')) {
    router.replace('/home');
    return;
  }
  loading.value = false;
};

const onRepay = async (item = null) => {
  try {
    await registerRepayAttempt();
  } catch (error) {
    // handled by interceptor
  }
  const title = item ? `第${item.index}期还款指引` : '还款指引';
  showDialog({
    title,
    message: '请联系您的专属客服专员完成还款处理，客服确认后会在后台同步更新账单状态。',
    confirmButtonText: '我知道了',
    confirmButtonColor: '#2f7ef7',
    className: 'repay-guide-dialog'
  });
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
.bill-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: calc(env(safe-area-inset-top, 0px) + 2px) 12px 8px;
}

.loading-box {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.status-card {
  padding: 26px 20px;
}

.status-card {
  text-align: center;
}

.payment-record-card {
  padding: 14px;
  background:
    radial-gradient(circle at top right, rgba(47, 126, 247, 0.12), transparent 34%),
    linear-gradient(140deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 250, 255, 0.96) 100%);
}

.payment-record-card-overdue {
  background:
    radial-gradient(circle at top right, rgba(227, 109, 109, 0.12), transparent 34%),
    linear-gradient(140deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 246, 246, 0.96) 100%);
}

.payment-record-badge {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(47, 126, 247, 0.1);
  color: var(--app-primary-deep);
  font-size: 12px;
  font-weight: 700;
}

.payment-record-card-overdue .payment-record-badge {
  background: rgba(216, 92, 92, 0.12);
  color: #cf5555;
}

.payment-record-head h1 {
  margin: 0;
  font-size: 20px;
  line-height: 1.28;
  color: var(--app-text);
  white-space: nowrap;
}

.payment-record-head-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.payment-record-head p {
  margin: 7px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--app-text-soft);
}

.payment-record-amount {
  margin-top: 10px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(47, 126, 247, 0.14);
}

.payment-record-amount span {
  font-size: 12px;
  color: var(--app-text-soft);
  white-space: nowrap;
}

.payment-record-amount strong {
  font-size: 24px;
  line-height: 1;
  font-weight: 700;
  color: var(--app-text);
  white-space: nowrap;
}

.status-icon {
  width: 82px;
  height: 82px;
  margin: 0 auto 20px;
  border-radius: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42px;
}

.status-icon-warn {
  background: rgba(255, 155, 61, 0.12);
  color: var(--app-warning);
}

.status-icon-success {
  background: rgba(48, 215, 169, 0.14);
  color: #0daa79;
}

.status-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--app-text);
}

@media (max-width: 420px) {
  .payment-record-amount strong {
    font-size: 22px;
  }
}

.status-desc {
  margin: 12px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--app-text-soft);
}

.pill-info {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 18px;
  min-height: 38px;
  padding: 0 16px;
  border-radius: 999px;
  background: rgba(47, 126, 247, 0.08);
  color: var(--app-primary-deep);
  font-size: 14px;
  font-weight: 600;
}

.detail-list {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px dashed #dbe4f2;
}

.status-detail-list {
  width: 100%;
  margin-top: 22px;
}

.detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  font-size: 14px;
  color: var(--app-text-soft);
}

.detail-item + .detail-item {
  margin-top: 12px;
}

.detail-item span:last-child {
  color: var(--app-text);
  font-weight: 500;
}

.detail-item .detail-danger {
  color: var(--app-danger);
}

.ecard-card {
  padding: 14px;
  border: 1px solid rgba(47, 126, 247, 0.16);
  background:
    radial-gradient(circle at top right, rgba(47, 126, 247, 0.1), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(243, 249, 255, 0.96) 100%);
}

.settled-ecard-card {
  margin-top: 18px;
  text-align: left;
}

.ecard-card h3 {
  margin: 0;
  font-size: 15px;
  color: var(--app-text);
}

.ecard-row {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 70px 1fr auto;
  gap: 8px;
  align-items: center;
}

.ecard-row span {
  font-size: 12px;
  color: var(--app-text-soft);
}

.ecard-row strong {
  font-size: 13px;
  color: var(--app-text);
  letter-spacing: 0.02em;
}

.copy-btn {
  min-width: 52px;
  height: 28px;
  border-radius: 10px !important;
}

.ecard-tip {
  margin: 10px 0 0;
  font-size: 11px;
  color: var(--app-text-soft);
}

.rights-service-card {
  padding: 14px;
  border: 1px solid rgba(47, 126, 247, 0.14);
  background:
    radial-gradient(circle at top right, rgba(47, 126, 247, 0.08), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 250, 255, 0.96) 100%);
}

.rights-service-card h3 {
  margin: 0;
  font-size: 15px;
  color: var(--app-text);
}

.rights-service-rows {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.rights-service-item {
  margin-top: 0;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(47, 126, 247, 0.08);
}

.rights-service-item span {
  display: block;
  font-size: 11px;
  color: var(--app-text-soft);
}

.rights-service-item p {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--app-text);
}

.rights-service-item a {
  color: var(--app-primary-deep);
  text-decoration: none;
}

.installment-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.installment-card {
  padding: 0;
  overflow: hidden;
  border-radius: 20px;
  position: relative;
  border: 1px solid rgba(47, 126, 247, 0.18);
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 249, 255, 0.96) 100%);
  box-shadow: 0 18px 36px rgba(36, 79, 147, 0.1);
}

.installment-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--app-gradient);
  opacity: 0.92;
}

.installment-card-overdue {
  border-color: rgba(213, 101, 101, 0.22);
}

.installment-card-settled {
  border-color: rgba(52, 177, 151, 0.22);
}

.installment-body {
  position: relative;
  padding: 12px;
  background:
    radial-gradient(circle at top right, rgba(47, 126, 247, 0.08), transparent 22%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(247, 251, 255, 0.94) 100%);
}

.installment-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr 1fr;
  gap: 6px;
  align-items: center;
}

.installment-grid-labels span {
  font-size: 11px;
  color: var(--app-text-soft);
  letter-spacing: 0.04em;
}

.installment-grid-values {
  margin-top: 6px;
}

.installment-grid-values strong {
  font-size: 16px;
  color: var(--app-text);
  line-height: 1.35;
}

.installment-grid-values strong:first-child {
  font-size: 18px;
}

.installment-btn {
  margin-top: 10px;
  height: 40px;
  border-radius: 12px !important;
  box-shadow: 0 10px 18px rgba(42, 120, 227, 0.2);
}

@media (max-height: 860px) {
  .bill-inner {
    gap: 6px;
    padding: calc(env(safe-area-inset-top, 0px) + 1px) 10px 6px;
  }

  .payment-record-card,
  .ecard-card,
  .rights-service-card {
    padding: 12px;
  }

  .payment-record-head h1 {
    font-size: 18px;
  }

  .payment-record-amount strong {
    font-size: 21px;
  }

  .rights-service-rows {
    gap: 6px;
  }

  .rights-service-item {
    padding: 7px 9px;
  }

  .installment-body {
    padding: 10px;
  }

  .installment-btn {
    height: 36px;
    margin-top: 8px;
  }
}

.installment-danger {
  color: var(--app-danger) !important;
}

:global(.repay-guide-dialog.van-dialog) {
  overflow: hidden;
  border-radius: 26px;
  box-shadow: 0 24px 48px rgba(26, 63, 123, 0.22);
  background:
    radial-gradient(circle at top right, rgba(47, 126, 247, 0.08), transparent 26%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.99) 0%, rgba(246, 250, 255, 0.98) 100%);
}

:global(.repay-guide-dialog .van-dialog__header) {
  padding: 22px 20px 14px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.14), transparent 26%),
    linear-gradient(135deg, #244b87 0%, #3774e6 58%, #3ed0ba 100%);
  color: #ffffff;
  font-size: 20px;
  font-weight: 700;
}

:global(.repay-guide-dialog .van-dialog__content) {
  padding: 18px 20px 4px;
}

:global(.repay-guide-dialog .van-dialog__message) {
  font-size: 14px;
  line-height: 1.8;
  color: var(--app-text-soft);
  text-align: left;
}

:global(.repay-guide-dialog .van-dialog__footer) {
  padding: 0 16px 16px;
}

:global(.repay-guide-dialog .van-dialog__confirm) {
  height: 46px;
  border-radius: 16px;
  background: var(--app-gradient) !important;
  color: #ffffff !important;
  font-weight: 700;
}
</style>
