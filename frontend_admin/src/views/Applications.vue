<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input v-model="filters.phone" placeholder="手机号 / 姓名 / 身份证号" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" style="width: 160px">
            <el-option label="全部" value="ALL" />
            <el-option label="审核中" value="REVIEWING" />
            <el-option label="待下单" value="APPROVED" />
            <el-option label="未通过" value="REJECTED" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isSuperAdmin" label="审核员">
          <el-select v-model="filters.reviewAdminId" style="width: 160px" clearable placeholder="全部">
            <el-option label="全部" value="" />
            <el-option v-for="item in reviewAssigneeOptions" :key="item.id" :label="item.username" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="复购次数">
          <el-select v-model="filters.relendFilter" style="width: 150px">
            <el-option label="全部" value="ALL" />
            <el-option label="首购" value="0" />
            <el-option label="复购1次" value="1" />
            <el-option label="复购2次" value="2" />
            <el-option label="复购3次及以上" value="3_PLUS" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="申请单号" width="100" />
        <el-table-column label="用户信息" min-width="220">
          <template #default="{ row }">
            <div class="applicant-name-row">
              <span>{{ row.user_name || '未实名' }}</span>
              <el-tooltip
                v-if="row.user_location_risk_hit"
                :content="row.user_location_risk_detail || 'GPS或IP命中风险位置'"
                placement="top"
              >
                <span class="suspicious-badge">Y</span>
              </el-tooltip>
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
        <el-table-column label="IP审查" width="100">
          <template #default="{ row }">
            <IpAuditTag @click="openIpAudit(row)" />
          </template>
        </el-table-column>
        <el-table-column label="审核员" width="140">
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
        <el-table-column label="身份证号" min-width="170">
          <template #default="{ row }">
            {{ row.user_id_card_num || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="风控查询" width="140">
          <template #default="{ row }">
            <el-button link type="primary" @click="openRiskReport(row)">查询</el-button>
          </template>
        </el-table-column>
        <el-table-column label="黑名单" width="100">
          <template #default="{ row }">
            <el-tag :type="row.user_blacklist_hit ? 'danger' : 'success'">
              {{ row.user_blacklist_hit ? '命中' : '未命中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险管理" width="110">
          <template #default="{ row }">
            <el-button link type="danger" :disabled="row.user_blacklist_hit" @click="handleBlacklist(row)">一键拉黑</el-button>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.application_submitted_at || row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="信用额度" min-width="200">
          <template #default="{ row }">
            <div>{{ formatCurrency(row.available_credit_limit || row.approved_credit_limit || row.credit_limit) }}</div>
            <div class="sub-text">可用额度；审批额度 {{ formatCurrency(row.approved_credit_limit || row.credit_limit || 0) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审批备注" min-width="220">
          <template #default="{ row }">
            {{ row.review_note || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">
              {{ row.status === 'APPROVED' ? '额度调整' : '审批处理' }}
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

    <el-drawer
      v-model="drawerVisible"
      size="1040px"
      title="申请审批处理"
      destroy-on-close
      class="applications-drawer"
    >
      <div v-if="detail" class="identity-drawer-layout">
        <div class="application-side-panel">
          <IdentityImagePanel :row="detail" />
          <section class="remark-card">
            <div class="remark-card-head">
              <h3>备注记录</h3>
              <span>{{ remarkEvents.length }} 条</span>
            </div>
            <div v-if="remarkEvents.length" class="remark-list">
              <article v-for="event in remarkEvents" :key="event.id" class="remark-item">
                <strong>{{ event.title }}</strong>
                <p>{{ event.detail || '无补充说明' }}</p>
                <div>{{ event.operator_name || event.actor_type }} · {{ formatDateTime(event.created_at) }}</div>
              </article>
            </div>
            <el-empty v-else description="暂无备注记录" :image-size="72" />
          </section>
        </div>
        <div class="detail-stack application-detail-stack">
        <section class="detail-card detail-card-summary">
          <h3>客户资料</h3>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="姓名">{{ detail.name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ detail.phone }}</el-descriptions-item>
            <el-descriptions-item label="身份证号">{{ detail.id_card_num || '--' }}</el-descriptions-item>
            <el-descriptions-item label="人脸状态">{{ detail.face_auth_status || '--' }}</el-descriptions-item>
            <el-descriptions-item label="住址" :span="2">{{ detail.id_address || '--' }}</el-descriptions-item>
            <el-descriptions-item label="有效期">{{ detail.id_expiry || '--' }}</el-descriptions-item>
            <el-descriptions-item label="资料提交">{{ formatDateTime(detail.application_submitted_at) }}</el-descriptions-item>
            <el-descriptions-item label="联系人一" :span="2">
              {{ detail.emergency_contact1_name || '--' }} / {{ detail.emergency_contact1_relation || '--' }} / {{ detail.emergency_contact1_phone || '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="联系人二" :span="2">
              {{ detail.emergency_contact2_name || '--' }} / {{ detail.emergency_contact2_relation || '--' }} / {{ detail.emergency_contact2_phone || '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="定位时间">{{ formatDateTime(detail.location_updated_at) }}</el-descriptions-item>
            <el-descriptions-item label="定位来源">{{ detail.location_source || '--' }}</el-descriptions-item>
            <el-descriptions-item label="GPS坐标" :span="2">
              {{ detail.location_latitude && detail.location_longitude ? `${detail.location_latitude}, ${detail.location_longitude}` : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="最小行政区划" :span="2">{{ detail.location_street || '--' }}</el-descriptions-item>
            <el-descriptions-item label="定位地址" :span="2">{{ detail.location_address || '--' }}</el-descriptions-item>
          </el-descriptions>
        </section>

        <section v-if="isApprovedStage" class="detail-card detail-card-credit-adjust">
          <h3>可用额度调整</h3>
          <div class="credit-adjust-summary">
            <article>
              <span>已审批额度</span>
              <strong>{{ formatCurrency(currentRow?.approved_credit_limit || currentRow?.credit_limit || 0) }}</strong>
            </article>
            <article>
              <span>当前可用额度</span>
              <strong>{{ formatCurrency(currentRow?.available_credit_limit || 0) }}</strong>
            </article>
            <article>
              <span>增加后可用额度</span>
              <strong>{{ formatCurrency(nextAvailableCredit) }}</strong>
            </article>
          </div>
          <el-form label-width="96px" size="small" class="approval-form">
            <el-form-item label="增加额度">
              <el-input-number v-model="creditAdjustForm.amount" :min="0" :step="100" size="small" />
            </el-form-item>
            <el-form-item label="调整备注">
              <el-input
                v-model="creditAdjustForm.note"
                type="textarea"
                :rows="2"
                placeholder="填写增加额度原因，例如：额度不足以展示商品"
              />
            </el-form-item>
          </el-form>
          <el-divider />
          <div class="credit-set-head">
            <h4>调减审批额度</h4>
            <span>仅适用于已审批但尚未下单的用户</span>
          </div>
          <el-form label-width="96px" size="small" class="approval-form">
            <el-form-item label="调整后额度">
              <el-input-number
                v-model="creditSetForm.credit_limit"
                :min="0"
                :max="currentApprovedCredit"
                :step="100"
                size="small"
              />
            </el-form-item>
            <el-form-item label="调减备注">
              <el-input
                v-model="creditSetForm.note"
                type="textarea"
                :rows="2"
                placeholder="填写调减原因，例如：资料复核后降低额度"
              />
            </el-form-item>
          </el-form>
          <div class="drawer-footer">
            <el-button @click="drawerVisible = false">关闭</el-button>
            <el-button type="primary" :loading="creditAdjustSaving" @click="submitCreditAdjust">确认增加额度</el-button>
            <el-button type="warning" :loading="creditSetSaving" @click="submitCreditSet">确认调减额度</el-button>
          </div>
        </section>

        <section v-else class="detail-card detail-card-approval">
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
              手动改派
            </el-button>
          </div>
          <h3>授信审批</h3>
          <el-form label-width="84px" size="small" class="approval-form">
            <el-form-item label="审批结果">
              <el-radio-group v-model="reviewForm.approved">
                <el-radio :value="true" :disabled="currentRow?.user_blacklist_hit">通过</el-radio>
                <el-radio :value="false">拒绝</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="授信额度">
              <div class="amount-edit-row">
                <el-input-number
                  v-model="reviewForm.credit_limit"
                  :min="0"
                  :step="500"
                  size="small"
                  :disabled="!reviewForm.approved"
                />
                <div class="quick-day-row amount-shortcuts">
                  <button
                    v-for="item in amountShortcutOptions"
                    :key="item"
                    type="button"
                    class="quick-day-tag"
                    :class="{ 'quick-day-tag-active': Number(reviewForm.credit_limit) === item }"
                    :disabled="!reviewForm.approved"
                    @click="applyAmountShortcut(item)"
                  >
                    {{ item }}
                  </button>
                </div>
              </div>
            </el-form-item>
            <el-form-item label="减免额度">
              <el-input-number
                v-model="reviewForm.approval_discount_amount"
                :min="0"
                :step="100"
                size="small"
                :disabled="!reviewForm.approved"
              />
            </el-form-item>
            <el-form-item label="期限">
              <el-input-number
                v-model="reviewForm.term_days"
                :min="1"
                :max="364"
                :step="1"
                size="small"
                :disabled="!reviewForm.approved"
              />
            </el-form-item>
            <el-form-item label="审批备注">
              <el-input
                v-model="reviewForm.review_note"
                type="textarea"
                :rows="2"
                placeholder="填写审批理由、授信说明或拒绝原因"
              />
            </el-form-item>
          </el-form>

          <div class="drawer-footer">
            <el-button @click="drawerVisible = false">关闭</el-button>
            <el-button :loading="savingReviewNote" @click="saveReviewNote">保存备注</el-button>
            <el-tooltip
              :disabled="canSubmitReview || !reviewForm.approved"
              content="请注意先检查风控报告"
              placement="top"
            >
              <span class="review-submit-tooltip-wrap">
                <el-button type="primary" :loading="submitting" :disabled="!canSubmitReview" @click="submitReview">保存审批结果</el-button>
              </span>
            </el-tooltip>
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

        <section class="detail-card detail-card-timeline">
          <h3>用户操作时间线</h3>
          <div class="timeline-list">
            <div v-for="event in detail.events" :key="event.id" class="timeline-item">
              <strong>{{ event.title }}</strong>
              <p>{{ event.detail || '无补充说明' }}</p>
              <div class="timeline-meta">{{ event.operator_name || event.actor_type }} · {{ formatDateTime(event.created_at) }}</div>
            </div>
          </div>
        </section>
        </div>
      </div>
    </el-drawer>

    <RiskReportDialog
      v-model="riskDialogVisible"
      :loading="riskLoading"
      :report="riskReport"
      @closed="handleRiskReportClosed"
    />
    <CompositeRiskReportDialog
      v-model="compositeRiskDialogVisible"
      :loading="compositeRiskLoading"
      :report="compositeRiskReport"
    />

    <LoanHistoryDialog
      v-model="historyDialogVisible"
      :loan="historyLoan"
      :borrower-name="historyBorrowerName"
    />
    <IpAuditDialog v-model="ipAuditVisible" :loading="ipAuditLoading" :items="ipAuditItems" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import LoanHistoryDialog from '../components/LoanHistoryDialog.vue';
import RiskReportDialog from '../components/RiskReportDialog.vue';
import CompositeRiskReportDialog from '../components/CompositeRiskReportDialog.vue';
import IdentityImagePanel from '../components/IdentityImagePanel.vue';
import IpAuditDialog from '../components/IpAuditDialog.vue';
import IpAuditTag from '../components/IpAuditTag.vue';
import { adjustAvailableCredit, assignLoan, blacklistUser, getCompositeRiskReportByUser, getLoanAssignees, getLoans, getRiskReportByUser, getUserDetail, getUserIpAudit, reviewLoan, setApprovedCreditLimit, updateLoan } from '../api';
import { readStoredAdminProfile } from '../constants/adminPages';
import { buildApplicationsQueryParams } from '../utils/applicationsFilters';
import { formatCurrency, formatDateTime, getStatusTagType, getStatusText } from '../utils/format';

const loading = ref(false);
const submitting = ref(false);
const savingReviewNote = ref(false);
const creditAdjustSaving = ref(false);
const creditSetSaving = ref(false);
const tableData = ref([]);
const total = ref(0);
const drawerVisible = ref(false);
const currentRow = ref(null);
const detail = ref(null);
const riskDialogVisible = ref(false);
const riskLoading = ref(false);
const riskReport = ref(null);
const compositeRiskDialogVisible = ref(false);
const compositeRiskLoading = ref(false);
const compositeRiskReport = ref(null);
const riskReportCheckedUserIds = ref(new Set());
const pendingRiskReportUserId = ref(null);
const historyDialogVisible = ref(false);
const historyLoan = ref(null);
const historyBorrowerName = ref('');
const assignLoading = ref(false);
const assigningReviewer = ref(false);
const reviewAssigneeOptions = ref([]);
const selectedReviewAdminId = ref(null);
const ipAuditVisible = ref(false);
const ipAuditLoading = ref(false);
const ipAuditItems = ref([]);
const adminProfile = ref(readStoredAdminProfile());
const isSuperAdmin = computed(() => (adminProfile.value?.roles || []).includes('ADMIN'));
const currentAdminUsername = computed(() => adminProfile.value?.username || '');

const filters = reactive({
  phone: '',
  status: 'REVIEWING',
  reviewAdminId: '',
  relendFilter: 'ALL',
  page: 1,
  size: 10
});

const reviewForm = reactive({
  approved: true,
  credit_limit: 1000,
  term_days: 7,
  approval_discount_amount: 0,
  review_note: ''
});
const creditAdjustForm = reactive({
  amount: 0,
  note: ''
});
const creditSetForm = reactive({
  credit_limit: 0,
  note: ''
});
const amountShortcutOptions = [1500, 2000, 3000];
const isApprovedStage = computed(() => currentRow.value?.status === 'APPROVED');
const currentApprovedCredit = computed(() => Number(currentRow.value?.approved_credit_limit || currentRow.value?.credit_limit || 0));
const nextAvailableCredit = computed(() => Number(currentRow.value?.available_credit_limit || 0) + Number(creditAdjustForm.amount || 0));
const hasCurrentRiskReportViewed = computed(() => riskReportCheckedUserIds.value.has(currentRow.value?.user_id));
const canSubmitReview = computed(() => {
  if (!reviewForm.approved) {
    return true;
  }
  return Boolean(reviewForm.credit_limit) && !currentRow.value?.user_blacklist_hit && hasCurrentRiskReportViewed.value;
});
const locationEvents = computed(() => (detail.value?.events || []).filter((item) => item.lon_lat));
const remarkEventTypes = new Set([
  'ADMIN_REVIEW_NOTE',
  'ADMIN_APPROVED_CREDIT_SET',
  'ADMIN_AVAILABLE_CREDIT_ADJUSTED',
  'ADMIN_COLLECTION_NOTE',
  'ADMIN_REMIND',
  'ADMIN_COLLECT',
  'ADMIN_FINANCE_RECONCILE',
  'ADMIN_CREDIT_ADJUST',
  'ADMIN_EXTENSION',
  'ADMIN_OVERDUE_DISPLAY'
]);
const remarkEvents = computed(() => (detail.value?.events || []).filter((event) => (
  remarkEventTypes.has(event.event_type)
  || /备注/.test(`${event.title || ''}${event.detail || ''}`)
)));

const isFreshRiskReportCheckedByCurrentAdmin = (row) => {
  if (!row?.risk_report_checked_at) {
    return false;
  }
  const checkedAt = new Date(row.risk_report_checked_at).getTime();
  if (!Number.isFinite(checkedAt)) {
    return false;
  }
  const fourteenDaysMs = 14 * 24 * 60 * 60 * 1000;
  if (Date.now() - checkedAt > fourteenDaysMs) {
    return false;
  }
  return !row.risk_report_checked_by || row.risk_report_checked_by === currentAdminUsername.value;
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
    const res = await getLoans(buildApplicationsQueryParams(filters, isSuperAdmin.value));
    tableData.value = res.items || [];
    const checkedIds = tableData.value
      .filter(isFreshRiskReportCheckedByCurrentAdmin)
      .map((item) => item.user_id);
    if (checkedIds.length) {
      riskReportCheckedUserIds.value = new Set([...riskReportCheckedUserIds.value, ...checkedIds]);
    }
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.phone = '';
  filters.status = 'REVIEWING';
  filters.reviewAdminId = '';
  filters.relendFilter = 'ALL';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const openDrawer = async (row) => {
  currentRow.value = row;
  detail.value = null;
  drawerVisible.value = true;
  detail.value = await getUserDetail(row.user_id);
  selectedReviewAdminId.value = row.review_admin_id || null;

  reviewForm.approved = row.status !== 'REJECTED';
  if (row.user_blacklist_hit) {
    reviewForm.approved = false;
  }
  reviewForm.credit_limit = Number(row.approved_credit_limit || row.credit_limit || 1000);
  reviewForm.term_days = Number(row.term_days || 7);
  reviewForm.approval_discount_amount = Number(row.approval_discount_amount || 0);
  reviewForm.review_note = row.review_note || '';
  creditAdjustForm.amount = 0;
  creditAdjustForm.note = '';
  creditSetForm.credit_limit = Number(row.approved_credit_limit || row.credit_limit || 0);
  creditSetForm.note = '';
  if (isFreshRiskReportCheckedByCurrentAdmin(row)) {
    riskReportCheckedUserIds.value = new Set([...riskReportCheckedUserIds.value, row.user_id]);
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

const openRiskReport = async (row) => {
  riskDialogVisible.value = true;
  riskLoading.value = true;
  riskReport.value = null;
  pendingRiskReportUserId.value = row.user_id;

  try {
    riskReport.value = await getCompositeRiskReportByUser({ user_id: row.user_id });
  } catch (error) {
    riskDialogVisible.value = false;
    pendingRiskReportUserId.value = null;
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

const handleRiskReportClosed = () => {
  if (riskReport.value && pendingRiskReportUserId.value) {
    riskReportCheckedUserIds.value = new Set([...riskReportCheckedUserIds.value, pendingRiskReportUserId.value]);
  }
  pendingRiskReportUserId.value = null;
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

const openHistoryDialog = (row) => {
  historyLoan.value = row.latest_settled_loan || null;
  historyBorrowerName.value = row.user_name || row.user_phone || '';
  historyDialogVisible.value = true;
};

const applyAmountShortcut = (value) => {
  if (!reviewForm.approved) {
    return;
  }
  reviewForm.credit_limit = value;
};

const submitReview = async () => {
  if (reviewForm.approved && !reviewForm.credit_limit) {
    ElMessage.warning('请填写授信额度');
    return;
  }
  if (reviewForm.approved && currentRow.value?.user_blacklist_hit) {
    ElMessage.warning('该用户命中黑名单，只能拒绝');
    return;
  }
  if (reviewForm.approved && !riskReportCheckedUserIds.value.has(currentRow.value?.user_id)) {
    ElMessage.warning('审批通过前请先查询并查看风控报告');
    return;
  }

  submitting.value = true;
  try {
    await reviewLoan(currentRow.value.id, {
      approved: reviewForm.approved,
      credit_limit: reviewForm.approved ? Number(reviewForm.credit_limit) : undefined,
      term_days: reviewForm.approved ? Number(reviewForm.term_days || 7) : undefined,
      approval_discount_amount: reviewForm.approved ? Number(reviewForm.approval_discount_amount || 0) : 0,
      review_note: reviewForm.review_note
    });
    ElMessage.success('审批结果已保存');
    drawerVisible.value = false;
    fetchData();
  } finally {
    submitting.value = false;
  }
};

const saveReviewNote = async () => {
  const note = (reviewForm.review_note || '').trim();
  if (!currentRow.value?.id) {
    return;
  }
  if (!note) {
    ElMessage.warning('请先填写备注内容');
    return;
  }
  savingReviewNote.value = true;
  try {
    const updatedLoan = await updateLoan(currentRow.value.id, { review_note: note });
    reviewForm.review_note = note;
    currentRow.value.review_note = updatedLoan.review_note || note;
    const rowIndex = tableData.value.findIndex((item) => item.id === currentRow.value.id);
    if (rowIndex >= 0) {
      tableData.value[rowIndex] = {
        ...tableData.value[rowIndex],
        review_note: currentRow.value.review_note
      };
    }
    detail.value = await getUserDetail(currentRow.value.user_id);
    ElMessage.success('备注已保存');
  } finally {
    savingReviewNote.value = false;
  }
};

const submitCreditAdjust = async () => {
  if (!currentRow.value?.id || Number(creditAdjustForm.amount || 0) <= 0) {
    ElMessage.warning('请填写需要增加的可用额度');
    return;
  }
  creditAdjustSaving.value = true;
  try {
    const result = await adjustAvailableCredit(currentRow.value.id, {
      amount: Number(creditAdjustForm.amount || 0),
      note: creditAdjustForm.note || '审核员后台增加可用额度'
    });
    const updatedLoan = result?.loan || {};
    currentRow.value = {
      ...currentRow.value,
      ...updatedLoan,
      user_id: currentRow.value.user_id,
      user_name: currentRow.value.user_name,
      user_phone: currentRow.value.user_phone,
      user_id_card_num: currentRow.value.user_id_card_num
    };
    creditAdjustForm.amount = 0;
    creditAdjustForm.note = '';
    ElMessage.success('可用额度已增加');
    await fetchData();
  } finally {
    creditAdjustSaving.value = false;
  }
};

const submitCreditSet = async () => {
  if (!currentRow.value?.id) {
    return;
  }
  const nextLimit = Number(creditSetForm.credit_limit || 0);
  if (nextLimit > currentApprovedCredit.value) {
    ElMessage.warning('调减额度不能高于当前审批额度');
    return;
  }
  if (nextLimit === currentApprovedCredit.value) {
    ElMessage.warning('调整后额度未变化');
    return;
  }
  creditSetSaving.value = true;
  try {
    const result = await setApprovedCreditLimit(currentRow.value.id, {
      credit_limit: nextLimit,
      note: creditSetForm.note || '审核员后台调减审批额度'
    });
    const updatedLoan = result?.loan || {};
    currentRow.value = {
      ...currentRow.value,
      ...updatedLoan,
      user_id: currentRow.value.user_id,
      user_name: currentRow.value.user_name,
      user_phone: currentRow.value.user_phone,
      user_id_card_num: currentRow.value.user_id_card_num
    };
    creditSetForm.credit_limit = Number(updatedLoan.approved_credit_limit || updatedLoan.credit_limit || nextLimit);
    creditSetForm.note = '';
    ElMessage.success('审批额度已调减');
    await fetchData();
  } finally {
    creditSetSaving.value = false;
  }
};

onMounted(() => {
  fetchData();
  loadReviewAssignees();
});
</script>

<style scoped>
.sub-text {
  margin-top: 4px;
  color: #7f8da2;
  font-size: 12px;
}

.applicant-name-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  line-height: 20px;
}

.suspicious-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #111827;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
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

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.review-submit-tooltip-wrap {
  display: inline-flex;
}

.amount-edit-row,
.term-edit-row,
.fee-edit-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-day-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-day-tag {
  height: 32px;
  padding: 0 14px;
  border: 1px solid rgba(44, 114, 229, 0.14);
  border-radius: 999px;
  background: #f7faff;
  color: #5f7188;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-day-tag:hover:not(:disabled) {
  border-color: rgba(44, 114, 229, 0.28);
  color: #2c72e5;
}

.quick-day-tag:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quick-day-tag-active {
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

.review-preview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 6px 0 18px;
}

.review-preview-card {
  padding: 14px 16px;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(246, 250, 255, 1) 0%, rgba(255, 255, 255, 1) 100%);
  border: 1px solid rgba(44, 114, 229, 0.08);
}

.review-preview-card span {
  display: block;
  font-size: 12px;
  color: #7a8aa1;
}

.review-preview-card strong {
  display: block;
  margin-top: 10px;
  font-size: 20px;
  color: #1f66e5;
}

.application-detail-stack {
  gap: 12px;
  max-height: none;
  overflow: visible;
  padding-bottom: 16px;
}

.application-side-panel {
  width: 320px;
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.application-side-panel :deep(.identity-image-panel) {
  width: 100%;
  flex: none;
}

.remark-card {
  min-height: 220px;
  padding: 12px;
  border: 1px solid #e7edf6;
  border-radius: 8px;
  background: #fff;
}

.remark-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.remark-card-head h3 {
  margin: 0;
  font-size: 14px;
  color: #21324a;
}

.remark-card-head span {
  color: #7a8aa1;
  font-size: 12px;
}

.remark-list {
  display: flex;
  max-height: 360px;
  overflow: auto;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px;
}

.remark-item {
  padding: 10px;
  border: 1px solid #edf2fa;
  border-radius: 8px;
  background: #f8fbff;
}

.remark-item strong {
  display: block;
  color: #1d2f49;
  font-size: 13px;
}

.remark-item p {
  margin: 6px 0;
  color: #40546f;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.remark-item div {
  color: #8a98ad;
  font-size: 12px;
}

.detail-card-summary,
.detail-card-approval,
.detail-card-credit-adjust,
.detail-card-timeline {
  padding: 14px;
}

.detail-card-summary :deep(.el-descriptions__label),
.detail-card-summary :deep(.el-descriptions__content) {
  padding: 8px 10px;
  font-size: 12px;
}

.detail-card-summary :deep(.el-descriptions__label) {
  width: 88px;
  color: #6f7f95;
}

.approval-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.assignee-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.approval-form :deep(.el-input-number) {
  width: 132px;
}

.credit-adjust-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.credit-adjust-summary article {
  padding: 12px;
  border: 1px solid #e7edf6;
  border-radius: 8px;
  background: #f8fbff;
}

.credit-adjust-summary span {
  display: block;
  color: #7a8aa1;
  font-size: 12px;
}

.credit-adjust-summary strong {
  display: block;
  margin-top: 8px;
  color: #1f66e5;
  font-size: 18px;
}

.credit-set-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 12px;
}

.credit-set-head h4 {
  margin: 0;
  color: #26364d;
  font-size: 14px;
}

.credit-set-head span {
  color: #8a98ad;
  font-size: 12px;
}

.review-preview-grid {
  margin: 4px 0 14px;
}

.review-preview-card {
  padding: 12px 14px;
}

.review-preview-card strong {
  margin-top: 8px;
  font-size: 18px;
}

.detail-card-timeline {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.detail-card-timeline .timeline-list {
  flex: 1;
  min-height: 0;
  max-height: 180px;
  overflow: auto;
  padding-right: 4px;
}

.detail-card-timeline .timeline-item {
  padding: 10px 12px;
}

.detail-card-timeline .timeline-item p {
  line-height: 1.55;
}

:deep(.applications-drawer .el-drawer__header) {
  margin-bottom: 0;
  padding: 18px 20px 14px;
}

:deep(.applications-drawer .el-drawer__body) {
  padding: 12px 16px 16px;
  height: calc(100vh - 56px);
  overflow-x: hidden;
  overflow-y: auto;
}
</style>
