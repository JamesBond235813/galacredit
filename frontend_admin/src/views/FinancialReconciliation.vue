<template>
  <div class="admin-page">
    <section class="summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="summary-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.tip }}</p>
      </article>
    </section>

    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="姓名 / 手机号"
            clearable
            @keydown.enter.prevent="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
        <el-form-item label="应还款时间">
          <el-date-picker
            v-model="filters.dueDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleDueDateSearch">查询</el-button>
        </el-form-item>
        <el-form-item label="实际还款时间">
          <el-date-picker
            v-model="filters.actualRepaymentRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleActualRepaymentSearch">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="订单号" width="96" />
        <el-table-column label="客户" min-width="210">
          <template #default="{ row }">
            <div class="borrower-name-row">
              <span>{{ row.user_name || '未实名' }}</span>
              <span v-if="row.user_blacklist_hit" class="black-badge">黑</span>
            </div>
            <div class="sub-text">{{ row.user_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="复购次数" width="120">
          <template #default="{ row }">
            <div>{{ row.relend_label || '首购' }}</div>
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
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="总还款额" min-width="126">
          <template #default="{ row }">
            {{ formatCurrency(row.total_repayment_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="已还款额" min-width="126">
          <template #default="{ row }">
            {{ formatCurrency(row.repaid_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="减免金额" min-width="126">
          <template #default="{ row }">
            {{ formatCurrency(row.reduction_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="其他费用" min-width="126">
          <template #default="{ row }">
            {{ formatCurrency(row.other_fee_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="剩余还款额" min-width="132">
          <template #default="{ row }">
            {{ formatCurrency(row.remaining_repayment_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="应还款时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.due_date) }}
          </template>
        </el-table-column>
        <el-table-column label="实际还款时间" min-width="150">
          <template #default="{ row }">
            {{ formatDate(row.actual_repayment_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.status === 'SETTLED'" @click="openDialog(row)">
              {{ row.status === 'SETTLED' ? '已平账' : '财务处理' }}
            </el-button>
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

    <el-dialog v-model="dialogVisible" width="1180px" title="财务处理" destroy-on-close>
      <div v-if="currentRow" class="detail-stack">
        <section class="detail-card">
          <h3>账单概览</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="客户">{{ currentRow.user_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ currentRow.user_phone || '--' }}</el-descriptions-item>
            <el-descriptions-item label="订单状态">
              <el-tag :type="getStatusTagType(currentRow.status)">{{ getStatusText(currentRow.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="应还款时间">{{ formatDateTime(currentRow.due_date) }}</el-descriptions-item>
            <el-descriptions-item label="实际还款时间">{{ formatDate(currentRow.actual_repayment_date) }}</el-descriptions-item>
            <el-descriptions-item label="总还款额">{{ formatCurrency(currentRow.total_repayment_amount) }}</el-descriptions-item>
            <el-descriptions-item label="剩余还款额">{{ formatCurrency(currentRow.remaining_repayment_amount) }}</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card">
          <h3>财务登记</h3>
          <el-form label-width="96px">
            <el-form-item label="登记收款">
              <el-input-number v-model="financeForm.received_amount" :min="0" :step="100" />
            </el-form-item>
            <el-form-item label="减免金额">
              <el-input-number v-model="financeForm.reduction_amount" :min="0" :step="100" />
            </el-form-item>
            <el-form-item label="额外收款">
              <el-input-number v-model="financeForm.other_fee_amount" :min="0" :step="100" />
            </el-form-item>
            <el-form-item label="实际还款日">
              <el-date-picker
                v-model="financeForm.actual_repayment_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="选择实际还款日"
                clearable
              />
            </el-form-item>
            <el-form-item label="备注">
              <el-input
                v-model="financeForm.note"
                type="textarea"
                :rows="3"
                placeholder="填写本次收款说明、减免原因或财务备注"
              />
            </el-form-item>
          </el-form>

          <div class="finance-preview" :class="{ 'finance-preview-danger': isPreviewOverLimit }">
            <div class="finance-preview-row">
              <span>平账后已还款额</span>
              <strong>{{ formatCurrency(previewPaidAmount) }}</strong>
            </div>
            <div class="finance-preview-row">
              <span>平账后减免金额</span>
              <strong>{{ formatCurrency(previewReductionAmount) }}</strong>
            </div>
            <div class="finance-preview-row">
              <span>本次冲抵逾期费</span>
              <strong>{{ formatCurrency(previewPenaltyOffsetAmount) }}</strong>
            </div>
            <div class="finance-preview-row">
              <span>平账后其他费用</span>
              <strong>{{ formatCurrency(previewOtherFeeAmount) }}</strong>
            </div>
            <div class="finance-preview-row">
              <span>当前待补逾期费</span>
              <strong>{{ formatCurrency(currentPendingPenaltyAmount) }}</strong>
            </div>
            <div class="finance-preview-row">
              <span>平账后剩余还款额</span>
              <strong>{{ formatCurrency(previewRemainingAmount) }}</strong>
            </div>
            <p v-if="isPreviewOverLimit" class="finance-preview-tip">收款金额与减免金额累计不能超过总还款额</p>
          </div>

          <div class="drawer-footer">
            <el-button @click="dialogVisible = false">关闭</el-button>
            <el-button type="primary" :loading="saving" :disabled="isPreviewOverLimit" @click="submitReconcile">
              提交财务登记
            </el-button>
          </div>
        </section>

        <section class="detail-card">
          <h3>账单台账</h3>
          <LoanLedgerPanel :ledger="loanLedger" :loading="ledgerLoading" />
        </section>
      </div>
    </el-dialog>

    <LoanHistoryDialog
      v-model="historyDialogVisible"
      :loan="historyLoan"
      :borrower-name="historyBorrowerName"
    />
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import LoanLedgerPanel from '../components/LoanLedgerPanel.vue';
import LoanHistoryDialog from '../components/LoanHistoryDialog.vue';
import { financeReconcileLoan, getAdminStats, getLoanLedger, getLoans, getRepaymentStats } from '../api';
import { formatCurrency, formatDate, formatDateTime, getStatusTagType, getStatusText } from '../utils/format';

const route = useRoute();
const loading = ref(false);
const saving = ref(false);
const total = ref(0);
const tableData = ref([]);
const dialogVisible = ref(false);
const currentRow = ref(null);
const stats = ref({});
const repaymentStats = ref({});
const historyDialogVisible = ref(false);
const historyLoan = ref(null);
const historyBorrowerName = ref('');
const loanLedger = ref(null);
const ledgerLoading = ref(false);

const filters = reactive({
  keyword: '',
  dueDateRange: [],
  actualRepaymentRange: [],
  page: 1,
  size: 10
});

const financeForm = reactive({
  received_amount: 0,
  reduction_amount: 0,
  other_fee_amount: 0,
  actual_repayment_date: '',
  note: ''
});

const summaryCards = computed(() => [
  {
    label: '未结清订单',
    value: `${Number(stats.value.disbursed_loans || 0) + Number(stats.value.overdue_loans || 0)} 单`,
    tip: '正常还款与逾期账单统一进入财务处理'
  },
  {
    label: '应收总额',
    value: formatCurrency(repaymentStats.value.receivable_amount || 0),
    tip: '按全部履约中与已结清口径统计'
  },
  {
    label: '实收金额',
    value: formatCurrency(repaymentStats.value.received_amount || 0),
    tip: `回款率 ${Number(repaymentStats.value.repayment_rate || 0).toFixed(2)}%`
  },
  {
    label: '其他费用',
    value: formatCurrency(repaymentStats.value.other_fee_amount || 0),
    tip: '账单外额外收款单独统计'
  },
  {
    label: '减免金额',
    value: formatCurrency(repaymentStats.value.reduction_amount || 0),
    tip: '财务登记后会自动回写账单余额'
  }
]);

const previewPaidAmount = computed(() => {
  if (!currentRow.value) {
    return 0;
  }
  return Number(currentRow.value.repaid_amount || 0) + Number(financeForm.received_amount || 0);
});

const previewReductionAmount = computed(() => {
  if (!currentRow.value) {
    return 0;
  }
  return Number(currentRow.value.reduction_amount || 0) + Number(financeForm.reduction_amount || 0);
});

const currentPendingPenaltyAmount = computed(() => {
  if (!currentRow.value) {
    return 0;
  }
  return Math.max(
    Number(currentRow.value.penalty_amount || 0)
      - Number(currentRow.value.paid_penalty_amount || 0)
      - Number(currentRow.value.reduced_penalty_amount || 0),
    0
  );
});

const previewPenaltyOffsetAmount = computed(() =>
  Math.min(currentPendingPenaltyAmount.value, Number(financeForm.other_fee_amount || 0))
);

const previewOtherFeeAmount = computed(() => {
  if (!currentRow.value) {
    return 0;
  }
  return Number(currentRow.value.other_fee_amount || 0)
    + Math.max(Number(financeForm.other_fee_amount || 0) - previewPenaltyOffsetAmount.value, 0);
});

const previewRemainingAmount = computed(() => {
  if (!currentRow.value) {
    return 0;
  }
  const totalAmount = Number(currentRow.value.total_repayment_amount || 0);
  return Math.max(totalAmount - previewPaidAmount.value - previewPenaltyOffsetAmount.value - previewReductionAmount.value, 0);
});

const isPreviewOverLimit = computed(() => {
  if (!currentRow.value) {
    return false;
  }
  const totalAmount = Number(currentRow.value.total_repayment_amount || 0);
  return previewPaidAmount.value + previewReductionAmount.value > totalAmount + 0.000001;
});

const buildLoanFilterParams = () => {
  const params = {
    scope: 'FINANCE',
    phone: filters.keyword || undefined,
    skip: (filters.page - 1) * filters.size,
    limit: filters.size
  };
  if (filters.dueDateRange.length === 2) {
    params.due_date_start = filters.dueDateRange[0];
    params.due_date_end = filters.dueDateRange[1];
  }
  if (filters.actualRepaymentRange.length === 2) {
    params.actual_repayment_start = filters.actualRepaymentRange[0];
    params.actual_repayment_end = filters.actualRepaymentRange[1];
  }
  return params;
};

const fetchData = async () => {
  loading.value = true;
  try {
    const [statsRes, repaymentStatsRes] = await Promise.all([getAdminStats(), getRepaymentStats()]);
    stats.value = statsRes;
    repaymentStats.value = repaymentStatsRes;
    const res = await getLoans(buildLoanFilterParams());
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  filters.page = 1;
  fetchData();
};

const resetFilters = () => {
  filters.keyword = '';
  filters.dueDateRange = [];
  filters.actualRepaymentRange = [];
  filters.page = 1;
  fetchData();
};

const ensureDueDateRange = () => {
  if (filters.dueDateRange.length === 2) {
    return true;
  }
  ElMessage.warning('请先选择应还款时间区间');
  return false;
};

const ensureActualRepaymentRange = () => {
  if (filters.actualRepaymentRange.length === 2) {
    return true;
  }
  ElMessage.warning('请先选择实际还款时间区间');
  return false;
};

const handleDueDateSearch = () => {
  if (!ensureDueDateRange()) {
    return;
  }
  filters.page = 1;
  fetchData();
};

const handleActualRepaymentSearch = () => {
  if (!ensureActualRepaymentRange()) {
    return;
  }
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const openDialog = (row) => {
  currentRow.value = row;
  financeForm.received_amount = 0;
  financeForm.reduction_amount = 0;
  financeForm.other_fee_amount = 0;
  financeForm.actual_repayment_date = new Date().toISOString().slice(0, 10);
  financeForm.note = '';
  dialogVisible.value = true;
  loadLoanLedger(row.id).catch(() => {});
};

const openHistoryDialog = (row) => {
  historyLoan.value = row.latest_settled_loan || null;
  historyBorrowerName.value = row.user_name || row.user_phone || '';
  historyDialogVisible.value = true;
};

const loadLoanLedger = async (loanId) => {
  ledgerLoading.value = true;
  loanLedger.value = null;
  try {
    loanLedger.value = await getLoanLedger(loanId);
  } finally {
    ledgerLoading.value = false;
  }
};

const submitReconcile = async () => {
  if (!currentRow.value) {
    return;
  }
  if (!financeForm.received_amount && !financeForm.reduction_amount && !financeForm.other_fee_amount) {
    ElMessage.warning('请填写登记收款、减免金额或额外收款');
    return;
  }
  if (isPreviewOverLimit.value) {
    ElMessage.warning('收款金额与减免金额累计不能超过总还款额');
    return;
  }

  saving.value = true;
  try {
    await financeReconcileLoan(currentRow.value.id, {
      received_amount: Number(financeForm.received_amount || 0),
      reduction_amount: Number(financeForm.reduction_amount || 0),
      other_fee_amount: Number(financeForm.other_fee_amount || 0),
      actual_repayment_date: financeForm.actual_repayment_date || undefined,
      note: financeForm.note
    });
    ElMessage.success('财务平账已登记');
    await loadLoanLedger(currentRow.value.id);
    dialogVisible.value = false;
    await fetchData();
  } finally {
    saving.value = false;
  }
};

watch(
  () => route.query.keyword,
  (keyword) => {
    filters.keyword = typeof keyword === 'string' ? keyword : '';
    filters.page = 1;
    fetchData();
  },
  { immediate: true }
);
</script>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.summary-card {
  padding: 18px 20px;
  border-radius: 22px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.94) 100%);
  box-shadow: 0 16px 36px rgba(16, 46, 91, 0.06);
}

.summary-card span {
  font-size: 12px;
  color: #7a8aa1;
}

.summary-card strong {
  display: block;
  margin-top: 12px;
  font-size: 26px;
  color: #16233a;
}

.summary-card p {
  margin: 10px 0 0;
  font-size: 12px;
  color: #2c72e5;
}

.sub-text {
  margin-top: 4px;
  color: #7f8da2;
  font-size: 12px;
}

.black-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  margin-left: 6px;
  border-radius: 50%;
  background: #f56c6c;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.borrower-name-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.detail-stack {
  display: grid;
  grid-template-columns: minmax(360px, 420px) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.detail-stack > section:nth-of-type(1),
.detail-stack > section:nth-of-type(2) {
  grid-column: 1;
}

.detail-stack > section:nth-of-type(3) {
  grid-column: 2;
  grid-row: 1 / span 2;
}

.detail-card {
  height: 100%;
}

.finance-preview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 20px;
  margin-top: 8px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid #d9e2f2;
  background: #f8fbff;
}

.finance-preview-danger {
  border-color: rgba(220, 95, 95, 0.24);
  background: #fff7f7;
}

.finance-preview-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0;
  color: #5f7188;
  font-size: 13px;
}

.finance-preview-row strong {
  color: #16233a;
  font-size: 14px;
}

.finance-preview-tip {
  grid-column: 1 / -1;
  margin: 10px 0 0;
  color: #d85c5c;
  font-size: 12px;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 14px;
}

@media (max-width: 1440px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1280px) {
  .detail-stack,
  .finance-preview {
    grid-template-columns: 1fr;
  }

  .detail-stack > section:nth-of-type(3) {
    grid-column: auto;
    grid-row: auto;
  }
}
</style>
