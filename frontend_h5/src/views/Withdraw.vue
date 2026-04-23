<template>
  <div class="page-shell detail-page">
    <van-nav-bar left-arrow title="信用下单" @click-left="router.back()" />

    <div class="page-inner detail-inner">
      <div v-if="loading" class="loading-box">
        <van-loading type="spinner" color="#2f7ef7" />
      </div>

      <template v-else>
        <section class="credit-card page-card">
          <p class="credit-label">可用信用额度</p>
          <div class="credit-value">
            <span>¥</span>
            <strong>{{ formatAmount(approvedLimit) }}</strong>
          </div>
          <p class="credit-tip">下单无需实际支付，将按商品总价占用信用额度，后台发卡后生成账单。</p>
        </section>

        <section class="product-card page-card" v-if="selectedProduct">
          <div class="product-card-head">
            <h2 class="page-section-title">可选商品</h2>
            <span>京东E卡 + 韶关丹霞山旅游权益</span>
          </div>

          <article class="product-showcase">
            <div class="showcase-top">
              <div class="showcase-title-block">
                <h3>{{ selectedProduct.name }}</h3>
                <p>{{ selectedProduct.rights_title || '韶关丹霞山旅游权益' }}</p>
              </div>
              <div class="showcase-price">
                <span>总售价</span>
                <strong>¥{{ formatAmount(selectedProduct.payment_amount) }}</strong>
              </div>
            </div>

            <div class="showcase-tags">
              <span>京东E卡额度 ¥{{ formatAmount(selectedProduct.ecard_face_value) }}</span>
              <span>账期 {{ selectedProduct.term_days }} 天</span>
              <span>额度按总价扣减</span>
            </div>

            <div class="showcase-benefits">
              <div class="benefits-head">
                <div class="benefits-label">权益说明</div>
                <button type="button" class="benefits-detail-btn" @click.stop="openRightsDialog">点我查看详情</button>
              </div>
              <p>{{ selectedProduct.rights_desc || '权益内容以订单快照为准' }}</p>
            </div>
          </article>
        </section>

        <section class="other-products-card page-card" v-if="otherProducts.length">
          <div class="other-head">
            <h3>其他商品</h3>
            <span>点击进入详情</span>
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
                <span>额度 ¥{{ formatAmount(item.ecard_face_value) }}</span>
                <strong>¥{{ formatAmount(item.payment_amount) }}</strong>
              </div>
            </button>
          </div>
        </section>

        <div class="order-footer">
          <van-button
            block
            type="primary"
            class="primary-action order-btn"
            :disabled="!selectedProductId"
            :loading="submitting"
            @click="handleOrderAction"
          >
            信用支付下单
          </van-button>
          <p class="order-tip">下单后等待后台发卡，付款日按商品账期自动生成</p>
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
          <h3 class="rights-dialog-title">权益详细介绍</h3>
          <button type="button" class="rights-close-btn" @click="rightsDialogVisible = false">关闭</button>
        </div>

        <div class="rights-dialog-scroll">
          <div class="rights-provider">
            <p>权益服务商：韶关市人在草木间商贸有限公司</p>
            <p>客服电话：13800138000</p>
          </div>

          <div class="rights-section">
            <h4>图片组1（酒店内景，2张）</h4>
            <div class="rights-image-grid">
              <img src="https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80" alt="酒店内景1">
              <img src="https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80" alt="酒店内景2">
            </div>
            <p class="rights-section-desc">酒店介绍：入住舒适酒店客房，周边交通便利，适合丹霞山行程入住与休整。</p>
          </div>

          <div class="rights-section">
            <h4>图片组2（旅游景点照片，2张）</h4>
            <div class="rights-image-grid">
              <img src="https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=900&q=80" alt="景点照片1">
              <img src="https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=900&q=80" alt="景点照片2">
            </div>
            <p class="rights-section-desc">景点介绍：丹霞地貌自然景观丰富，行程包含核心观景区域游览与打卡路线建议。</p>
          </div>

          <div class="rights-section">
            <h4>图片组3（餐饮介绍）</h4>
            <div class="rights-image-grid rights-image-grid-single">
              <img src="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80" alt="餐饮介绍">
            </div>
            <p class="rights-section-desc">餐饮简介：安排当地特色风味餐，覆盖正餐场景，具体菜单以服务商当日安排为准。</p>
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
            {{ readCountdown > 0 ? `${readCountdown}s 后可点击` : '我已阅读并理解' }}
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { showToast } from 'vant';
import { getLoanStatus, getProducts, withdraw } from '../api';

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const rightsDialogVisible = ref(false);
const readCountdown = ref(5);
const hasConfirmedRights = ref(false);
const submitting = ref(false);
const approvedLimit = ref(0);
const products = ref([]);
const selectedProductId = ref(null);
let readTimer = null;

const formatAmount = (value) => Number(value || 0).toLocaleString('zh-CN', {
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

const otherProducts = computed(() =>
  products.value.filter((item) => item.id !== selectedProductId.value)
);

const initData = async () => {
  try {
    const loan = await getLoanStatus();
    if (loan.status !== 'APPROVED') {
      showToast('当前状态不可下单');
      router.replace(
        loan.status === 'WITHDRAWING' || loan.status === 'DISBURSED' || loan.status === 'OVERDUE'
          ? '/bill'
          : '/home'
      );
      return;
    }
    approvedLimit.value = Number(loan.approved_credit_limit || loan.credit_limit || 0);

    const list = await getProducts();
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

const resetRightsDialog = () => {
  clearReadTimer();
  readCountdown.value = 5;
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

  submitting.value = true;
  try {
    await withdraw({ product_id: selectedProductId.value });
    showToast('下单成功');
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
  }
);

onMounted(() => {
  initData();
});

onBeforeUnmount(() => {
  clearReadTimer();
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

.order-btn {
  height: 50px;
}

.order-tip {
  margin: 10px 0 0;
  text-align: center;
  font-size: 12px;
  color: var(--app-text-faint);
}

.rights-dialog {
  max-height: 86vh;
}

.rights-dialog-inner {
  display: flex;
  flex-direction: column;
  height: min(86vh, 700px);
  padding: 12px 14px calc(12px + var(--app-tabbar-space) + env(safe-area-inset-bottom, 0px));
}

.rights-dialog-header {
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

.rights-dialog-scroll {
  flex: 1;
  overflow-y: auto;
  margin-top: 10px;
  padding-right: 2px;
}

.rights-dialog-footer {
  margin-top: 10px;
  padding-top: 10px;
  padding-bottom: 2px;
  border-top: 1px solid rgba(214, 226, 244, 0.9);
  background: #ffffff;
}

.rights-dialog-title {
  margin: 0;
  font-size: 18px;
  color: var(--app-text);
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

.rights-confirm-btn {
  min-height: 44px;
}
</style>
