<template>
  <div class="page-shell review-page">
    <van-nav-bar title="Application Review" />

    <div class="page-inner review-inner">
      <section v-if="loading" class="page-card review-loading-card">
        <div class="loading-orbit">
          <van-loading type="spinner" color="#ea9518" size="56px" />
        </div>
        <h2 class="review-title">Application Under Review</h2>
        <p class="review-desc">
          We are reviewing your information and determining your available credit limit.
        </p>
      </section>

      <template v-else-if="loanStatus === 'APPROVED'">
        <section class="page-card approval-card">
          <span class="approval-badge">Decision</span>
          <div class="approval-summary-grid">
            <article class="approval-summary-item">
              <span>Status</span>
              <strong>Approved</strong>
            </article>
            <article class="approval-summary-item">
              <span>Valid For</span>
              <strong>30 Days</strong>
            </article>
            <article class="approval-summary-item">
              <span>Credit Limit</span>
              <strong>GHS {{ formatAmount(creditLimit) }}</strong>
            </article>
          </div>
          <p class="approval-note">This is your approved credit limit. Borrow responsibly.</p>
        </section>

        <section v-if="recommendedProduct" class="page-card product-item-card">
          <button type="button" class="product-item-shell" @click="openProductDetail(recommendedProduct.id)">
            <div class="product-item-head">
              <h3 class="product-item-title">{{ recommendedProduct.name }}</h3>
              <div class="product-item-price-wrap">
                <span class="product-item-price-label">Loan Amount</span>
                <strong class="product-item-price">GHS {{ formatAmount(recommendedProduct.payment_amount) }}</strong>
              </div>
            </div>
            <p class="product-item-subtitle">{{ recommendedProduct.product_type === 'CASH_LOAN' ? 'Ghana short-term cash loan' : (recommendedProduct.rights_title || 'Service package') }}</p>
            <div class="product-item-tags">
                <span>Cash Received: GHS {{ formatAmount(recommendedProduct.product_type === 'CASH_LOAN' ? (recommendedProduct.actual_disbursement_amount || (recommendedProduct.nominal_loan_amount - recommendedProduct.upfront_fee_amount)) : recommendedProduct.ecard_face_value) }}</span>
              <span>Term: {{ recommendedProduct.term_days }} days</span>
              <span>Upfront Fees: {{ formatAmount(recommendedProduct.upfront_fee_rate * 100) }}%</span>
            </div>
            <div class="product-item-rights">
              <p class="rights-caption">Repayment</p>
              <p class="rights-content">{{ recommendedProduct.product_type === 'CASH_LOAN' ? `Due on day ${recommendedProduct.repayment_due_day}, paid in ${recommendedProduct.installment_count} instalment(s)` : (recommendedProduct.rights_desc || 'Details are saved with your application') }}</p>
            </div>
            <div class="product-item-action">
              <span>View and Apply</span>
            </div>
          </button>
        </section>

        <section v-if="otherProducts.length" class="other-list">
          <article
            v-for="item in otherProducts"
            :key="item.id"
            class="page-card product-item-card"
          >
            <button type="button" class="product-item-shell" @click="openProductDetail(item.id)">
              <div class="product-item-head">
                <h3 class="product-item-title">{{ item.name }}</h3>
                <div class="product-item-price-wrap">
                  <span class="product-item-price-label">Loan Amount</span>
                  <strong class="product-item-price">GHS {{ formatAmount(item.payment_amount) }}</strong>
                </div>
              </div>
              <p class="product-item-subtitle">{{ item.product_type === 'CASH_LOAN' ? 'Ghana short-term cash loan' : (item.rights_title || 'Service package') }}</p>
              <div class="product-item-tags">
                <span>Cash Received: GHS {{ formatAmount(item.product_type === 'CASH_LOAN' ? (item.actual_disbursement_amount || (item.nominal_loan_amount - item.upfront_fee_amount)) : item.ecard_face_value) }}</span>
                <span>Term: {{ item.term_days }} days</span>
                <span>Upfront Fees: {{ formatAmount(item.upfront_fee_rate * 100) }}%</span>
              </div>
              <div class="product-item-rights">
                <p class="rights-caption">Repayment</p>
                <p class="rights-content">{{ item.product_type === 'CASH_LOAN' ? `Due on day ${item.repayment_due_day}, paid in ${item.installment_count} instalment(s)` : (item.rights_desc || 'Details are saved with your application') }}</p>
              </div>
              <div class="product-item-action">
                <span>View and Apply</span>
              </div>
            </button>
          </article>
        </section>
      </template>

      <section v-else-if="loanStatus === 'REJECTED'" class="page-card reject-card">
        <div class="reject-head">
          <h2 class="review-title">Application Not Approved</h2>
          <span class="reject-order">Application {{ loanOrderNo }}</span>
        </div>
        <p class="review-desc">{{ rejectReason }}</p>

        <div class="reject-grid">
          <article class="reject-item">
            <span>Decision</span>
            <strong>Not Approved</strong>
          </article>
          <article class="reject-item">
            <span>Next Step</span>
            <strong>Update and Resubmit</strong>
          </article>
          <article class="reject-item reject-item-wide">
            <span>Review Note</span>
            <strong>{{ rejectReason }}</strong>
          </article>
        </div>

        <van-button
          block
          type="primary"
          class="primary-action reject-action-btn"
          @click="router.replace('/application-form')"
        >
          Resubmit Application
        </van-button>
      </section>

      <section v-else class="page-card review-loading-card">
        <div class="loading-orbit">
          <van-loading type="spinner" color="#ea9518" size="48px" />
        </div>
        <h2 class="review-title">Updating Status</h2>
        <p class="review-desc">Loading the latest application status.</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { getProducts } from '../api';
import { createLoanSnapshotSubscriber } from '../api/loanSocket';

const router = useRouter();
const loading = ref(true);
const loanData = ref(null);
const products = ref([]);
let loanSnapshotSubscriber = null;
let loadedProductsLoanId = null;

const loanStatus = computed(() => loanData.value?.status || 'REVIEWING');
const creditLimit = computed(() => Number(loanData.value?.available_credit_limit ?? loanData.value?.approved_credit_limit ?? loanData.value?.credit_limit ?? 0));
const recommendedProduct = computed(() => {
  if (!products.value.length) {
    return null;
  }
  const matched = products.value.find(
    (item) => Number(item.payment_amount || 0) <= creditLimit.value + 1e-6
  );
  return matched || products.value[0];
});
const otherProducts = computed(() => {
  if (!recommendedProduct.value) {
    return [];
  }
  return products.value.filter((item) => item.id !== recommendedProduct.value.id);
});
const loanOrderNo = computed(() => {
  if (!loanData.value?.id) {
    return '--';
  }
  return String(loanData.value.id).padStart(6, '0');
});
const rejectReason = computed(() => loanData.value?.review_note || 'Your application was not approved. Review your information and submit again.');

const formatAmount = (value) => Number(value || 0).toLocaleString('en-GH', {
  minimumFractionDigits: Number(value || 0) % 1 === 0 ? 0 : 2,
  maximumFractionDigits: 2
});

const loadProducts = async () => {
  try {
    const list = await getProducts();
    products.value = Array.isArray(list) ? list : [];
  } catch (error) {
    products.value = [];
  }
};

const routeByStatus = (status) => {
  if (status === 'INIT') {
    router.replace('/application-form');
    return true;
  }
  if (status === 'WITHDRAWING' || status === 'DISBURSED' || status === 'OVERDUE') {
    router.replace('/bill');
    return true;
  }
  if (status === 'SETTLED') {
    router.replace('/home');
    return true;
  }
  return false;
};

const applyLoanSnapshot = async (snapshot) => {
  loanData.value = snapshot || null;
  const currentStatus = snapshot?.status || 'REVIEWING';
  if (routeByStatus(currentStatus)) {
    return;
  }

  if (currentStatus === 'APPROVED' && loadedProductsLoanId !== snapshot?.id) {
    loadedProductsLoanId = snapshot?.id || null;
    await loadProducts();
  }
  loading.value = currentStatus === 'REVIEWING';
};

const openProductDetail = (productId) => {
  if (!productId) {
    return;
  }
  router.push({
    path: '/withdraw',
    query: { product_id: String(productId) }
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
.review-inner {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: calc(100vh - 48px);
  padding-top: calc(env(safe-area-inset-top, 0px) + 8px);
  padding-bottom: 14px;
}

.review-loading-card,
.approval-card,
.product-item-card,
.reject-card {
  padding: 18px 15px;
}

.review-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: var(--app-text);
}

.review-desc {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--app-text-soft);
}

.review-loading-card {
  text-align: center;
}

.loading-orbit {
  width: 78px;
  height: 78px;
  margin: 2px auto 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
}

.approval-card {
  border-radius: 18px;
  border: 1px solid #dbe7fb;
  background: linear-gradient(180deg, #f8fbff 0%, #f4f8ff 100%);
  box-shadow: 0 8px 22px rgba(31, 77, 162, 0.08);
}

.approval-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 12px;
  border-radius: 999px;
  background: #e9f1ff;
  color: var(--app-primary-deep);
  font-size: 13px;
  font-weight: 600;
}

.approval-summary-grid {
  margin-top: 16px;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.approval-summary-item {
  padding: 12px 10px;
  border-radius: 14px;
  border: 1px solid #cfe0fb;
  background: #ffffff;
  text-align: center;
}

.approval-summary-item span {
  display: block;
  font-size: 12px;
  color: var(--app-text-soft);
}

.approval-summary-item strong {
  display: block;
  margin-top: 7px;
  font-size: 20px;
  line-height: 1.2;
  font-weight: 700;
  color: var(--app-primary-deep);
}

.approval-note {
  margin: 10px 2px 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--app-text-soft);
}

.product-item-card {
  padding: 0;
  border: 1px solid #d6e4fa;
  border-radius: 18px;
  min-height: 190px;
  background: linear-gradient(180deg, #f8fbff 0%, #f5f9ff 100%);
  box-shadow: 0 8px 20px rgba(35, 82, 166, 0.07);
}

.product-item-shell {
  width: 100%;
  min-height: 190px;
  padding: 15px;
  text-align: left;
  background: transparent;
}

.product-item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.product-item-title {
  margin: 0;
  flex: 1;
  font-size: 17px;
  line-height: 1.35;
  font-weight: 700;
  letter-spacing: 0.1px;
  color: var(--app-text);
}

.product-item-price-wrap {
  text-align: right;
  flex-shrink: 0;
}

.product-item-price-label {
  display: block;
  font-size: 11px;
  color: var(--app-text-soft);
}

.product-item-price {
  display: block;
  margin-top: 3px;
  font-size: 44px;
  line-height: 1;
  color: var(--app-primary-deep);
  font-weight: 700;
  letter-spacing: 0.2px;
}

.product-item-subtitle {
  margin: 11px 0 0;
  font-size: 15px;
  line-height: 1.35;
  color: var(--app-text-soft);
  font-weight: 600;
}

.product-item-tags {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.product-item-tags span {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 11px;
  border-radius: 999px;
  background: #edf3ff;
  color: var(--app-primary-deep);
  font-size: 12px;
  border: 1px solid #dbe7fb;
  white-space: nowrap;
}

.product-item-rights {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #ccdcf8;
  background: #ffffff;
}

.product-item-action {
  margin-top: 12px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--app-gradient);
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.rights-caption {
  margin: 0;
  font-size: 12px;
  color: var(--app-text-faint);
}

.rights-content {
  margin: 5px 0 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--app-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.other-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.reject-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.reject-order {
  font-size: 12px;
  color: var(--app-text-faint);
}

.reject-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.reject-item {
  padding: 11px 12px 10px;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(246, 249, 255, 0.88) 100%);
  border: 1px solid rgba(214, 226, 244, 0.92);
}

.reject-item-wide {
  grid-column: 1 / -1;
}

.reject-item span {
  display: block;
  font-size: 11px;
  color: var(--app-text-soft);
}

.reject-item strong {
  display: block;
  margin-top: 6px;
  font-size: 15px;
  color: var(--app-text);
  font-weight: 700;
}

.reject-action-btn {
  margin-top: 12px;
  height: 46px;
  border-radius: 12px !important;
}
</style>
