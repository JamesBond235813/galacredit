<template>
  <div class="page-shell detail-page">
    <van-nav-bar left-arrow title="Loan Application" @click-left="router.back()" />

    <div class="page-inner detail-inner">
      <div v-if="loading" class="loading-box">
        <van-loading type="spinner" color="#2f7ef7" />
      </div>

      <template v-else>
        <section class="credit-card page-card">
          <p class="credit-label">Available Credit</p>
          <div class="credit-value">
            <span>GHS</span>
            <strong>{{ formatAmount(approvedLimit) }}</strong>
          </div>
          <p class="credit-tip">No payment is required to apply. Approved funds will be sent to your MoMo wallet.</p>
        </section>

        <section v-if="discountAmount > 0" class="coupon-card page-card">
          <div>
            <strong>GHS {{ formatAmount(discountAmount) }} discount</strong>
            <p>Fees are deducted once before disbursement. Your cash received is shown before confirmation.</p>
          </div>
          <van-checkbox v-model="useDiscount" checked-color="#2f7ef7">Apply</van-checkbox>
        </section>

        <section class="product-card page-card" v-if="selectedProduct">
          <div class="product-card-head">
            <h2 class="page-section-title">Available Loan</h2>
              <span>{{ selectedProduct.product_type === 'CASH_LOAN' ? 'Ghana short-term cash loan' : (selectedProduct.ecard_face_value > 0 ? 'Legacy E-card service' : 'Service package') }}</span>
          </div>

          <article class="product-showcase">
            <div class="showcase-top">
              <div class="showcase-title-block">
                <h3>{{ selectedProduct.name }}</h3>
                <p>{{ selectedProduct.product_type === 'CASH_LOAN' ? 'MoMo cash disbursement' : (selectedProduct.rights_title || 'Service package') }}</p>
              </div>
              <div class="showcase-price">
                <span>Loan Amount</span>
                <strong>GHS {{ formatAmount(displayPaymentAmount) }}</strong>
              </div>
            </div>

            <div class="showcase-tags">
              <span>{{ selectedProduct.product_type === 'CASH_LOAN' ? `Cash received: GHS ${formatAmount(selectedProduct.nominal_loan_amount * (1 - selectedProduct.upfront_fee_rate))}` : (selectedProduct.ecard_face_value > 0 ? `Value: GHS ${formatAmount(selectedProduct.ecard_face_value)}` : 'No cash disbursement') }}</span>
              <span>Term: {{ selectedProduct.term_days }} days</span>
              <span>Uses your available credit limit</span>
            </div>

            <div class="showcase-benefits">
              <div class="benefits-head">
                <div class="benefits-label">Loan Details</div>
                <button type="button" class="benefits-detail-btn" @click.stop="openRightsDialog">View Details</button>
              </div>
              <p>{{ selectedProduct.rights_desc || 'The terms shown at confirmation will be saved with your application.' }}</p>
            </div>
          </article>
        </section>

        <section class="other-products-card page-card" v-if="otherProducts.length">
          <div class="other-head">
            <h3>Other Options</h3>
            <span>Tap to view</span>
          </div>

          <div class="other-grid">
            <button
              v-for="item in otherProducts"
              :key="item.id"
              type="button"
              class="other-item"
              @click="openProductDetail(item.id)"
            >
              <p class="other-item-title">{{ item.name }}</p>
              <div class="other-item-meta">
                <span>Amount GHS {{ formatAmount(item.payment_amount || item.ecard_face_value) }}</span>
                <strong>GHS {{ formatAmount(item.payment_amount) }}</strong>
              </div>
            </button>
          </div>
        </section>

        <div class="order-footer">
          <div v-if="smsPanelVisible" class="sms-verify-box">
            <van-field
              v-model="smsCode"
              label="Verification Code"
              placeholder="Enter the 6-digit code"
              maxlength="6"
              type="digit"
            />
            <div class="sms-verify-actions">
              <van-button
                type="primary"
                size="small"
                class="primary-action sms-confirm-btn"
                :disabled="!isSmsCodeValid || submitting"
                :loading="submitting"
                @click="handleConfirmOrder"
              >
                Confirm Application
              </van-button>
              <van-button
                plain
                size="small"
                class="sms-resend-btn"
                :disabled="smsResendDisabled"
                :loading="smsSending"
                @click="handleResendSmsCode"
              >
                {{ resendButtonText }}
              </van-button>
            </div>
          </div>
          <van-button
            v-if="!smsPanelVisible"
            block
            type="primary"
            class="primary-action order-btn"
            :disabled="!selectedProductId || !contractAgreed"
            :loading="submitting"
            @click="handleOrderAction"
          >
          Submit Loan Application
          </van-button>
          <button
            v-if="!smsPanelVisible"
            type="button"
            class="contract-consent"
            :class="{ checked: contractAgreed }"
            @click="openContractDialog"
          >
            <span class="contract-checkbox">{{ contractAgreed ? '✓' : '' }}</span>
            <span>I have read and agree to the GalaCredit Loan Agreement</span>
          </button>
          <p class="order-tip">After approval, funds will be sent by MoMo and your repayment schedule will be created.</p>
        </div>
      </template>
    </div>

    <van-popup
      v-model:show="rightsDialogVisible"
      round
      position="bottom"
      class="rights-dialog"
      :close-on-click-overlay="true"
      @closed="resetRightsDialog"
    >
      <div class="rights-dialog-inner">
        <div class="rights-dialog-header">
          <h3 class="rights-dialog-title">Loan Details</h3>
          <button type="button" class="rights-close-btn" @click="rightsDialogVisible = false">Close</button>
        </div>

        <div class="rights-dialog-scroll">
          <div class="rights-provider">
            <p>Support phone: {{ rightsDetail.contact_phone || 'Not available' }}</p>
          </div>

          <div v-for="(section, index) in rightsSections" :key="index" class="rights-section">
            <h4>{{ section.title }}</h4>
            <div :class="['rights-image-grid', { 'rights-image-grid-single': section.images.length === 1 }]">
              <img
                v-for="(image, imageIndex) in section.images"
                :key="imageIndex"
                :src="image"
                :alt="`${section.title}-${imageIndex + 1}`"
              >
            </div>
            <p v-if="section.desc" class="rights-section-desc">{{ section.desc }}</p>
          </div>

          <div v-if="!rightsSections.length" class="rights-empty">
            <p>No additional information is available for this option.</p>
          </div>
        </div>

        <div class="rights-dialog-footer">
          <van-button
            block
            type="primary"
            class="primary-action rights-confirm-btn"
            :disabled="readCountdown > 0"
            @click="confirmRightsRead"
          >
            {{ readCountdown > 0 ? `Available in ${readCountdown}s` : 'I Have Read and Understood' }}
          </van-button>
        </div>
      </div>
    </van-popup>

    <van-popup
      v-model:show="contractDialogVisible"
      round
      position="bottom"
      class="contract-dialog"
      :close-on-click-overlay="false"
      @closed="resetContractDialog"
    >
      <div class="contract-dialog-inner">
        <div class="contract-dialog-header">
          <h3 class="contract-dialog-title">GalaCredit Loan Agreement</h3>
          <button type="button" class="rights-close-btn" @click="contractDialogVisible = false">Close</button>
        </div>

        <div ref="contractScrollRef" class="contract-dialog-scroll" @scroll="handleContractScroll">
          <van-loading v-if="contractLoading" type="spinner" color="#2f7ef7" />
          <div v-else class="contract-content" v-html="contractContent"></div>
        </div>

        <div class="contract-dialog-footer">
          <p class="contract-read-tip">
            {{ contractScrolledToBottom ? 'You have reached the end. You may accept or decline.' : 'Scroll to the end and read the full agreement.' }}
          </p>
          <van-checkbox v-model="contractCarefulRead" :disabled="!contractScrolledToBottom" checked-color="#2f7ef7">
            I have read and agree to all terms of this agreement
          </van-checkbox>
          <div class="contract-actions">
            <van-button plain class="contract-reject-btn" @click="rejectContract">Decline</van-button>
            <van-button
              type="primary"
              class="primary-action contract-agree-btn"
              :disabled="!contractScrolledToBottom || !contractCarefulRead"
              :loading="contractSigning"
              @click="agreeContract"
            >
              Accept
            </van-button>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { showToast } from 'vant';
import { getLoanStatus, getProducts, previewPurchaseContract, sendOrderSmsCode, signPurchaseContract, withdraw } from '../api';
import { getOrderSmsResendText, isOrderSmsCodeValid, isOrderSmsResendDisabled } from '../utils/orderSms';

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const rightsDialogVisible = ref(false);
const contractDialogVisible = ref(false);
const contractLoading = ref(false);
const contractSigning = ref(false);
const contractScrolledToBottom = ref(false);
const contractCarefulRead = ref(false);
const contractAgreed = ref(false);
const contractContent = ref('');
const contractSignatureId = ref(null);
const contractScrollRef = ref(null);
const readCountdown = ref(5);
const hasConfirmedRights = ref(false);
const submitting = ref(false);
const smsSending = ref(false);
const approvedLimit = ref(0);
const extensionSourceLoanId = computed(() => {
  const value = Number(route.query.extension_source_loan_id || 0);
  return Number.isInteger(value) && value > 0 ? value : null;
});
const products = ref([]);
const selectedProductId = ref(null);
const smsPanelVisible = ref(false);
const smsCode = ref('');
const smsCooldown = ref(0);
const discountAmount = ref(0);
const useDiscount = ref(true);
let readTimer = null;
let smsCooldownTimer = null;

const formatAmount = (value) => Number(value || 0).toLocaleString('en-GH', {
  minimumFractionDigits: Number(value || 0) % 1 === 0 ? 0 : 2,
  maximumFractionDigits: 2
});

const parseProductId = (value) => {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null;
  }
  return parsed;
};

const syncSelectedProduct = () => {
  if (!products.value.length) {
    selectedProductId.value = null;
    return;
  }

  const queryId = parseProductId(route.query.product_id);
  const exists = queryId && products.value.some((item) => item.id === queryId);
  selectedProductId.value = exists ? queryId : products.value[0].id;
};

const selectedProduct = computed(() => {
  if (!products.value.length) {
    return null;
  }
  const matched = products.value.find((item) => item.id === selectedProductId.value);
  return matched || products.value[0];
});

const displayPaymentAmount = computed(() => {
  const product = selectedProduct.value;
  if (!product) {
    return 0;
  }
  const discount = useDiscount.value ? Math.min(Number(discountAmount.value || 0), Number(product.rights_price || 0)) : 0;
  return Math.max(Number(product.payment_amount || 0) - discount, 0);
});

const contractPayload = () => ({
  product_id: selectedProductId.value,
  use_discount: useDiscount.value,
  extension_source_loan_id: extensionSourceLoanId.value || undefined
});

const otherProducts = computed(() =>
  products.value.filter((item) => item.id !== selectedProductId.value)
);

const defaultRightsDetail = {
  contact_phone: '13800138000',
  sections: [
    {
      title: 'Loan information',
      images: [
        'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80',
        'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80'
      ],
      desc: 'Review the loan amount, upfront fees, cash received and repayment schedule before applying.'
    },
    {
      title: 'MoMo disbursement',
      images: [
        'https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=900&q=80',
        'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=900&q=80'
      ],
      desc: 'Approved funds are sent to the mobile money account linked to your registered number.'
    },
    {
      title: 'Repayment',
      images: [
        'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80'
      ],
      desc: 'Repayments must be made according to the schedule shown in your bill.'
    }
  ]
};

const rightsDetail = computed(() => selectedProduct.value?.rights_detail || defaultRightsDetail);
const rightsSections = computed(() => {
  const sections = Array.isArray(rightsDetail.value?.sections) ? rightsDetail.value.sections : [];
  return sections
    .map((section) => ({
      title: section?.title || 'Loan information',
      images: Array.isArray(section?.images) ? section.images.filter(Boolean) : [],
      desc: section?.desc || ''
    }))
    .filter((section) => section.title || section.images.length || section.desc);
});

const initData = async () => {
  try {
    const loan = await getLoanStatus();
    if (loan.status !== 'APPROVED' && !extensionSourceLoanId.value) {
      showToast('A loan application cannot be submitted in the current status');
      router.replace(
        loan.status === 'WITHDRAWING' || loan.status === 'DISBURSED' || loan.status === 'OVERDUE'
          ? '/bill'
          : '/home'
      );
      return;
    }
    approvedLimit.value = Number(loan.available_credit_limit || loan.approved_credit_limit || loan.credit_limit || 0);
    discountAmount.value = Number(loan.approval_discount_amount || 0);

    const list = await getProducts(extensionSourceLoanId.value ? { extension_source_loan_id: extensionSourceLoanId.value } : undefined);
    products.value = Array.isArray(list) ? list : [];
    syncSelectedProduct();
  } catch (error) {
    // handled by interceptor
  } finally {
    loading.value = false;
  }
};

const openProductDetail = (productId) => {
  if (!productId) {
    return;
  }
  selectedProductId.value = productId;
  if (String(route.query.product_id || '') === String(productId)) {
    return;
  }
  router.push({
    path: '/withdraw',
    query: { product_id: String(productId) }
  });
};

const clearReadTimer = () => {
  if (readTimer) {
    clearInterval(readTimer);
    readTimer = null;
  }
};

const openRightsDialog = () => {
  rightsDialogVisible.value = true;
  readCountdown.value = 5;
  clearReadTimer();
  readTimer = setInterval(() => {
    if (readCountdown.value <= 1) {
      readCountdown.value = 0;
      clearReadTimer();
      return;
    }
    readCountdown.value -= 1;
  }, 1000);
};

const resetContractState = () => {
  contractAgreed.value = false;
  contractSignatureId.value = null;
  contractContent.value = '';
  contractCarefulRead.value = false;
  contractScrolledToBottom.value = false;
};

const handleContractScroll = () => {
  const el = contractScrollRef.value;
  if (!el) {
    return;
  }
  contractScrolledToBottom.value = el.scrollTop + el.clientHeight >= el.scrollHeight - 8;
};

const openContractDialog = async () => {
  if (!selectedProductId.value || contractLoading.value) {
    return;
  }
  contractDialogVisible.value = true;
  contractLoading.value = true;
  contractCarefulRead.value = false;
  contractScrolledToBottom.value = false;
  try {
    const resp = await previewPurchaseContract(contractPayload());
    contractContent.value = resp?.contract_content || '';
    await nextTick();
    handleContractScroll();
  } catch (error) {
    contractDialogVisible.value = false;
  } finally {
    contractLoading.value = false;
  }
};

const resetContractDialog = () => {
  contractCarefulRead.value = false;
  contractScrolledToBottom.value = false;
};

const rejectContract = () => {
  contractAgreed.value = false;
  contractSignatureId.value = null;
  contractDialogVisible.value = false;
};

const agreeContract = async () => {
  if (!contractScrolledToBottom.value || !contractCarefulRead.value || contractSigning.value) {
    return;
  }
  contractSigning.value = true;
  try {
    const resp = await signPurchaseContract(contractPayload());
    contractSignatureId.value = resp?.id || null;
    contractAgreed.value = Boolean(contractSignatureId.value);
    contractDialogVisible.value = false;
    if (contractAgreed.value) {
      showToast('Agreement accepted');
    }
  } catch (error) {
    // handled by interceptor
  } finally {
    contractSigning.value = false;
  }
};

const resetRightsDialog = () => {
  clearReadTimer();
  readCountdown.value = 5;
};

const clearSmsCooldownTimer = () => {
  if (smsCooldownTimer) {
    clearInterval(smsCooldownTimer);
    smsCooldownTimer = null;
  }
};

const startSmsCooldown = (seconds = 60) => {
  clearSmsCooldownTimer();
  smsCooldown.value = Number(seconds) > 0 ? Number(seconds) : 60;
  smsCooldownTimer = setInterval(() => {
    if (smsCooldown.value <= 1) {
      smsCooldown.value = 0;
      clearSmsCooldownTimer();
      return;
    }
    smsCooldown.value -= 1;
  }, 1000);
};

const resendButtonText = computed(() => {
  return getOrderSmsResendText(smsSending.value, smsCooldown.value);
});

const smsResendDisabled = computed(() => isOrderSmsResendDisabled(smsSending.value, smsCooldown.value));
const isSmsCodeValid = computed(() => isOrderSmsCodeValid(smsCode.value));

const requestOrderSmsCode = async () => {
  if (smsSending.value) {
    return false;
  }
  smsSending.value = true;
  try {
    const resp = await sendOrderSmsCode();
    smsPanelVisible.value = true;
    startSmsCooldown(Number(resp?.cooldown_seconds || 60));
    showToast('Verification code sent');
    return true;
  } catch (error) {
    return false;
  } finally {
    smsSending.value = false;
  }
};

const confirmRightsRead = () => {
  if (readCountdown.value > 0) {
    return;
  }
  hasConfirmedRights.value = true;
  rightsDialogVisible.value = false;
};

const handleOrderAction = async () => {
  if (!selectedProductId.value || submitting.value) {
    return;
  }
  if (!hasConfirmedRights.value) {
    openRightsDialog();
    return;
  }
  if (!contractAgreed.value || !contractSignatureId.value) {
    await openContractDialog();
    return;
  }
  if (!smsPanelVisible.value) {
    await requestOrderSmsCode();
    return;
  }
};

const handleResendSmsCode = async () => {
  if (smsResendDisabled.value) {
    return;
  }
  await requestOrderSmsCode();
};

const handleConfirmOrder = async () => {
  if (!selectedProductId.value || submitting.value || !isSmsCodeValid.value) {
    return;
  }
  submitting.value = true;
  try {
    await withdraw({
      product_id: selectedProductId.value,
      sms_code: smsCode.value,
      use_discount: useDiscount.value,
      extension_source_loan_id: extensionSourceLoanId.value || undefined,
      contract_signature_id: contractSignatureId.value
    });
    showToast('Loan application submitted');
    router.replace('/bill');
  } catch (error) {
    // handled by interceptor
  } finally {
    submitting.value = false;
  }
};

watch(
  () => route.query.product_id,
  () => {
    syncSelectedProduct();
    resetContractState();
  }
);

watch(useDiscount, () => {
  resetContractState();
});

onMounted(() => {
  initData();
});

onBeforeUnmount(() => {
  clearReadTimer();
  clearSmsCooldownTimer();
});
</script>

<style scoped>
.detail-inner {
  min-height: calc(100vh - 48px);
}

.loading-box {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.credit-card,
.product-card,
.other-products-card {
  padding: 16px 14px;
}

.credit-card {
  text-align: center;
}

.credit-label {
  margin: 0;
  font-size: 13px;
  color: var(--app-text-soft);
}

.credit-value {
  margin-top: 10px;
  line-height: 1;
}

.credit-value span {
  font-size: 22px;
  color: var(--app-primary-deep);
}

.credit-value strong {
  font-size: 40px;
  font-weight: 700;
  background: var(--app-gradient);
  -webkit-background-clip: text;
  color: transparent;
}

.credit-tip {
  margin: 10px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text-soft);
}

.coupon-card {
  margin-top: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.coupon-card strong {
  color: var(--app-primary-deep);
  font-size: 18px;
}

.coupon-card p {
  margin: 6px 0 0;
  color: var(--app-text-soft);
  font-size: 12px;
}

.product-card {
  margin-top: 12px;
}

.product-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.product-card-head span {
  font-size: 11px;
  color: var(--app-text-faint);
}

.product-showcase {
  margin-top: 10px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(181, 207, 243, 0.9);
  background:
    radial-gradient(circle at top left, rgba(47, 126, 247, 0.14), transparent 40%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(246, 250, 255, 0.96) 100%);
}

.showcase-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.showcase-title-block h3 {
  margin: 0;
  font-size: 17px;
  line-height: 1.5;
  color: var(--app-text);
}

.showcase-title-block p {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--app-text-soft);
}

.showcase-price {
  text-align: right;
}

.showcase-price span {
  display: block;
  font-size: 11px;
  color: var(--app-text-soft);
}

.showcase-price strong {
  display: block;
  margin-top: 4px;
  font-size: 30px;
  line-height: 1;
  color: var(--app-primary-deep);
}

.showcase-tags {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.showcase-tags span {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(47, 126, 247, 0.1);
  color: var(--app-primary-deep);
  font-size: 11px;
}

.showcase-benefits {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(214, 226, 244, 0.92);
}

.benefits-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.benefits-label {
  font-size: 11px;
  color: var(--app-text-soft);
}

.benefits-detail-btn {
  height: 22px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid rgba(47, 126, 247, 0.28);
  background: rgba(47, 126, 247, 0.08);
  color: var(--app-primary-deep);
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
}

.showcase-benefits p {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text);
}

.other-products-card {
  margin-top: 12px;
}

.other-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.other-head h3 {
  margin: 0;
  font-size: 15px;
  color: var(--app-text);
}

.other-head span {
  font-size: 11px;
  color: var(--app-text-faint);
}

.other-grid {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.other-item {
  padding: 10px;
  border-radius: 12px;
  border: 1px solid rgba(214, 226, 244, 0.95);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(246, 250, 255, 0.9) 100%);
  text-align: left;
}

.other-item-title {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  font-weight: 600;
  color: var(--app-text);
}

.other-item-meta {
  margin-top: 8px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}

.other-item-meta span {
  font-size: 11px;
  color: var(--app-text-soft);
}

.other-item-meta strong {
  font-size: 16px;
  color: var(--app-primary-deep);
}

.order-footer {
  margin-top: 16px;
}

.sms-verify-box {
  margin-bottom: 10px;
  border: 1px solid rgba(214, 226, 244, 0.95);
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}

.sms-verify-actions {
  display: flex;
  gap: 10px;
  padding: 0 12px 12px;
}

.sms-confirm-btn,
.sms-resend-btn {
  flex: 1;
  height: 40px;
  border-radius: 8px !important;
  padding: 0 10px;
  font-size: 14px;
  font-weight: 600;
  line-height: 40px;
}

.order-btn {
  height: 50px;
}

.order-tip {
  margin: 10px 0 0;
  text-align: center;
  font-size: 12px;
  color: var(--app-text-faint);
}

.contract-consent {
  width: 100%;
  margin-top: 10px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  background: transparent;
  color: var(--app-text-soft);
  font-size: 13px;
  line-height: 1.5;
}

.contract-consent.checked {
  color: var(--app-primary-deep);
}

.contract-checkbox {
  width: 17px;
  height: 17px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 17px;
  border-radius: 4px;
  border: 1px solid rgba(47, 126, 247, 0.75);
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  background: #ffffff;
}

.contract-consent.checked .contract-checkbox {
  background: var(--app-primary);
}

.rights-dialog {
  max-height: 86vh;
}

.contract-dialog {
  max-height: 92vh;
}

.rights-dialog-inner,
.contract-dialog-inner {
  display: flex;
  flex-direction: column;
  height: min(86vh, 700px);
  padding: 12px 14px calc(12px + var(--app-tabbar-space) + env(safe-area-inset-bottom, 0px));
}

.contract-dialog-inner {
  height: min(92vh, 760px);
}

.rights-dialog-header,
.contract-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.rights-close-btn {
  height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  border: none;
  background: rgba(47, 126, 247, 0.1);
  color: var(--app-primary-deep);
  font-size: 12px;
  font-weight: 600;
}

.rights-dialog-scroll,
.contract-dialog-scroll {
  flex: 1;
  overflow-y: auto;
  margin-top: 10px;
  padding-right: 2px;
}

.rights-dialog-footer,
.contract-dialog-footer {
  margin-top: 10px;
  padding-top: 10px;
  padding-bottom: 2px;
  border-top: 1px solid rgba(214, 226, 244, 0.9);
  background: #ffffff;
}

.rights-dialog-title,
.contract-dialog-title {
  margin: 0;
  font-size: 18px;
  color: var(--app-text);
}

.contract-dialog-scroll {
  padding: 8px 4px 8px 0;
}

.contract-content {
  font-size: 13px;
  line-height: 1.85;
  color: var(--app-text);
}

.contract-content :deep(h1) {
  margin: 4px 0 14px;
  text-align: center;
  font-size: 20px;
}

.contract-content :deep(h2) {
  margin: 18px 0 8px;
  font-size: 15px;
}

.contract-content :deep(p) {
  margin: 8px 0;
}

.contract-content :deep(.contract-summary) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 14px;
  font-size: 12px;
}

.contract-content :deep(.contract-summary th),
.contract-content :deep(.contract-summary td) {
  border: 1px solid rgba(214, 226, 244, 0.95);
  padding: 7px 8px;
  vertical-align: top;
}

.contract-content :deep(.contract-summary th) {
  width: 32%;
  background: rgba(47, 126, 247, 0.08);
  color: var(--app-text-soft);
  font-weight: 600;
}

.contract-content :deep(.contract-sign-area) {
  margin-top: 16px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(47, 126, 247, 0.06);
}

.contract-read-tip {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--app-text-faint);
}

.contract-actions {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.contract-reject-btn,
.contract-agree-btn {
  min-height: 42px;
}

.rights-provider {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(47, 126, 247, 0.08);
}

.rights-provider p {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text);
}

.rights-provider p + p {
  margin-top: 4px;
}

.rights-section {
  margin-top: 12px;
}

.rights-section h4 {
  margin: 0;
  font-size: 13px;
  color: var(--app-text);
}

.rights-image-grid {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.rights-image-grid img {
  width: 100%;
  height: 92px;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid rgba(214, 226, 244, 0.92);
}

.rights-image-grid-single {
  grid-template-columns: 1fr;
}

.rights-image-grid-single img {
  height: 110px;
}

.rights-section-desc {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text-soft);
}

.rights-empty {
  margin-top: 12px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(247, 250, 255, 0.95);
  color: var(--app-text-soft);
  font-size: 12px;
}

.rights-empty p {
  margin: 0;
}

.rights-confirm-btn {
  min-height: 44px;
}
</style>
