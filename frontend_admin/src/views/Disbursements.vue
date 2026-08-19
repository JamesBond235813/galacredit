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
        <el-form-item :label="tr('搜索', 'Search')">
          <el-input
            v-model="filters.phone"
            :placeholder="tr('手机号 / 姓名 / 身份证号', 'Phone / name / ID')"
            clearable
            @keyup.enter="fetchData"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">{{ tr('查询', 'Search') }}</el-button>
          <el-button @click="resetFilters">{{ tr('重置', 'Reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" :label="tr('订单号', 'Loan ID')" width="96" />
        <el-table-column :label="tr('客户信息', 'Borrower')" min-width="220">
          <template #default="{ row }">
            <div class="customer-name-row">
              <span>{{ row.user_name || '未实名' }}</span>
              <el-tooltip
                v-if="row.user_risk_list_hit"
                :content="row.user_risk_list_reason || '命中风险名单'"
                placement="top"
              >
                <span class="risk-list-badge">风</span>
              </el-tooltip>
            </div>
            <div class="sub-text">{{ row.user_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('IP审查', 'IP review')" width="100">
          <template #default="{ row }">
            <IpAuditTag @click="openIpAudit(row)" />
          </template>
        </el-table-column>
        <el-table-column :label="tr('复购次数', 'Repeat loans')" width="120">
          <template #default="{ row }">
            <div>{{ row.relend_label || '首购' }}</div>
            <el-button
              v-if="row.latest_settled_loan"
              link
              type="primary"
              class="history-link"
              @click="openHistoryDialog(row)"
            >
              {{ tr('历史账单', 'Loan history') }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column :label="tr('名义本金', 'Nominal principal')" min-width="126">
          <template #default="{ row }">
            {{ formatCurrency(resolveNominalAmount(row)) }}
          </template>
        </el-table-column>
        <el-table-column :label="tr('贷款产品', 'Loan product')" min-width="220">
          <template #default="{ row }">
            <div>{{ row.product_name || '--' }}</div>
            <div class="sub-text">
              {{ tr('上扣费用', 'Upfront fee') }} {{ formatCurrency(row.upfront_fee_amount || row.fee_amount) }} · {{ tr('到期日第', 'Due on day') }} {{ row.repayment_due_day || row.term_days || '--' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('MoMo到账 / 应还', 'MoMo received / due')" min-width="150">
          <template #default="{ row }">
            <div>{{ formatCurrency(resolvePaymentAmount(row)) }}</div>
            <div class="sub-text">{{ tr('应还总额', 'Total repayment') }} {{ formatCurrency(resolvePaymentAmount(row)) }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('风控报告', 'Risk report')" width="140">
          <template #default="{ row }">
            <el-button link type="primary" @click="openRiskReport(row)">查询</el-button>
          </template>
        </el-table-column>
        <el-table-column :label="tr('风险管理', 'Risk actions')" width="110">
          <template #default="{ row }">
            <el-button link type="danger" :disabled="row.user_blacklist_hit" @click="handleBlacklist(row)">一键拉黑</el-button>
          </template>
        </el-table-column>
        <el-table-column :label="tr('申请时间', 'Application time')" min-width="150">
          <template #default="{ row }">
            <div v-if="getOrderTime(row)" class="date-cell">
              <div>{{ formatDate(getOrderTime(row)) }}</div>
              <div class="sub-text">{{ formatTime(getOrderTime(row)) }}</div>
            </div>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column :label="tr('操作', 'Actions')" width="310" fixed="right" align="center">
          <template #default="{ row }">
            <div class="row-action-cell">
              <el-button
                size="small"
                type="primary"
                :loading="actionLoading === getDisburseActionKey(row.id)"
                :disabled="row.user_blacklist_hit"
                @click="handleDisburse(row)"
              >
                {{ tr('MoMo放款', 'Disburse via MoMo') }}
              </el-button>
              <el-button size="small" text type="danger" @click="handleRejectCard(row)">{{ tr('拒绝放款', 'Reject') }}</el-button>
              <el-button size="small" text type="warning" @click="handleCloseCard(row)">{{ tr('退回待下单', 'Return to product selection') }}</el-button>
              <el-button size="small" text type="primary" @click="openDrawer(row)">{{ tr('查看更多', 'Details') }}</el-button>
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

    <el-drawer v-model="drawerVisible" size="1080px" title="待MoMo放款处理" destroy-on-close>
      <div v-if="form.id" class="identity-drawer-layout">
        <IdentityImagePanel :row="currentRow || {}" />
        <div class="detail-stack">
        <section class="detail-card">
          <h3>客户与订单信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用户">{{ currentRow?.user_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ currentRow?.user_phone || '--' }}</el-descriptions-item>
            <el-descriptions-item label="状态">待MoMo放款</el-descriptions-item>
            <el-descriptions-item label="下单商品">{{ currentRow?.product_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="名义本金">{{ formatCurrency(currentSummary.nominalAmount) }}</el-descriptions-item>
            <el-descriptions-item label="上扣费用">{{ formatCurrency(currentSummary.upfrontFeeAmount) }}</el-descriptions-item>
            <el-descriptions-item label="MoMo到账">{{ formatCurrency(currentSummary.disbursementAmount) }}</el-descriptions-item>
            <el-descriptions-item label="账期">{{ currentSummary.termDays ? `${currentSummary.termDays} 天` : '--' }}</el-descriptions-item>
            <el-descriptions-item label="预计付款日">{{ currentSummary.dueDateText }}</el-descriptions-item>
            <el-descriptions-item label="下单时间">{{ formatDateTime(getOrderTime(currentRow)) }}</el-descriptions-item>
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
                placeholder="填写放款前确认信息、MoMo核验说明或审批备注"
              />
            </el-form-item>
          </el-form>

          <div class="preview-grid">
            <article class="preview-card">
              <span>名义本金</span>
              <strong>{{ formatCurrency(currentSummary.nominalAmount) }}</strong>
            </article>
            <article class="preview-card">
              <span>上扣费用</span>
              <strong>{{ formatCurrency(currentSummary.upfrontFeeAmount) }}</strong>
            </article>
            <article class="preview-card">
              <span>MoMo到账</span>
              <strong>{{ formatCurrency(currentSummary.disbursementAmount) }}</strong>
            </article>
            <article class="preview-card">
              <span>到期应付</span>
              <strong>{{ formatCurrency(currentSummary.installmentAmount) }}</strong>
            </article>
          </div>

          <div class="due-preview">
            <span class="due-preview-label">预计付款日</span>
            <strong>{{ currentSummary.dueDateText }}</strong>
            <p>规则：放款日为第 1 天，按起息日与到期日参数生成还款计划。</p>
          </div>

          <div class="drawer-footer">
            <el-button @click="drawerVisible = false">关闭</el-button>
            <el-button type="primary" :loading="saving" @click="saveConfig">保存订单备注</el-button>
          </div>
        </section>

        <section class="detail-card">
          <h3>MoMo 放款确认</h3>
          <div class="callout-card">
            <div class="callout-title">放款前请核对</div>
            <p>当前页面只处理待放款订单。确认后将通过 MoMo provider 支付实际到账金额，并生成正式还款账单。</p>
          </div>
          <div class="action-row">
            <el-button
              type="primary"
              :loading="actionLoading === getDisburseActionKey(form.id)"
              @click="handleDisburse()"
            >
              MoMo放款
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
      </div>
    </el-drawer>

    <LoanHistoryDialog
      v-model="historyDialogVisible"
      :loan="historyLoan"
      :borrower-name="historyBorrowerName"
    />
    <RiskReportDialog v-model="riskDialogVisible" :loading="riskLoading" :report="riskReport" />
    <CompositeRiskReportDialog
      v-model="compositeRiskDialogVisible"
      :loading="compositeRiskLoading"
      :report="compositeRiskReport"
    />
    <IpAuditDialog v-model="ipAuditVisible" :loading="ipAuditLoading" :items="ipAuditItems" />
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import LoanHistoryDialog from '../components/LoanHistoryDialog.vue';
import IdentityImagePanel from '../components/IdentityImagePanel.vue';
import IpAuditDialog from '../components/IpAuditDialog.vue';
import IpAuditTag from '../components/IpAuditTag.vue';
import RiskReportDialog from '../components/RiskReportDialog.vue';
import CompositeRiskReportDialog from '../components/CompositeRiskReportDialog.vue';
import { blacklistUser, closeCardReissue, disburseLoan, getAdminStats, getCompositeRiskReportByUser, getLoans, getRiskReportByUser, getUserDetail, getUserIpAudit, rejectCardLoan, updateLoan } from '../api';
import { formatCurrency, formatDate, formatDateTime, formatTime } from '../utils/format';
import { tr } from '../i18n/adminLocale';

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
const riskDialogVisible = ref(false);
const riskLoading = ref(false);
const riskReport = ref(null);
const compositeRiskDialogVisible = ref(false);
const compositeRiskLoading = ref(false);
const compositeRiskReport = ref(null);
const ipAuditVisible = ref(false);
const ipAuditLoading = ref(false);
const ipAuditItems = ref([]);

const filters = reactive({
  phone: '',
  page: 1,
  size: 10
});

const form = reactive({
  id: null,
  review_note: ''
});

const resolveEcardFaceValue = (source) => Number(source?.ecard_face_value ?? source?.credit_limit ?? 0);
const resolveNominalAmount = (source) => Number(source?.nominal_loan_amount || source?.total_repayment_amount || source?.credit_limit || resolveEcardFaceValue(source));
const resolveUpfrontFeeAmount = (source) => Number(source?.upfront_fee_amount || source?.fee_amount || resolveNominalAmount(source) * Number(source?.fee_rate || 0));
const resolveDisbursementAmount = (source) => Number(source?.actual_disbursement_amount || Math.max(resolveNominalAmount(source) - resolveUpfrontFeeAmount(source), 0));
const resolveRightsPrice = (source) => Number(source?.rights_price || 0);
const resolvePaymentAmount = (source) => {
  const fromSnapshot = Number(source?.total_repayment_amount || source?.product_total_price || 0);
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
const resolveInstallmentPeriods = (source) => Math.max(Number(source?.installment_count || source?.installment_periods || 1), 1);
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
  tableData.value.reduce((sum, row) => sum + resolveNominalAmount(row), 0)
);

const visibleRepaymentAmount = computed(() =>
  tableData.value.reduce((sum, row) => sum + resolvePaymentAmount(row), 0)
);

const getOrderTime = (row) => row?.ordered_at || row?.created_at || null;

const summaryCards = computed(() => [
  {
    label: tr('待MoMo放款订单', 'Pending MoMo loans'),
    value: `${stats.value.withdrawing_loans || 0} ${tr('单', 'loans')}`,
    tip: tr('等待审核确认后向借款人支付实际到账金额', 'Awaiting approval to send the actual disbursement amount')
  },
  {
    label: tr('当前页名义本金', 'Visible nominal principal'),
    value: formatCurrency(visiblePrincipalAmount.value),
    tip: tr('按当前筛选结果统计', 'Based on the current filter')
  },
  {
    label: tr('当前页应还总额', 'Visible total repayment'),
    value: formatCurrency(visibleRepaymentAmount.value),
    tip: tr('放款确认后将进入正式还款账单', 'The repayment schedule starts after disbursement confirmation')
  },
  {
    label: tr('MoMo渠道状态', 'MoMo provider status'),
    value: tr('待连接', 'Ready for integration'),
    tip: tr('当前使用可替换的模拟MoMo provider', 'Using a replaceable mock MoMo provider')
  }
]);

const buildSummary = (source) => {
  const ecardFaceValue = resolveEcardFaceValue(source);
  const rightsPrice = resolveRightsPrice(source);
  const paymentAmount = resolvePaymentAmount(source);
  const termDays = resolveTermDays(source);
  const installmentPeriods = resolveInstallmentPeriods(source);

  return {
    nominalAmount: resolveNominalAmount(source),
    upfrontFeeAmount: resolveUpfrontFeeAmount(source),
    disbursementAmount: resolveDisbursementAmount(source),
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
    currentRow.value = {
      ...currentRow.value,
      id_card_front_image_url: detail.id_card_front_image_url,
      id_card_back_image_url: detail.id_card_back_image_url,
      face_image_url: detail.face_image_url
    };
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

const openRiskReport = async (row) => {
  riskDialogVisible.value = true;
  riskLoading.value = true;
  riskReport.value = null;
  try {
    riskReport.value = await getCompositeRiskReportByUser({ user_id: row.user_id });
  } catch (error) {
    riskDialogVisible.value = false;
  } finally {
    riskLoading.value = false;
  }
};

const openCompositeRiskReport = async (row) => {
  compositeRiskDialogVisible.value = true;
  compositeRiskLoading.value = true;
  compositeRiskReport.value = null;
  try {
    compositeRiskReport.value = await getCompositeRiskReportByUser({ user_id: row.user_id });
  } catch (error) {
    compositeRiskDialogVisible.value = false;
  } finally {
    compositeRiskLoading.value = false;
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

const handleRejectCard = async (row) => {
  try {
    await ElMessageBox.confirm(`确认拒绝 ${row.user_name || row.user_phone} 的放款？`, '拒绝放款', {
      type: 'warning',
      confirmButtonText: '确认拒绝',
      cancelButtonText: '取消'
    });
  } catch (error) {
    return;
  }
  await rejectCardLoan(row.id, { note: '后台拒绝MoMo放款' });
  ElMessage.success('已拒绝放款');
  fetchData();
};

const handleCloseCard = async (row) => {
  try {
    await ElMessageBox.confirm(`确认将 ${row.user_name || row.user_phone} 退回待下单，并清除本次错误下单商品信息？`, '退回待下单', {
      type: 'warning',
      confirmButtonText: '确认退回',
      cancelButtonText: '取消'
    });
  } catch (error) {
    return;
  }
  await closeCardReissue(row.id);
  ElMessage.success('已退回待下单');
  fetchData();
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
    h('span', { class: 'confirm-tag' }, tr('MoMo放款指令', 'MoMo disbursement instruction')),
      h('span', { class: 'confirm-order' }, `订单 ${row.id || '--'}`)
    ]),
    h('div', { class: 'confirm-head' }, [
      h('strong', { class: 'confirm-name' }, row.user_name || '未实名'),
      h('span', { class: 'confirm-phone' }, row.user_phone || '--')
    ]),
    h('p', { class: 'confirm-desc' }, tr('确认后将通过MoMo provider支付实际到账金额，并立即生成正式还款账单。', 'The MoMo provider will send the actual amount and create the repayment schedule.'))
  ]),
  h('div', { class: 'confirm-grid' }, [
    createMetric(tr('名义本金', 'Nominal principal'), formatCurrency(summary.nominalAmount), 'confirm-metric-primary'),
    createMetric(tr('上扣费用', 'Upfront fee'), formatCurrency(summary.upfrontFeeAmount))
  ]),
  h('div', { class: 'confirm-grid confirm-grid-detail' }, [
    createMetric(tr('MoMo到账', 'MoMo received'), formatCurrency(summary.disbursementAmount)),
    createMetric(
      '期限',
      summary.termDays && summary.installmentPeriods
        ? `${summary.termDays} 天`
        : '待确认'
    ),
    createMetric(tr('本期应还', 'Current installment due'), formatCurrency(summary.installmentAmount))
  ]),
  h('div', { class: 'confirm-note' }, [
    h('span', { class: 'confirm-note-label' }, tr('预计还款日', 'Expected repayment date')),
    h('strong', { class: 'confirm-note-value' }, summary.dueDateText),
    h('p', { class: 'confirm-note-desc' }, tr('按实际放款时间计算起息日与到期日。确认前请再次核对金额和还款参数。', 'Interest and due dates use the actual disbursement time. Recheck amounts and repayment parameters before confirming.'))
  ])
]);

const handleDisburse = async (row = null) => {
  const targetRow = row || currentRow.value;
  const targetId = row?.id || form.id;

  if (!targetRow || !targetId) {
    return;
  }

  const summary = buildSummary(targetRow);
  if (summary.nominalAmount <= 0 || summary.disbursementAmount < 0 || summary.paymentAmount <= 0) {
    ElMessage.warning(tr('订单快照不完整，请先核对贷款金额、上扣费用和还款总额', 'Loan snapshot is incomplete. Check principal, upfront fee and total repayment.'));
    return;
  }
  if (targetRow.user_blacklist_hit) {
    ElMessage.warning(tr('该用户命中黑名单，不能继续放款', 'This borrower is blacklisted and cannot be disbursed.'));
    return;
  }
  try {
    await ElMessageBox({
      title: tr('确认MoMo放款', 'Confirm MoMo disbursement'),
      message: createConfirmMessage(targetRow, summary),
      showCancelButton: true,
      confirmButtonText: tr('确认放款', 'Confirm disbursement'),
      cancelButtonText: tr('取消', 'Cancel'),
      customClass: 'disburse-confirm-dialog'
    });
  } catch (error) {
    return;
  }

  actionLoading.value = getDisburseActionKey(targetId);
  try {
    const payload = summary.termDays ? { term_days: summary.termDays } : {};
    await disburseLoan(targetId, payload);
    ElMessage.success(tr('MoMo放款已确认', 'MoMo disbursement confirmed'));
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
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
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 0;
  padding: 6px 0;
}

.row-action-cell :deep(.el-button) {
  margin-left: 0;
  width: auto;
  justify-content: center;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.customer-name-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  line-height: 20px;
}

.risk-list-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #dc2626;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
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
