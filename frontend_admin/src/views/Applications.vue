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
            <div>{{ row.user_name || '未实名' }}</div>
            <div class="sub-text">{{ row.user_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column label="审核员" width="140">
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
        <el-table-column label="身份证号" min-width="170">
          <template #default="{ row }">
            {{ row.user_id_card_num || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="风控查询" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="openRiskReport(row)">查询</el-button>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.application_submitted_at || row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="信用额度" min-width="200">
          <template #default="{ row }">
            <div>{{ formatCurrency(row.approved_credit_limit || row.credit_limit) }}</div>
            <div class="sub-text">用于商品列表信用下单上限</div>
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
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">审批处理</el-button>
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
      size="640px"
      title="申请审批处理"
      destroy-on-close
      class="applications-drawer"
    >
      <div v-if="detail" class="detail-stack application-detail-stack">
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

        <section class="detail-card detail-card-approval">
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
                <el-radio :value="true">通过</el-radio>
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
            <el-button type="primary" :loading="submitting" @click="submitReview">保存审批结果</el-button>
          </div>
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
    </el-drawer>

    <RiskReportDialog
      v-model="riskDialogVisible"
      :loading="riskLoading"
      :report="riskReport"
    />

    <LoanHistoryDialog
      v-model="historyDialogVisible"
      :loan="historyLoan"
      :borrower-name="historyBorrowerName"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import LoanHistoryDialog from '../components/LoanHistoryDialog.vue';
import RiskReportDialog from '../components/RiskReportDialog.vue';
import { assignLoan, getLoanAssignees, getLoans, getRiskReportByUser, getUserDetail, reviewLoan } from '../api';
import { readStoredAdminProfile } from '../constants/adminPages';
import { formatCurrency, formatDateTime, getStatusTagType, getStatusText } from '../utils/format';

const loading = ref(false);
const submitting = ref(false);
const tableData = ref([]);
const total = ref(0);
const drawerVisible = ref(false);
const currentRow = ref(null);
const detail = ref(null);
const riskDialogVisible = ref(false);
const riskLoading = ref(false);
const riskReport = ref(null);
const historyDialogVisible = ref(false);
const historyLoan = ref(null);
const historyBorrowerName = ref('');
const assignLoading = ref(false);
const assigningReviewer = ref(false);
const reviewAssigneeOptions = ref([]);
const selectedReviewAdminId = ref(null);
const adminProfile = ref(readStoredAdminProfile());
const isSuperAdmin = computed(() => (adminProfile.value?.roles || []).includes('ADMIN'));

const filters = reactive({
  phone: '',
  status: 'REVIEWING',
  page: 1,
  size: 10
});

const reviewForm = reactive({
  approved: true,
  credit_limit: 1000,
  review_note: ''
});
const amountShortcutOptions = [1500, 2000, 3000];

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
    const res = await getLoans({
      scope: 'REVIEWING',
      phone: filters.phone || undefined,
      status: filters.status === 'ALL' ? undefined : filters.status,
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
  filters.status = 'REVIEWING';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const openDrawer = async (row) => {
  currentRow.value = row;
  drawerVisible.value = true;
  detail.value = await getUserDetail(row.user_id);
  selectedReviewAdminId.value = row.review_admin_id || null;

  reviewForm.approved = row.status !== 'REJECTED';
  reviewForm.credit_limit = Number(row.approved_credit_limit || row.credit_limit || 1000);
  reviewForm.review_note = row.review_note || '';
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

  try {
    riskReport.value = await getRiskReportByUser({ user_id: row.user_id });
  } catch (error) {
    riskDialogVisible.value = false;
  } finally {
    riskLoading.value = false;
  }
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

  submitting.value = true;
  try {
    await reviewLoan(currentRow.value.id, {
      approved: reviewForm.approved,
      credit_limit: reviewForm.approved ? Number(reviewForm.credit_limit) : undefined,
      review_note: reviewForm.review_note
    });
    ElMessage.success('审批结果已保存');
    drawerVisible.value = false;
    fetchData();
  } finally {
    submitting.value = false;
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

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
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
  max-height: calc(100vh - 96px);
  overflow: hidden;
}

.detail-card-summary,
.detail-card-approval,
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
  overflow: hidden;
}
</style>
