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
        <el-form-item label="还款日">
          <div class="quick-tag-row">
            <button
              v-for="item in duePresetOptions"
              :key="item.value"
              type="button"
              class="quick-tag"
              :class="{ 'quick-tag-active': filters.dueDatePreset === item.value }"
              @click="applyDueFilter(item.value)"
            >
              {{ item.label }}
            </button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="订单号" width="96" />
        <el-table-column label="借款人" min-width="220">
          <template #default="{ row }">
            <div class="borrower-name-row">
              <span>{{ row.user_name || '未实名' }}</span>
              <span v-if="Number(row.repay_attempt_count || 0) > 0" class="repay-attempt-badge">
                {{ Number(row.repay_attempt_count || 0) }}
              </span>
            </div>
            <div class="sub-text">{{ row.user_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="审核员" width="130">
          <template #default="{ row }">
            {{ row.review_admin_name || '--' }}
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
        <el-table-column label="还款日" min-width="150">
          <template #default="{ row }">
            <div v-if="row.due_date" class="date-cell">
              <div>{{ formatDate(row.due_date) }}</div>
              <div class="sub-text">{{ formatTime(row.due_date) }}</div>
            </div>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="账单进度" width="188">
          <template #default="{ row }">
            <div class="progress-tags">
              <el-tag :type="getDueProgressTagType(row)" effect="light">
                {{ getDueProgressText(row) }}
              </el-tag>
              <el-tag :type="getPaymentProgressTagType(row)" effect="light">
                {{ getPaymentProgressText(row) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="提醒记录" min-width="138">
          <template #default="{ row }">
            <div>{{ row.reminder_count || 0 }} 次</div>
            <div class="sub-text">{{ formatDateTime(row.last_reminded_at) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="日志" width="92">
          <template #default="{ row }">
            <el-button link type="primary" @click="openFollowLogs(row)">查询</el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">跟进处理</el-button>
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

    <el-drawer v-model="drawerVisible" size="720px" title="还款跟进" destroy-on-close>
      <div v-if="currentRow" class="detail-stack">
        <section class="detail-card">
          <h3>客户与账单信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="借款人">{{ currentRow.user_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ currentRow.user_phone || '--' }}</el-descriptions-item>
            <el-descriptions-item label="还款日">{{ formatDateTime(currentRow.due_date) }}</el-descriptions-item>
            <el-descriptions-item label="提醒次数">{{ currentRow.reminder_count || 0 }} 次</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card">
          <h3>账单概览</h3>
          <div class="bill-grid">
            <article class="bill-cell">
              <span>E卡面值</span>
              <strong>{{ formatCurrency(resolveEcardFaceValue(currentRow)) }}</strong>
            </article>
            <article class="bill-cell">
              <span>权益金额</span>
              <strong>{{ formatCurrency(resolveRightsPrice(currentRow)) }}</strong>
            </article>
            <article class="bill-cell">
              <span>信用支付金额</span>
              <strong>{{ formatCurrency(resolvePaymentAmount(currentRow)) }}</strong>
            </article>
            <article class="bill-cell">
              <span>总还款额</span>
              <strong>{{ formatCurrency(currentRow.total_repayment_amount) }}</strong>
            </article>
            <article class="bill-cell">
              <span>已还款额</span>
              <strong>{{ formatCurrency(currentRow.repaid_amount) }}</strong>
            </article>
            <article class="bill-cell">
              <span>减免金额</span>
              <strong>{{ formatCurrency(currentRow.reduction_amount) }}</strong>
            </article>
            <article class="bill-cell bill-cell-emphasis">
              <span>剩余待还</span>
              <strong>{{ formatCurrency(currentRow.remaining_repayment_amount) }}</strong>
            </article>
          </div>
        </section>

        <section class="detail-card">
          <h3>还款跟进</h3>
          <div v-if="isSuperAdmin" class="assignee-row">
            <el-select
              v-model="selectedReviewAdminId"
              placeholder="选择审核员"
              filterable
              :loading="assignLoading"
              style="width: 220px"
            >
              <el-option v-for="item in reviewAssigneeOptions" :key="item.id" :label="item.username" :value="item.id" />
            </el-select>
            <el-button type="primary" plain :loading="assigningReviewer" @click="assignReviewOwner">
              改派负责人
            </el-button>
          </div>
          <el-form label-width="92px">
            <el-form-item label="提醒备注">
              <el-input
                v-model="followNote"
                type="textarea"
                :rows="3"
                placeholder="填写本次提醒内容、客户反馈或后续跟进安排"
              />
            </el-form-item>
          </el-form>

          <div class="follow-actions">
            <el-button
              type="warning"
              :loading="actionLoading === 'remind'"
              @click="handleRemind"
            >
              登记提醒
            </el-button>
            <el-button plain type="primary" @click="jumpToFinance">
              去财务平账
            </el-button>
          </div>
        </section>

        <section class="detail-card">
          <h3>最近跟进记录</h3>
          <div v-if="followEvents.length" class="timeline-list">
            <article v-for="event in followEvents" :key="event.id" class="timeline-item">
              <strong>{{ event.title }}</strong>
              <p>{{ event.detail || '无补充说明' }}</p>
              <div class="timeline-meta">{{ event.operator_name || event.actor_type }} · {{ formatDateTime(event.created_at) }}</div>
            </article>
          </div>
          <el-empty v-else description="暂无跟进记录" />
        </section>

        <section class="detail-card">
          <h3>账单台账</h3>
          <LoanLedgerPanel :ledger="loanLedger" :loading="ledgerLoading" />
        </section>
      </div>
    </el-drawer>

    <el-dialog v-model="logVisible" width="720px" title="跟进日志" destroy-on-close>
      <div class="dialog-head">
        <strong>{{ logTarget }}</strong>
        <span>展示当前账单相关的提醒、财务与结清记录</span>
      </div>

      <div v-loading="logLoading">
        <div v-if="logEvents.length" class="timeline-list">
          <article v-for="event in logEvents" :key="event.id" class="timeline-item">
            <strong>{{ event.title }}</strong>
            <p>{{ event.detail || '无补充说明' }}</p>
            <div class="timeline-meta">{{ event.operator_name || event.actor_type }} · {{ formatDateTime(event.created_at) }}</div>
          </article>
        </div>
        <el-empty v-else description="暂无日志" />
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
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import LoanLedgerPanel from '../components/LoanLedgerPanel.vue';
import LoanHistoryDialog from '../components/LoanHistoryDialog.vue';
import { ackRepayAttempt, assignLoan, getAdminStats, getLoanAssignees, getLoanLedger, getLoans, getRepaymentStats, getUserDetail, remindLoan } from '../api';
import { readStoredAdminProfile } from '../constants/adminPages';
import { formatCurrency, formatDate, formatDateTime, formatTime } from '../utils/format';

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const actionLoading = ref('');
const drawerVisible = ref(false);
const total = ref(0);
const tableData = ref([]);
const stats = ref({});
const repaymentStats = ref({});
const currentRow = ref(null);
const followNote = ref('');
const followEvents = ref([]);
const logVisible = ref(false);
const logLoading = ref(false);
const logEvents = ref([]);
const logTarget = ref('');
const historyDialogVisible = ref(false);
const historyLoan = ref(null);
const historyBorrowerName = ref('');
const loanLedger = ref(null);
const ledgerLoading = ref(false);
const assignLoading = ref(false);
const assigningReviewer = ref(false);
const reviewAssigneeOptions = ref([]);
const selectedReviewAdminId = ref(null);
const adminProfile = ref(readStoredAdminProfile());
const isSuperAdmin = computed(() => (adminProfile.value?.roles || []).includes('ADMIN'));

const resolveEcardFaceValue = (row) => Number(row?.ecard_face_value || row?.credit_limit || 0);
const resolveRightsPrice = (row) => Number(row?.rights_price || row?.fee_amount || 0);
const resolvePaymentAmount = (row) => Number(
  row?.product_total_price
  || row?.total_repayment_amount
  || (resolveEcardFaceValue(row) + resolveRightsPrice(row))
  || 0
);

const duePresetOptions = [
  { label: '今日', value: 'TODAY' },
  { label: '明日', value: 'TOMORROW' },
  { label: '全部', value: 'ALL' }
];

const followEventTypes = [
  'ADMIN_REMIND',
  'ADMIN_FINANCE_RECONCILE',
  'ADMIN_SETTLED',
  'ADMIN_COLLECTION_NOTE',
  'ADMIN_COLLECT'
];

const filters = reactive({
  phone: '',
  dueDatePreset: 'ALL',
  page: 1,
  size: 10
});

const summaryCards = computed(() => [
  {
    label: '在贷订单',
    value: `${stats.value.disbursed_loans || 0} 单`,
    tip: '当前处于正常还款阶段的订单'
  },
  {
    label: '今日应还',
    value: `${stats.value.due_today_loans || 0} 单`,
    tip: '建议优先完成到期客户提醒'
  },
  {
    label: '实收金额',
    value: formatCurrency(repaymentStats.value.received_amount || 0),
    tip: `减免 ${formatCurrency(repaymentStats.value.reduction_amount || 0)}`
  },
  {
    label: '回款率',
    value: `${Number(repaymentStats.value.repayment_rate || 0).toFixed(2)}%`,
    tip: '按全部在贷与已结清订单口径统计'
  }
]);

const syncDuePresetFromRoute = () => {
  const routePreset = typeof route.query.due === 'string' ? route.query.due.toUpperCase() : 'ALL';
  filters.dueDatePreset = ['TODAY', 'TOMORROW'].includes(routePreset) ? routePreset : 'ALL';
  filters.page = 1;
};

const fetchSummaries = async () => {
  const [statsRes, repaymentStatsRes] = await Promise.all([getAdminStats(), getRepaymentStats()]);
  stats.value = statsRes;
  repaymentStats.value = repaymentStatsRes;
};

const loadReviewAssignees = async () => {
  if (!isSuperAdmin.value) {
    return;
  }
  assignLoading.value = true;
  try {
    reviewAssigneeOptions.value = await getLoanAssignees({ stage: 'review' });
  } finally {
    assignLoading.value = false;
  }
};

const fetchData = async () => {
  loading.value = true;
  try {
    await fetchSummaries();
    const params = {
      scope: 'REPAYMENTS',
      phone: filters.phone || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    };

    if (filters.dueDatePreset !== 'ALL') {
      params.due_date_preset = filters.dueDatePreset;
    }

    const res = await getLoans(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const applyDueFilter = (value) => {
  filters.dueDatePreset = value;
  filters.page = 1;
  const query = value === 'ALL' ? {} : { due: value };
  router.replace({ path: route.path, query });
};

const resetFilters = () => {
  filters.phone = '';
  filters.page = 1;
  if (route.query.due) {
    router.replace({ path: route.path, query: {} });
    return;
  }
  filters.dueDatePreset = 'ALL';
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const filterFollowEvents = (events, loanId) =>
  (events || []).filter(
    (event) => event.loan_id === loanId && followEventTypes.includes(event.event_type)
  );

const loadLoanLedger = async (loanId) => {
  ledgerLoading.value = true;
  loanLedger.value = null;
  try {
    loanLedger.value = await getLoanLedger(loanId);
  } finally {
    ledgerLoading.value = false;
  }
};

const openDrawer = async (row) => {
  currentRow.value = row;
  followNote.value = '';
  drawerVisible.value = true;
  selectedReviewAdminId.value = row.review_admin_id || null;
  loadLoanLedger(row.id).catch(() => {});

  const currentAttempts = Number(row.repay_attempt_count || 0);
  if (currentAttempts > 0) {
    try {
      const ackRes = await ackRepayAttempt(row.id);
      const cleared = Number(ackRes?.cleared_count || 0);
      if (cleared > 0) {
        row.repay_attempt_count = 0;
        if (currentRow.value?.id === row.id) {
          currentRow.value.repay_attempt_count = 0;
        }
        window.dispatchEvent(new CustomEvent('admin-repay-attempt-ack', { detail: { cleared } }));
      }
    } catch (error) {
      // keep original value when ack fails
    }
  }

  try {
    const detail = await getUserDetail(row.user_id);
    followEvents.value = filterFollowEvents(detail.events, row.id);
  } catch (error) {
    followEvents.value = [];
  }
};

const assignReviewOwner = async () => {
  if (!currentRow.value?.id) {
    return;
  }
  if (!selectedReviewAdminId.value) {
    ElMessage.warning('请先选择审核员');
    return;
  }
  assigningReviewer.value = true;
  try {
    const result = await assignLoan(currentRow.value.id, {
      stage: 'review',
      admin_id: selectedReviewAdminId.value
    });
    currentRow.value.review_admin_id = result.assignee_id;
    currentRow.value.review_admin_name = result.assignee_name;
    ElMessage.success(`已改派给 ${result.assignee_name}`);
    await fetchData();
  } finally {
    assigningReviewer.value = false;
  }
};

const openFollowLogs = async (row) => {
  logVisible.value = true;
  logLoading.value = true;
  logTarget.value = `${row.user_name || '未实名'} · 订单 ${row.id}`;
  logEvents.value = [];

  try {
    const detail = await getUserDetail(row.user_id);
    logEvents.value = filterFollowEvents(detail.events, row.id);
  } finally {
    logLoading.value = false;
  }
};

const openHistoryDialog = (row) => {
  historyLoan.value = row.latest_settled_loan || null;
  historyBorrowerName.value = row.user_name || row.user_phone || '';
  historyDialogVisible.value = true;
};

const handleRemind = async () => {
  if (!currentRow.value) {
    return;
  }

  actionLoading.value = 'remind';
  try {
    await remindLoan(currentRow.value.id, {
      note: followNote.value || '已完成还款提醒'
    });
    ElMessage.success('提醒记录已登记');
    drawerVisible.value = false;
    await fetchData();
  } finally {
    actionLoading.value = '';
  }
};

const jumpToFinance = () => {
  if (!currentRow.value?.user_phone) {
    router.push('/financials');
    return;
  }

  drawerVisible.value = false;
  router.push({ path: '/financials', query: { keyword: currentRow.value.user_phone } });
};

const getDueProgressText = (row) => {
  if (!row?.due_date) {
    return '未到期';
  }

  const dueTime = new Date(row.due_date).getTime();
  if (Number.isNaN(dueTime)) {
    return '未到期';
  }

  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const tomorrowStart = todayStart + 24 * 60 * 60 * 1000;
  const dueStart = new Date(new Date(row.due_date).setHours(0, 0, 0, 0)).getTime();

  if (dueStart < todayStart) {
    return '逾期';
  }
  if (dueStart < tomorrowStart) {
    return '到期';
  }
  return '未到期';
};

const getDueProgressTagType = (row) => {
  const progress = getDueProgressText(row);
  if (progress === '逾期') {
    return 'danger';
  }
  if (progress === '到期') {
    return 'warning';
  }
  return 'success';
};

const getPaymentProgressText = (row) => {
  const totalAmount = Number(row.total_repayment_amount || 0);
  const remainingAmount = Number(row.remaining_repayment_amount || 0);
  const paidAmount = Math.max(totalAmount - remainingAmount, 0);

  if (totalAmount > 0 && remainingAmount <= 1e-6) {
    return '已结清';
  }
  if (paidAmount > 1e-6) {
    return '部分支付';
  }
  return '待支付';
};

const getPaymentProgressTagType = (row) => {
  const progress = getPaymentProgressText(row);
  if (progress === '已结清') {
    return 'success';
  }
  if (progress === '部分支付') {
    return 'warning';
  }
  if (progress === '待支付') {
    return 'info';
  }
  return 'info';
};

onMounted(() => {
  syncDuePresetFromRoute();
  fetchData();
  loadReviewAssignees();
});

watch(
  () => route.query.due,
  () => {
    syncDuePresetFromRoute();
    fetchData();
  }
);
</script>

<style scoped>
.sub-text {
  margin-top: 4px;
  color: #7f8da2;
  font-size: 12px;
}

.borrower-name-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.repay-attempt-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #f04438;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}

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

.quick-tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.assignee-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
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

.date-cell {
  display: flex;
  flex-direction: column;
}

.progress-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.bill-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.bill-cell {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(44, 114, 229, 0.08);
  background: linear-gradient(180deg, rgba(246, 250, 255, 1) 0%, rgba(255, 255, 255, 1) 100%);
}

.bill-cell span {
  display: block;
  font-size: 12px;
  color: #7a8aa1;
}

.bill-cell strong {
  display: block;
  margin-top: 10px;
  font-size: 20px;
  color: #16233a;
}

.bill-cell-emphasis {
  border-color: rgba(31, 102, 229, 0.18);
  box-shadow: inset 0 0 0 1px rgba(31, 102, 229, 0.03);
}

.bill-cell-emphasis strong {
  color: #1f66e5;
}

.follow-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.dialog-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: #6b7a90;
  font-size: 12px;
}

.dialog-head strong {
  color: #16233a;
  font-size: 14px;
}

@media (max-width: 1440px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .bill-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
