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
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="订单号" width="96" />
        <el-table-column label="借款人" min-width="210">
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
        <el-table-column label="剩余还款额" min-width="132">
          <template #default="{ row }">
            {{ formatCurrency(row.remaining_repayment_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="还款日" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.due_date) }}
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

    <el-dialog v-model="dialogVisible" width="680px" title="财务处理" destroy-on-close>
      <div v-if="currentRow" class="detail-stack">
        <section class="detail-card">
          <h3>账单概览</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="借款人">{{ currentRow.user_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ currentRow.user_phone || '--' }}</el-descriptions-item>
            <el-descriptions-item label="订单状态">
              <el-tag :type="getStatusTagType(currentRow.status)">{{ getStatusText(currentRow.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="还款日">{{ formatDateTime(currentRow.due_date) }}</el-descriptions-item>
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
import { formatCurrency, formatDateTime, getStatusTagType, getStatusText } from '../utils/format';

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
  page: 1,
  size: 10
});

const financeForm = reactive({
  received_amount: 0,
  reduction_amount: 0,
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
    tip: '按全部在贷与已结清口径统计'
  },
  {
    label: '实收金额',
    value: formatCurrency(repaymentStats.value.received_amount || 0),
    tip: `回款率 ${Number(repaymentStats.value.repayment_rate || 0).toFixed(2)}%`
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

const previewRemainingAmount = computed(() => {
  if (!currentRow.value) {
    return 0;
  }
  const totalAmount = Number(currentRow.value.total_repayment_amount || 0);
  return Math.max(totalAmount - previewPaidAmount.value - previewReductionAmount.value, 0);
});

const isPreviewOverLimit = computed(() => {
  if (!currentRow.value) {
    return false;
  }
  const totalAmount = Number(currentRow.value.total_repayment_amount || 0);
  return previewPaidAmount.value + previewReductionAmount.value > totalAmount + 0.000001;
});

const fetchData = async () => {
  loading.value = true;
  try {
    const [statsRes, repaymentStatsRes] = await Promise.all([getAdminStats(), getRepaymentStats()]);
    stats.value = statsRes;
    repaymentStats.value = repaymentStatsRes;
    const res = await getLoans({
      scope: 'FINANCE',
      phone: filters.keyword || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    });
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
  if (!financeForm.received_amount && !financeForm.reduction_amount) {
    ElMessage.warning('请填写登记收款或减免金额');
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

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.finance-preview {
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
  margin: 10px 0 0;
  color: #d85c5c;
  font-size: 12px;
}

@media (max-width: 1440px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
