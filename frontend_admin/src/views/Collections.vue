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
        <el-form-item label="逾期天数">
          <div class="overdue-filter-box">
            <div class="range-row">
              <span class="range-label">逾期</span>
              <el-input-number v-model="filters.overdueMinDays" :min="1" :controls="false" class="day-input" />
              <span class="range-label">天 到 逾期</span>
              <el-input-number v-model="filters.overdueMaxDays" :min="1" :controls="false" class="day-input" />
              <span class="range-label">天</span>
              <el-button type="primary" @click="fetchData">查询</el-button>
            </div>
            <div class="quick-tag-row">
              <button
                v-for="item in quickDayOptions"
                :key="item.value"
                type="button"
                class="quick-tag"
                :class="{ 'quick-tag-active': activeQuickDay === item.value }"
                @click="applyQuickFilter(item.value)"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
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
        <el-table-column label="催收员" width="130">
          <template #default="{ row }">
            {{ row.collection_admin_name || '--' }}
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
        <el-table-column label="逾期天数" width="110">
          <template #default="{ row }">
            {{ getOverdueDays(row) }}
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
        <el-table-column label="违约金" min-width="110">
          <template #default="{ row }">
            {{ formatCurrency(row.penalty_amount) }}
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
        <el-table-column label="催收记录" min-width="138">
          <template #default="{ row }">
            <div>{{ row.collection_count || 0 }} 次</div>
            <div class="sub-text">{{ formatDateTime(row.last_collection_at) }}</div>
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
            <el-button link type="danger" @click="openDrawer(row)">催收处理</el-button>
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

    <el-drawer v-model="drawerVisible" size="1080px" title="逾期催收处理" destroy-on-close>
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
            <el-descriptions-item label="逾期天数">{{ getOverdueDays(currentRow) }}</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card">
          <h3>逾期账单概览</h3>
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
              <span>违约金</span>
              <strong>{{ formatCurrency(currentRow.penalty_amount) }}</strong>
            </article>
            <article class="bill-cell">
              <span>总还款额</span>
              <strong>{{ formatCurrency(currentRow.total_repayment_amount) }}</strong>
            </article>
            <article class="bill-cell">
              <span>已还款额</span>
              <strong>{{ formatCurrency(currentRow.repaid_amount) }}</strong>
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
            <el-button :loading="overdueDisplaySaving" @click="submitOverdueDisplayClose">关闭逾期显示</el-button>
            <el-input-number v-model="creditAdjustForm.amount" :min="0" :step="100" :controls="false" placeholder="增加可用额度" />
            <el-input v-model="creditAdjustForm.note" placeholder="额度调整备注" clearable />
            <el-button type="primary" :loading="creditAdjustSaving" @click="submitCreditAdjust">增加额度</el-button>
          </div>
        </section>

        <section class="detail-card">
          <h3>全部经纬度记录</h3>
          <el-table :data="locationEvents" size="small">
            <el-table-column prop="lon_lat" label="经纬度" min-width="150" />
            <el-table-column label="行政区划" min-width="180">
              <template #default="{ row }">
                {{ [row.lon_lat_province, row.lon_lat_city, row.lon_lat_district].filter(Boolean).join(' / ') || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="lon_lat_detail" label="地址" min-width="220" />
            <el-table-column label="时间" width="160">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </section>

        <section class="detail-card">
          <h3>催收登记</h3>
          <div v-if="isSuperAdmin" class="assignee-row">
            <el-select
              v-model="selectedCollectionAdminId"
              placeholder="选择催收员"
              filterable
              :loading="assignLoading"
              style="width: 220px"
            >
              <el-option v-for="item in collectionAssigneeOptions" :key="item.id" :label="item.username" :value="item.id" />
            </el-select>
            <el-button type="primary" plain :loading="assigningCollector" @click="assignCollectionOwner">
              改派负责人
            </el-button>
          </div>
          <el-form label-width="92px">
            <el-form-item label="催收备注">
              <el-input
                v-model="collectionNote"
                type="textarea"
                :rows="3"
                placeholder="填写本次催收结果、客户反馈、承诺还款时间或失败原因"
              />
            </el-form-item>
          </el-form>

          <div class="follow-actions">
            <el-button
              type="danger"
              :loading="actionLoading === 'collect'"
              @click="handleCollect"
            >
              登记催收
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

    <el-dialog v-model="logVisible" width="720px" title="催收日志" destroy-on-close>
      <div class="dialog-head">
        <strong>{{ logTarget }}</strong>
        <span>展示当前账单相关的催收与财务记录</span>
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
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import IdentityImagePanel from '../components/IdentityImagePanel.vue';
import IpAuditDialog from '../components/IpAuditDialog.vue';
import IpAuditTag from '../components/IpAuditTag.vue';
import LoanLedgerPanel from '../components/LoanLedgerPanel.vue';
import LoanHistoryDialog from '../components/LoanHistoryDialog.vue';
import RiskReportDialog from '../components/RiskReportDialog.vue';
import { ackRepayAttempt, adjustAvailableCredit, assignLoan, blacklistUser, collectLoan, extendLoan, getAdminStats, getLoanAssignees, getLoanLedger, getLoans, getRiskReportByUser, getUserDetail, getUserIpAudit, updateOverdueDisplay } from '../api';
import { readStoredAdminProfile } from '../constants/adminPages';
import { formatCurrency, formatDate, formatDateTime, formatTime } from '../utils/format';

const router = useRouter();

const loading = ref(false);
const actionLoading = ref('');
const drawerVisible = ref(false);
const total = ref(0);
const tableData = ref([]);
const stats = ref({});
const currentRow = ref(null);
const collectionNote = ref('');
const followEvents = ref([]);
const locationEvents = ref([]);
const logVisible = ref(false);
const logLoading = ref(false);
const logEvents = ref([]);
const logTarget = ref('');
const activeQuickDay = ref('ALL');
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
const overdueDisplaySaving = ref(false);
const assignLoading = ref(false);
const assigningCollector = ref(false);
const collectionAssigneeOptions = ref([]);
const selectedCollectionAdminId = ref(null);
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

const quickDayOptions = [
  { label: '15天', value: 15 },
  { label: '30天', value: 30 },
  { label: '45天', value: 45 },
  { label: '全部', value: 'ALL' }
];

const followEventTypes = [
  'ADMIN_REVIEW_NOTE',
  'ADMIN_COLLECTION_NOTE',
  'ADMIN_COLLECT',
  'ADMIN_FINANCE_RECONCILE',
  'ADMIN_SETTLED',
  'ADMIN_REMIND'
];

const filters = reactive({
  phone: '',
  dueDateRange: [],
  actualRepaymentRange: [],
  overdueMinDays: null,
  overdueMaxDays: null,
  page: 1,
  size: 10
});

const visibleRemainingAmount = computed(() =>
  tableData.value.reduce((sum, row) => sum + Number(row.remaining_repayment_amount || 0), 0)
);

const visiblePenaltyAmount = computed(() =>
  tableData.value.reduce((sum, row) => sum + Number(row.penalty_amount || 0), 0)
);

const summaryCards = computed(() => [
  {
    label: '逾期订单',
    value: `${stats.value.overdue_loans || 0} 单`,
    tip: '仅展示已进入催收阶段的账单'
  },
  {
    label: '今日已催收',
    value: `${stats.value.today_collections || 0} 次`,
    tip: '按后台催收登记次数统计'
  },
  {
    label: '当前页待回收',
    value: formatCurrency(visibleRemainingAmount.value),
    tip: '按当前筛选结果统计'
  },
  {
    label: '当前页违约金',
    value: formatCurrency(visiblePenaltyAmount.value),
    tip: '用于判断优先催收账单'
  }
]);

const loadCollectionAssignees = async () => {
  if (!isSuperAdmin.value) {
    return;
  }
  assignLoading.value = true;
  try {
    collectionAssigneeOptions.value = await getLoanAssignees({ stage: 'collection' });
  } finally {
    assignLoading.value = false;
  }
};

const syncQuickDayState = () => {
  if (filters.overdueMinDays === null && filters.overdueMaxDays === null) {
    activeQuickDay.value = 'ALL';
    return;
  }

  if (filters.overdueMinDays !== null && filters.overdueMinDays === filters.overdueMaxDays) {
    const day = Number(filters.overdueMinDays);
    activeQuickDay.value = [15, 30, 45].includes(day) ? day : null;
    return;
  }

  activeQuickDay.value = null;
};

const fetchData = async () => {
  if (
    filters.overdueMinDays !== null
    && filters.overdueMaxDays !== null
    && Number(filters.overdueMinDays) > Number(filters.overdueMaxDays)
  ) {
    ElMessage.warning('最小逾期天数不能大于最大逾期天数');
    return;
  }

  loading.value = true;
  try {
    stats.value = await getAdminStats();
    const params = {
      scope: 'OVERDUE',
      phone: filters.phone || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    };

    if (filters.overdueMinDays !== null) {
      params.overdue_min_days = Number(filters.overdueMinDays);
    }
    if (filters.overdueMaxDays !== null) {
      params.overdue_max_days = Number(filters.overdueMaxDays);
    }
    if (filters.dueDateRange.length === 2) {
      params.due_date_start = filters.dueDateRange[0];
      params.due_date_end = filters.dueDateRange[1];
    }
    if (filters.actualRepaymentRange.length === 2) {
      params.actual_repayment_start = filters.actualRepaymentRange[0];
      params.actual_repayment_end = filters.actualRepaymentRange[1];
    }

    const res = await getLoans(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    syncQuickDayState();
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.phone = '';
  filters.dueDateRange = [];
  filters.actualRepaymentRange = [];
  filters.overdueMinDays = null;
  filters.overdueMaxDays = null;
  filters.page = 1;
  activeQuickDay.value = 'ALL';
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

const applyQuickFilter = (value) => {
  filters.page = 1;

  if (value === 'ALL') {
    filters.overdueMinDays = null;
    filters.overdueMaxDays = null;
  } else {
    filters.overdueMinDays = value;
    filters.overdueMaxDays = value;
  }

  activeQuickDay.value = value;
  fetchData();
};

const getOverdueDays = (row) => {
  if (!row?.due_date) {
    return '--';
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const dueDate = new Date(row.due_date);
  dueDate.setHours(0, 0, 0, 0);

  const days = Math.max(Math.floor((today - dueDate) / (1000 * 60 * 60 * 24)), 1);
  return `${days} 天`;
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
  collectionNote.value = row.collection_note || '';
  drawerVisible.value = true;
  selectedCollectionAdminId.value = row.collection_admin_id || null;
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
    locationEvents.value = (detail.events || []).filter((item) => item.lon_lat);
  } catch (error) {
    followEvents.value = [];
    locationEvents.value = [];
  }
};

const assignCollectionOwner = async () => {
  if (!currentRow.value?.id) {
    return;
  }
  if (!selectedCollectionAdminId.value) {
    ElMessage.warning('请先选择催收员');
    return;
  }
  assigningCollector.value = true;
  try {
    const result = await assignLoan(currentRow.value.id, {
      stage: 'collection',
      admin_id: selectedCollectionAdminId.value
    });
    currentRow.value.collection_admin_id = result.assignee_id;
    currentRow.value.collection_admin_name = result.assignee_name;
    ElMessage.success(`已改派给 ${result.assignee_name}`);
    await fetchData();
  } finally {
    assigningCollector.value = false;
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

const submitOverdueDisplayClose = async () => {
  if (!currentRow.value?.id) {
    return;
  }
  overdueDisplaySaving.value = true;
  try {
    await updateOverdueDisplay(currentRow.value.id, { overdue_hidden: true, note: '展期前关闭逾期显示' });
    ElMessage.success('逾期显示已关闭');
    fetchData();
  } finally {
    overdueDisplaySaving.value = false;
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

const handleCollect = async () => {
  if (!currentRow.value) {
    return;
  }

  actionLoading.value = 'collect';
  try {
    await collectLoan(currentRow.value.id, {
      note: collectionNote.value || '已完成本次逾期催收'
    });
    ElMessage.success('催收记录已登记');
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

onMounted(() => {
  fetchData();
  loadCollectionAssignees();
});

watch(
  () => [filters.overdueMinDays, filters.overdueMaxDays],
  () => {
    syncQuickDayState();
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

.overdue-filter-box {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.range-row,
.quick-tag-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.range-label {
  font-size: 13px;
  color: #607089;
  white-space: nowrap;
}

.day-input {
  width: 92px;
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
  border-color: rgba(220, 95, 95, 0.2);
  box-shadow: inset 0 0 0 1px rgba(220, 95, 95, 0.03);
}

.bill-cell-emphasis strong {
  color: #d85c5c;
}

.follow-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.extension-prep-box {
  display: grid;
  grid-template-columns: auto 160px minmax(180px, 1fr) auto;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
}

.assignee-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
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
