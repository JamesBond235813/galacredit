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
            @keydown.enter.prevent="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
        <el-form-item label="应还款快捷">
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
        <el-form-item label="还款状态">
          <el-select
            v-model="filters.repaymentStatus"
            class="repayment-status-select"
            placeholder="选择还款状态"
          >
            <el-option
              v-for="item in repaymentStatusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRepaymentStatusSearch">确认</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="订单号" width="96" />
        <el-table-column label="客户" min-width="220">
          <template #default="{ row }">
            <div class="borrower-name-row">
              <span>{{ row.user_name || '未实名' }}</span>
              <span v-if="row.user_blacklist_hit" class="black-badge">黑</span>
              <span v-if="Number(row.repay_attempt_count || 0) > 0" class="repay-attempt-badge">
                {{ Number(row.repay_attempt_count || 0) }}
              </span>
            </div>
            <div class="sub-text">{{ row.user_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="IP审查" width="100">
          <template #default="{ row }"><IpAuditTag @click="openIpAudit(row)" /></template>
        </el-table-column>
        <el-table-column label="审核员" width="130">
          <template #default="{ row }">
            {{ row.review_admin_name || '--' }}
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
        <el-table-column label="逾期费口径" min-width="150">
          <template #default="{ row }">
            <span v-if="Number(row.daily_overdue_fee_snapshot || 0) > 0">
              {{ formatCurrency(row.daily_overdue_fee_snapshot) }} / 天
            </span>
            <span v-else class="sub-text">历史订单兜底</span>
          </template>
        </el-table-column>
        <el-table-column label="应还款时间" min-width="150">
          <template #default="{ row }">
            <div v-if="row.due_date" class="date-cell">
              <div>{{ formatDate(row.due_date) }}</div>
              <div class="sub-text">{{ formatTime(row.due_date) }}</div>
            </div>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="实际还款时间" min-width="150">
          <template #default="{ row }">
            {{ formatDate(row.actual_repayment_date) }}
          </template>
        </el-table-column>
        <el-table-column label="账单进度" width="188">
          <template #default="{ row }">
            <div class="progress-tags">
              <el-tag v-if="isLoanSettled(row)" type="success" effect="light">
                已结清
              </el-tag>
              <template v-else>
                <el-tag :type="getDueProgressTagType(row)" effect="light">
                  {{ getDueProgressText(row) }}
                </el-tag>
                <el-tag :type="getPaymentProgressTagType(row)" effect="light">
                  {{ getPaymentProgressText(row) }}
                </el-tag>
              </template>
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
        <el-table-column label="风控报告" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="openRiskReport(row)">查询</el-button>
          </template>
        </el-table-column>
        <el-table-column label="风险管理" width="110">
          <template #default="{ row }">
            <el-button link type="danger" :disabled="row.user_blacklist_hit" @click="handleBlacklist(row)">一键拉黑</el-button>
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

    <el-drawer v-model="drawerVisible" size="1080px" title="还款跟进" destroy-on-close>
      <div v-if="currentRow" class="identity-drawer-layout">
        <IdentityImagePanel :row="currentRow" />
        <div class="detail-stack">
        <section class="detail-card">
          <h3>客户与账单信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="客户">{{ currentRow.user_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ currentRow.user_phone || '--' }}</el-descriptions-item>
            <el-descriptions-item label="应还款时间">{{ formatDateTime(currentRow.due_date) }}</el-descriptions-item>
            <el-descriptions-item label="实际还款时间">{{ formatDate(currentRow.actual_repayment_date) }}</el-descriptions-item>
            <el-descriptions-item label="提醒次数">{{ currentRow.reminder_count || 0 }} 次</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card">
          <h3>账单概览</h3>
          <div class="bill-grid">
            <article class="bill-cell">
              <span>名义本金</span>
              <strong>{{ formatCurrency(resolveNominalAmount(currentRow)) }}</strong>
            </article>
            <article class="bill-cell">
              <span>上扣费用</span>
              <strong>{{ formatCurrency(resolveUpfrontFee(currentRow)) }}</strong>
            </article>
            <article class="bill-cell">
              <span>MoMo到账</span>
              <strong>{{ formatCurrency(resolveDisbursementAmount(currentRow)) }}</strong>
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
            <article class="bill-cell">
              <span>可用额度</span>
              <strong>{{ formatCurrency(currentRow.available_credit_limit) }}</strong>
            </article>
          </div>
          <div class="extension-prep-box">
            <el-input-number v-model="creditAdjustForm.amount" :min="0" :step="100" :controls="false" placeholder="增加可用额度" />
            <el-input v-model="creditAdjustForm.note" placeholder="额度调整备注" clearable />
            <el-button type="primary" :loading="creditAdjustSaving" @click="submitCreditAdjust">增加额度</el-button>
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
            <el-button plain type="warning" @click="openExtensionDialog">
              展期
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
    <RiskReportDialog v-model="riskDialogVisible" :loading="riskLoading" :report="riskReport" />
    <IpAuditDialog v-model="ipAuditVisible" :loading="ipAuditLoading" :items="ipAuditItems" />
    <el-dialog v-model="extensionVisible" width="460px" title="账单展期" destroy-on-close>
      <el-form label-width="110px">
        <el-form-item label="展期类型">
          <el-radio-group v-model="extensionForm.extension_type">
            <el-radio value="FREE">无附加条件</el-radio>
            <el-radio value="FEE">带息费</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="展期天数">
          <el-input-number v-model="extensionForm.days" :min="1" :max="365" />
        </el-form-item>
        <el-form-item label="减免金额">
          <el-input-number v-model="extensionForm.reduction_amount" :min="0" :disabled="extensionForm.extension_type !== 'FREE'" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="extensionForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="extensionVisible = false">取消</el-button>
        <el-button type="primary" :loading="extensionSaving" @click="submitExtension">确认展期</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import IdentityImagePanel from '../components/IdentityImagePanel.vue';
import IpAuditDialog from '../components/IpAuditDialog.vue';
import IpAuditTag from '../components/IpAuditTag.vue';
import LoanLedgerPanel from '../components/LoanLedgerPanel.vue';
import LoanHistoryDialog from '../components/LoanHistoryDialog.vue';
import RiskReportDialog from '../components/RiskReportDialog.vue';
import { ackRepayAttempt, adjustAvailableCredit, assignLoan, blacklistUser, extendLoan, getLoanAssignees, getLoanLedger, getLoans, getRepaymentStats, getRiskReportByUser, getUserDetail, getUserIpAudit, remindLoan } from '../api';
import { readStoredAdminProfile } from '../constants/adminPages';
import { formatCurrency, formatDate, formatDateTime, formatTime } from '../utils/format';

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const actionLoading = ref('');
const drawerVisible = ref(false);
const total = ref(0);
const tableData = ref([]);
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
const riskDialogVisible = ref(false);
const riskLoading = ref(false);
const riskReport = ref(null);
const ipAuditVisible = ref(false);
const ipAuditLoading = ref(false);
const ipAuditItems = ref([]);
const extensionVisible = ref(false);
const extensionSaving = ref(false);
const extensionForm = reactive({ extension_type: 'FREE', days: 3, reduction_amount: 0, note: '' });
const creditAdjustSaving = ref(false);
const creditAdjustForm = reactive({ amount: 0, note: '' });
const assignLoading = ref(false);
const assigningReviewer = ref(false);
const reviewAssigneeOptions = ref([]);
const selectedReviewAdminId = ref(null);
const adminProfile = ref(readStoredAdminProfile());
const isSuperAdmin = computed(() => (adminProfile.value?.roles || []).includes('ADMIN'));

const resolveEcardFaceValue = (row) => Number(row?.ecard_face_value || row?.credit_limit || 0);
const resolveNominalAmount = (row) => Number(row?.nominal_loan_amount || row?.total_repayment_amount || row?.credit_limit || resolveEcardFaceValue(row));
const resolveRightsPrice = (row) => Number(row?.rights_price || row?.fee_amount || 0);
const resolveUpfrontFee = (row) => Number(row?.upfront_fee_amount || row?.fee_amount || resolveRightsPrice(row));
const resolveDisbursementAmount = (row) => Number(row?.actual_disbursement_amount || row?.ecard_face_value || Math.max(resolveNominalAmount(row) - resolveUpfrontFee(row), 0));
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

const repaymentStatusOptions = [
  { label: '全部', value: 'ALL' },
  { label: '未到期', value: 'NOT_DUE' },
  { label: '今日到期', value: 'DUE_TODAY' },
  { label: '已逾期', value: 'OVERDUE' },
  { label: '待支付', value: 'UNPAID' },
  { label: '部分支付', value: 'PARTIAL_PAID' },
  { label: '已结清', value: 'SETTLED' }
];

const followEventTypes = [
  'ADMIN_REVIEW_NOTE',
  'ADMIN_REMIND',
  'ADMIN_FINANCE_RECONCILE',
  'ADMIN_SETTLED',
  'ADMIN_COLLECTION_NOTE',
  'ADMIN_COLLECT'
];

const filters = reactive({
  phone: '',
  dueDatePreset: 'ALL',
  dueDateRange: [],
  actualRepaymentRange: [],
  repaymentStatus: 'ALL',
  page: 1,
  size: 10
});
const activeFilterScope = ref('due');

const selectedDueOption = computed(() =>
  duePresetOptions.find((item) => item.value === filters.dueDatePreset) || duePresetOptions[2]
);
const activeSummaryLabel = computed(() => {
  if (activeFilterScope.value === 'actualRepayment') {
    return '实际还款时间区间';
  }
  if (activeFilterScope.value === 'dueRange') {
    return '应还款时间区间';
  }
  if (activeFilterScope.value === 'keyword') {
    return '当前搜索结果';
  }
  if (activeFilterScope.value === 'repaymentStatus') {
    const selected = repaymentStatusOptions.find((item) => item.value === filters.repaymentStatus);
    return `${selected?.label || '还款状态'}筛选`;
  }
  return `${selectedDueOption.value.label}时间区间`;
});

const summaryCards = computed(() => [
  {
    label: '应还订单',
    value: `${repaymentStats.value.receivable_order_count || 0} 单`,
    tip: `${activeSummaryLabel.value}内的应还订单`
  },
  {
    label: '应还客户',
    value: `${repaymentStats.value.receivable_user_count || 0} 人`,
    tip: `应还金额 ${formatCurrency(repaymentStats.value.receivable_amount || 0)}`
  },
  {
    label: '实收金额',
    value: formatCurrency(repaymentStats.value.received_amount || 0),
    tip: `减免 ${formatCurrency(repaymentStats.value.reduction_amount || 0)} · 其他费用 ${formatCurrency(repaymentStats.value.other_fee_amount || 0)}`
  },
  {
    label: '回款率',
    value: `${Number(repaymentStats.value.repayment_rate || 0).toFixed(2)}%`,
    tip: '实收金额 / 当前区间应还款额'
  }
]);

const syncDuePresetFromRoute = () => {
  const routePreset = typeof route.query.due === 'string' ? route.query.due.toUpperCase() : 'ALL';
  filters.dueDatePreset = ['TODAY', 'TOMORROW'].includes(routePreset) ? routePreset : 'ALL';
  filters.page = 1;
};

const buildRepaymentFilterParams = (scope = activeFilterScope.value) => {
  const params = {};
  if (scope === 'keyword') {
    params.phone = filters.phone || undefined;
    return params;
  }
  if (scope === 'actualRepayment') {
    if (filters.actualRepaymentRange.length === 2) {
      params.actual_repayment_start = filters.actualRepaymentRange[0];
      params.actual_repayment_end = filters.actualRepaymentRange[1];
    }
    return params;
  }
  if (scope === 'dueRange') {
    if (filters.dueDateRange.length === 2) {
      params.due_date_start = filters.dueDateRange[0];
      params.due_date_end = filters.dueDateRange[1];
    }
    return params;
  }
  if (scope === 'repaymentStatus') {
    if (filters.repaymentStatus !== 'ALL') {
      params.repayment_status = filters.repaymentStatus;
    }
    return params;
  }
  if (filters.dueDatePreset !== 'ALL') {
    params.due_date_preset = filters.dueDatePreset;
  }
  return params;
};

const fetchSummaries = async () => {
  const params = buildRepaymentFilterParams();
  delete params.phone;
  repaymentStats.value = await getRepaymentStats(params);
};

const ensureActualRepaymentRange = () => {
  if (filters.actualRepaymentRange.length === 2) {
    return true;
  }
  ElMessage.warning('请先选择实际还款时间区间');
  return false;
};

const ensureDueDateRange = () => {
  if (filters.dueDateRange.length === 2) {
    return true;
  }
  ElMessage.warning('请先选择应还款时间区间');
  return false;
};

const applyQueryScope = (scope) => {
  activeFilterScope.value = scope;
  filters.page = 1;
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
      ...buildRepaymentFilterParams(),
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    };

    const res = await getLoans(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  applyQueryScope('keyword');
  fetchData();
};

const handleActualRepaymentSearch = () => {
  if (!ensureActualRepaymentRange()) {
    return;
  }
  applyQueryScope('actualRepayment');
  fetchData();
};

const handleDueDateSearch = () => {
  if (!ensureDueDateRange()) {
    return;
  }
  applyQueryScope('dueRange');
  fetchData();
};

const handleRepaymentStatusSearch = () => {
  applyQueryScope('repaymentStatus');
  fetchData();
};

const applyDueFilter = (value) => {
  activeFilterScope.value = 'due';
  filters.dueDatePreset = value;
  filters.page = 1;
  const query = value === 'ALL' ? {} : { due: value };
  router.replace({ path: route.path, query });
};

const resetFilters = () => {
  activeFilterScope.value = 'due';
  filters.phone = '';
  filters.dueDateRange = [];
  filters.actualRepaymentRange = [];
  filters.repaymentStatus = 'ALL';
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
    (event) => event.loan_id === loanId && (
      followEventTypes.includes(event.event_type) || /备注/.test(`${event.title || ''}${event.detail || ''}`)
    )
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
    currentRow.value = {
      ...currentRow.value,
      id_card_front_image_url: detail.id_card_front_image_url,
      id_card_back_image_url: detail.id_card_back_image_url,
      face_image_url: detail.face_image_url
    };
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

const openRiskReport = async (row) => {
  riskDialogVisible.value = true;
  riskLoading.value = true;
  riskReport.value = null;
  try {
    riskReport.value = await getRiskReportByUser({ user_id: row.user_id });
  } catch (error) {
    riskDialogVisible.value = false;
  } finally {
    riskLoading.value = false;
  }
};

const openIpAudit = async (row) => {
  ipAuditVisible.value = true;
  ipAuditLoading.value = true;
  ipAuditItems.value = [];
  try {
    const result = await getUserIpAudit(row.user_id);
    ipAuditItems.value = result.items || [];
  } finally {
    ipAuditLoading.value = false;
  }
};

const handleBlacklist = async (row) => {
  try {
    await ElMessageBox.confirm(`确认将 ${row.user_name || row.user_phone} 加入黑名单？`, '一键拉黑', {
      type: 'warning',
      confirmButtonText: '确认拉黑',
      cancelButtonText: '取消'
    });
  } catch (error) {
    return;
  }
  await blacklistUser(row.user_id, { note: '后台一键拉黑' });
  ElMessage.success('已加入黑名单');
  fetchData();
};

const openExtensionDialog = () => {
  extensionForm.extension_type = 'FREE';
  extensionForm.days = 3;
  extensionForm.reduction_amount = 0;
  extensionForm.note = '';
  extensionVisible.value = true;
};

const submitExtension = async () => {
  if (!currentRow.value?.id) {
    return;
  }
  extensionSaving.value = true;
  try {
    await extendLoan(currentRow.value.id, extensionForm);
    ElMessage.success('展期成功');
    extensionVisible.value = false;
    drawerVisible.value = false;
    fetchData();
  } finally {
    extensionSaving.value = false;
  }
};

const submitCreditAdjust = async () => {
  if (!currentRow.value?.id || Number(creditAdjustForm.amount || 0) <= 0) {
    ElMessage.warning('请填写需要增加的可用额度');
    return;
  }
  creditAdjustSaving.value = true;
  try {
    await adjustAvailableCredit(currentRow.value.id, {
      amount: Number(creditAdjustForm.amount || 0),
      note: creditAdjustForm.note || ''
    });
    ElMessage.success('可用额度已增加');
    creditAdjustForm.amount = 0;
    creditAdjustForm.note = '';
    fetchData();
  } finally {
    creditAdjustSaving.value = false;
  }
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

const isLoanSettled = (row) => {
  const totalAmount = Number(row?.total_repayment_amount || 0);
  const remainingAmount = Number(row?.remaining_repayment_amount || 0);
  return row?.status === 'SETTLED' || (totalAmount > 0 && remainingAmount <= 1e-6);
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

  if (isLoanSettled(row)) {
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

.repayment-status-select {
  width: 150px;
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

.extension-prep-box {
  display: grid;
  grid-template-columns: 160px minmax(180px, 1fr) auto;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
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

  .extension-prep-box {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
