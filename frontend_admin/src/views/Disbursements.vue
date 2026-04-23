<template>
  <div class="admin-page">
    <section class="queue-summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="queue-summary-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.tip }}</p>
      </article>
    </section>

    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input
            v-model="filters.phone"
            placeholder="手机号 / 姓名 / 身份证号"
            clearable
            @keyup.enter="fetchData"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="订单号" width="96" />
        <el-table-column label="客户信息" min-width="220">
          <template #default="{ row }">
            <div>{{ row.user_name || '未实名' }}</div>
            <div class="sub-text">{{ row.user_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="复借次数" width="120">
          <template #default="{ row }">
            <div>{{ row.relend_label || '初借' }}</div>
            <el-button
              v-if="row.latest_settled_loan"
              link
              type="primary"
              class="history-link"
              @click="openHistoryDialog(row)"
            >
              历史账单
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="E卡面值" min-width="126">
          <template #default="{ row }">
            {{ formatCurrency(resolveEcardFaceValue(row)) }}
          </template>
        </el-table-column>
        <el-table-column label="商品信息" min-width="220">
          <template #default="{ row }">
            <div>{{ row.product_name || '--' }}</div>
            <div class="sub-text">
              旅游权益 {{ formatCurrency(row.rights_price) }} · 账期 {{ row.product_term_days || row.term_days || '--' }} 天
            </div>
          </template>
        </el-table-column>
        <el-table-column label="支付/账单" min-width="150">
          <template #default="{ row }">
            <div>{{ formatCurrency(resolvePaymentAmount(row)) }}</div>
            <div class="sub-text">账单总额 {{ formatCurrency(resolvePaymentAmount(row)) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" min-width="150">
          <template #default="{ row }">
            <div v-if="row.created_at" class="date-cell">
              <div>{{ formatDate(row.created_at) }}</div>
              <div class="sub-text">{{ formatTime(row.created_at) }}</div>
            </div>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="188" fixed="right">
          <template #default="{ row }">
            <div class="row-action-cell">
              <el-button
                size="small"
                type="primary"
                :loading="actionLoading === getDisburseActionKey(row.id)"
                @click="handleDisburse(row)"
              >
                发卡GO
              </el-button>
              <el-button link type="primary" @click="openDrawer(row)">查看处理</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="filters.size"
          :current-page="filters.page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="drawerVisible" size="720px" title="待发卡处理" destroy-on-close>
      <div v-if="form.id" class="detail-stack">
        <section class="detail-card">
          <h3>客户与订单信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用户">{{ currentRow?.user_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ currentRow?.user_phone || '--' }}</el-descriptions-item>
            <el-descriptions-item label="状态">待发卡</el-descriptions-item>
            <el-descriptions-item label="下单商品">{{ currentRow?.product_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="E卡面值">{{ formatCurrency(currentSummary.ecardFaceValue) }}</el-descriptions-item>
            <el-descriptions-item label="旅游权益">{{ formatCurrency(currentSummary.rightsPrice) }}</el-descriptions-item>
            <el-descriptions-item label="信用支付金额">{{ formatCurrency(currentSummary.paymentAmount) }}</el-descriptions-item>
            <el-descriptions-item label="账期">{{ currentSummary.termDays ? `${currentSummary.termDays} 天` : '--' }}</el-descriptions-item>
            <el-descriptions-item label="预计付款日">{{ currentSummary.dueDateText }}</el-descriptions-item>
            <el-descriptions-item label="下单时间">{{ formatDateTime(currentRow?.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card">
          <h3>处理备注</h3>
          <el-form label-width="96px">
            <el-form-item label="备注">
              <el-input
                v-model="form.review_note"
                type="textarea"
                :rows="3"
                placeholder="填写发卡前确认信息、卡池核验说明或审批备注"
              />
            </el-form-item>
          </el-form>

          <div class="preview-grid">
            <article class="preview-card">
              <span>E卡面值</span>
              <strong>{{ formatCurrency(currentSummary.ecardFaceValue) }}</strong>
            </article>
            <article class="preview-card">
              <span>旅游权益</span>
              <strong>{{ formatCurrency(currentSummary.rightsPrice) }}</strong>
            </article>
            <article class="preview-card">
              <span>信用支付金额</span>
              <strong>{{ formatCurrency(currentSummary.paymentAmount) }}</strong>
            </article>
            <article class="preview-card">
              <span>每期应付</span>
              <strong>{{ formatCurrency(currentSummary.installmentAmount) }}</strong>
            </article>
          </div>

          <div class="due-preview">
            <span class="due-preview-label">预计付款日</span>
            <strong>{{ currentSummary.dueDateText }}</strong>
            <p>规则：每 7 天为 1 期，共 {{ currentSummary.installmentPeriods }} 期；发卡日计为第 1 天，账期第 N 天为付款日。</p>
          </div>

          <div class="drawer-footer">
            <el-button @click="drawerVisible = false">关闭</el-button>
            <el-button type="primary" :loading="saving" @click="saveConfig">保存订单备注</el-button>
          </div>
        </section>

        <section class="detail-card">
          <h3>发卡确认</h3>
          <div class="callout-card">
            <div class="callout-title">发卡前请核对</div>
            <p>当前页面只处理待发卡订单。确认后将从卡池按面额完全匹配分配E卡，并生成正式账单。</p>
          </div>
          <div class="action-row">
            <el-button
              type="primary"
              :loading="actionLoading === getDisburseActionKey(form.id)"
              @click="handleDisburse()"
            >
              发卡GO
            </el-button>
          </div>
        </section>

        <section class="detail-card">
          <h3>最近操作轨迹</h3>
          <div v-if="events.length" class="timeline-list">
            <article v-for="event in events" :key="event.id" class="timeline-item">
              <strong>{{ event.title }}</strong>
              <p>{{ event.detail || '无补充说明' }}</p>
              <div class="timeline-meta">{{ event.operator_name || event.actor_type }} · {{ formatDateTime(event.created_at) }}</div>
            </article>
          </div>
          <el-empty v-else description="暂无操作记录" />
        </section>
      </div>
    </el-drawer>

    <LoanHistoryDialog
      v-model="historyDialogVisible"
      :loan="historyLoan"
      :borrower-name="historyBorrowerName"
    />
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import LoanHistoryDialog from '../components/LoanHistoryDialog.vue';
import { disburseLoan, getAdminStats, getLoans, getUserDetail, updateLoan } from '../api';
import { formatCurrency, formatDate, formatDateTime, formatTime } from '../utils/format';

const BILLING_PERIOD_DAYS = 7;

const loading = ref(false);
const saving = ref(false);
const actionLoading = ref('');
const drawerVisible = ref(false);
const total = ref(0);
const tableData = ref([]);
const stats = ref({});
const currentRow = ref(null);
const events = ref([]);
const historyDialogVisible = ref(false);
const historyLoan = ref(null);
const historyBorrowerName = ref('');

const filters = reactive({
  phone: '',
  page: 1,
  size: 10
});

const form = reactive({
  id: null,
  review_note: ''
});

const resolveEcardFaceValue = (source) => Number(source?.ecard_face_value || source?.credit_limit || 0);
const resolveRightsPrice = (source) => Number(source?.rights_price || 0);
const resolvePaymentAmount = (source) => {
  const fromSnapshot = Number(source?.product_total_price || source?.total_repayment_amount || 0);
  if (fromSnapshot > 0) {
    return fromSnapshot;
  }
  return resolveEcardFaceValue(source) + resolveRightsPrice(source);
};
const TERM_DAYS_FALLBACK_BY_ECARD_FACE_VALUE = {
  1000: 7,
  1500: 10,
  2000: 14,
  3000: 30
};
const resolveTermDays = (source) => {
  const termDays = Number(source?.product_term_days || source?.term_days || 0);
  if (Number.isFinite(termDays) && termDays > 0) {
    return termDays;
  }

  const ecardFaceValue = Math.round(resolveEcardFaceValue(source));
  return Number(TERM_DAYS_FALLBACK_BY_ECARD_FACE_VALUE[ecardFaceValue] || 0);
};
const resolveInstallmentPeriods = (termDays) => (
  termDays >= BILLING_PERIOD_DAYS && termDays % BILLING_PERIOD_DAYS === 0
    ? termDays / BILLING_PERIOD_DAYS
    : 0
);
const resolveDueDateText = (termDays) => {
  if (!termDays) {
    return '--';
  }
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + Math.max(Number(termDays) - 1, 0));
  return formatDateTime(dueDate);
};
const resolveInstallmentAmount = (paymentAmount, installmentPeriods) => (
  installmentPeriods > 0 ? Number((paymentAmount / installmentPeriods).toFixed(2)) : 0
);

const visiblePrincipalAmount = computed(() =>
  tableData.value.reduce((sum, row) => sum + resolveEcardFaceValue(row), 0)
);

const visibleRepaymentAmount = computed(() =>
  tableData.value.reduce((sum, row) => sum + resolvePaymentAmount(row), 0)
);

const summaryCards = computed(() => [
  {
    label: '待发卡订单',
    value: `${stats.value.withdrawing_loans || 0} 单`,
    tip: '待客户完成信用下单后的卡池发卡确认'
  },
  {
    label: '当前页E卡面值',
    value: formatCurrency(visiblePrincipalAmount.value),
    tip: '按当前筛选结果统计'
  },
  {
    label: '当前页支付总额',
    value: formatCurrency(visibleRepaymentAmount.value),
    tip: '发卡后将进入正式账单'
  }
]);

const buildSummary = (source) => {
  const ecardFaceValue = resolveEcardFaceValue(source);
  const rightsPrice = resolveRightsPrice(source);
  const paymentAmount = resolvePaymentAmount(source);
  const termDays = resolveTermDays(source);
  const installmentPeriods = resolveInstallmentPeriods(termDays);

  return {
    ecardFaceValue,
    rightsPrice,
    paymentAmount,
    termDays,
    installmentPeriods,
    installmentAmount: resolveInstallmentAmount(paymentAmount, installmentPeriods),
    dueDateText: resolveDueDateText(termDays),
  };
};

const currentSummary = computed(() => buildSummary(currentRow.value));

const fetchStats = async () => {
  stats.value = await getAdminStats();
};

const fetchData = async () => {
  loading.value = true;
  try {
    await fetchStats();
    const res = await getLoans({
      scope: 'WITHDRAWING',
      phone: filters.phone || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.phone = '';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const openDrawer = async (row) => {
  currentRow.value = row;
  form.id = row.id;
  form.review_note = row.review_note || '';
  drawerVisible.value = true;

  try {
    const detail = await getUserDetail(row.user_id);
    events.value = detail.events || [];
  } catch (error) {
    events.value = [];
  }
};

const openHistoryDialog = (row) => {
  historyLoan.value = row.latest_settled_loan || null;
  historyBorrowerName.value = row.user_name || row.user_phone || '';
  historyDialogVisible.value = true;
};

const saveConfig = async () => {
  saving.value = true;
  try {
    await updateLoan(form.id, { review_note: form.review_note });
    ElMessage.success('订单备注已保存');
    drawerVisible.value = false;
    await fetchData();
  } finally {
    saving.value = false;
  }
};

const getDisburseActionKey = (loanId) => `disburse-${loanId}`;

const createMetric = (label, value, extraClass = '') =>
  h('div', { class: ['confirm-metric', extraClass].filter(Boolean).join(' ') }, [
    h('span', { class: 'confirm-metric-label' }, label),
    h('strong', { class: 'confirm-metric-value' }, value)
  ]);

const createConfirmMessage = (row, summary) => h('div', { class: 'confirm-shell' }, [
  h('div', { class: 'confirm-banner' }, [
    h('div', { class: 'confirm-banner-top' }, [
      h('span', { class: 'confirm-tag' }, '京东E卡发放指令'),
      h('span', { class: 'confirm-order' }, `订单 ${row.id || '--'}`)
    ]),
    h('div', { class: 'confirm-head' }, [
      h('strong', { class: 'confirm-name' }, row.user_name || '未实名'),
      h('span', { class: 'confirm-phone' }, row.user_phone || '--')
    ]),
    h('p', { class: 'confirm-desc' }, '确认后该订单会从待发卡切换为已发卡，并立即生成正式账单。')
  ]),
  h('div', { class: 'confirm-grid' }, [
    createMetric('E卡面值', formatCurrency(summary.ecardFaceValue), 'confirm-metric-primary'),
    createMetric('旅游权益', formatCurrency(summary.rightsPrice))
  ]),
  h('div', { class: 'confirm-grid confirm-grid-detail' }, [
    createMetric('信用支付金额', formatCurrency(summary.paymentAmount)),
    createMetric(
      '账期',
      summary.termDays && summary.installmentPeriods
        ? `${summary.termDays} 天 / ${summary.installmentPeriods} 期`
        : '待确认'
    ),
    createMetric('每期应付', formatCurrency(summary.installmentAmount))
  ]),
  h('div', { class: 'confirm-note' }, [
    h('span', { class: 'confirm-note-label' }, '预计付款日'),
    h('strong', { class: 'confirm-note-value' }, summary.dueDateText),
    h('p', { class: 'confirm-note-desc' }, '按实际发卡时间计为第 1 天，账期第 N 天为付款日。确认前请再次核对卡池库存和有效期。')
  ])
]);

const handleDisburse = async (row = null) => {
  const targetRow = row || currentRow.value;
  const targetId = row?.id || form.id;

  if (!targetRow || !targetId) {
    return;
  }

  const summary = buildSummary(targetRow);
  if (!summary.ecardFaceValue || !summary.paymentAmount) {
    ElMessage.warning('订单快照不完整，请先核对商品配置');
    return;
  }
  if (summary.termDays && !summary.installmentPeriods) {
    ElMessage.warning(`账期必须为 ${BILLING_PERIOD_DAYS} 天的倍数`);
    return;
  }

  try {
    await ElMessageBox({
      title: '确认发放京东E卡',
      message: createConfirmMessage(targetRow, summary),
      showCancelButton: true,
      confirmButtonText: '确认发卡',
      cancelButtonText: '取消',
      customClass: 'disburse-confirm-dialog'
    });
  } catch (error) {
    return;
  }

  actionLoading.value = getDisburseActionKey(targetId);
  try {
    const payload = summary.termDays ? { term_days: summary.termDays } : {};
    await disburseLoan(targetId, payload);
    ElMessage.success('发卡已确认');
    drawerVisible.value = false;
    await fetchData();
  } finally {
    actionLoading.value = '';
  }
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.sub-text {
  margin-top: 4px;
  color: #7f8da2;
  font-size: 12px;
}

.queue-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.queue-summary-card {
  padding: 18px 20px;
  border-radius: 22px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.94) 100%);
  box-shadow: 0 16px 36px rgba(16, 46, 91, 0.06);
}

.queue-summary-card span {
  font-size: 12px;
  color: #7a8aa1;
}

.queue-summary-card strong {
  display: block;
  margin-top: 12px;
  font-size: 26px;
  color: #16233a;
}

.queue-summary-card p {
  margin: 10px 0 0;
  font-size: 12px;
  color: #2c72e5;
}

.date-cell {
  display: flex;
  flex-direction: column;
}

.row-action-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.edit-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-tag {
  height: 32px;
  padding: 0 14px;
  border: 1px solid rgba(44, 114, 229, 0.14);
  border-radius: 999px;
  background: #f7faff;
  color: #5f7188;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-tag:hover {
  border-color: rgba(44, 114, 229, 0.28);
  color: #2c72e5;
}

.quick-tag-active {
  border-color: transparent;
  background: linear-gradient(135deg, #2c72e5 0%, #4b8ef8 100%);
  color: #ffffff;
  box-shadow: 0 10px 22px rgba(44, 114, 229, 0.18);
}

.fee-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.suffix-unit {
  font-size: 14px;
  color: #5f7188;
  font-weight: 600;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 8px 0 14px;
}

.preview-card {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(44, 114, 229, 0.08);
  background: linear-gradient(180deg, rgba(246, 250, 255, 1) 0%, rgba(255, 255, 255, 1) 100%);
}

.preview-card span {
  display: block;
  font-size: 12px;
  color: #7a8aa1;
}

.preview-card strong {
  display: block;
  margin-top: 10px;
  font-size: 20px;
  color: #1f66e5;
}

.due-preview {
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255, 248, 230, 0.96) 0%, rgba(255, 252, 242, 0.96) 100%);
  border: 1px solid rgba(243, 194, 82, 0.28);
}

.due-preview-label {
  display: block;
  font-size: 12px;
  color: #9a7b24;
}

.due-preview strong {
  display: block;
  margin-top: 8px;
  font-size: 16px;
  color: #16233a;
}

.due-preview p {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.7;
  color: #8a7330;
}

.callout-card {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(44, 114, 229, 0.08);
  background: linear-gradient(180deg, rgba(246, 250, 255, 1) 0%, rgba(255, 255, 255, 1) 100%);
}

.callout-title {
  font-size: 14px;
  font-weight: 700;
  color: #16233a;
}

.callout-card p {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: #607089;
}

.action-row {
  margin-top: 16px;
}

:global(.disburse-confirm-dialog.el-message-box) {
  width: 540px;
  max-width: calc(100vw - 32px);
  padding: 0;
  border: 1px solid rgba(13, 63, 131, 0.08);
  border-radius: 22px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.94) 100%);
  box-shadow: 0 16px 36px rgba(16, 46, 91, 0.14);
}

:global(.disburse-confirm-dialog .el-message-box__header) {
  padding: 20px 22px 0;
}

:global(.disburse-confirm-dialog .el-message-box__title) {
  font-size: 22px;
  font-weight: 700;
  color: #16233a;
}

:global(.disburse-confirm-dialog .el-message-box__content) {
  padding: 14px 22px 0;
}

:global(.disburse-confirm-dialog .el-message-box__message) {
  padding: 0;
}

:global(.disburse-confirm-dialog .el-message-box__btns) {
  margin-top: 18px;
  padding: 18px 22px 22px;
  border-top: 1px solid rgba(22, 35, 58, 0.06);
  background: rgba(255, 255, 255, 0.86);
}

:global(.disburse-confirm-dialog .el-message-box__btns .el-button) {
  min-width: 112px;
  height: 42px;
  border-radius: 12px;
  font-weight: 600;
}

:global(.disburse-confirm-dialog .el-message-box__btns .el-button--primary) {
  border-color: transparent;
  background: linear-gradient(135deg, #2c72e5 0%, #4b8ef8 100%);
  box-shadow: 0 10px 22px rgba(44, 114, 229, 0.18);
}

:global(.confirm-shell) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:global(.confirm-banner) {
  padding: 18px 18px 16px;
  border-radius: 18px;
  border: 1px solid rgba(44, 114, 229, 0.14);
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.12), transparent 36%),
    linear-gradient(135deg, #1c4e93 0%, #245faf 56%, #2c72e5 100%);
  box-shadow: 0 14px 28px rgba(31, 102, 229, 0.18);
}

:global(.confirm-banner-top) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

:global(.confirm-tag) {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
}

:global(.confirm-order) {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.72);
}

:global(.confirm-head) {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
}

:global(.confirm-name) {
  font-size: 22px;
  color: #ffffff;
}

:global(.confirm-phone) {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.78);
}

:global(.confirm-desc) {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.74);
}

:global(.confirm-grid) {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

:global(.confirm-grid-detail) {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

:global(.confirm-grid-detail .confirm-metric) {
  grid-column: span 2;
}

:global(.confirm-metric) {
  padding: 14px 16px;
  border-radius: 16px;
  min-height: 92px;
  background: linear-gradient(180deg, rgba(246, 250, 255, 1) 0%, rgba(255, 255, 255, 1) 100%);
  border: 1px solid rgba(44, 114, 229, 0.08);
}

:global(.confirm-metric-primary) {
  background: linear-gradient(135deg, #1f66e5 0%, #3b82f6 100%);
  box-shadow: 0 14px 24px rgba(31, 102, 229, 0.18);
}

:global(.confirm-metric-label) {
  display: block;
  font-size: 12px;
  color: #7a8aa1;
  line-height: 1.45;
}

:global(.confirm-metric-primary .confirm-metric-label) {
  color: rgba(255, 255, 255, 0.78);
}

:global(.confirm-metric-value) {
  display: block;
  margin-top: 10px;
  font-size: 18px;
  line-height: 1.45;
  white-space: normal;
  word-break: break-word;
  color: #16233a;
}

:global(.confirm-metric-primary .confirm-metric-value) {
  color: #ffffff;
}

:global(.confirm-note) {
  padding: 16px 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255, 248, 230, 0.96) 0%, rgba(255, 252, 242, 0.96) 100%);
  border: 1px solid rgba(243, 194, 82, 0.28);
}

:global(.confirm-note-label) {
  display: block;
  font-size: 12px;
  color: #9a7b24;
}

:global(.confirm-note-value) {
  display: block;
  margin-top: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #16233a;
}

:global(.confirm-note-desc) {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.7;
  color: #8a7330;
}

@media (max-width: 1280px) {
  .queue-summary-grid,
  .preview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  :global(.confirm-head),
  :global(.confirm-banner-top) {
    flex-direction: column;
    align-items: flex-start;
  }

  :global(.confirm-grid),
  :global(.confirm-grid-detail) {
    grid-template-columns: 1fr;
  }
}
</style>
