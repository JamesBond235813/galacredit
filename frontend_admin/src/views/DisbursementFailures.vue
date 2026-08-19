<template>
  <div class="admin-page failure-page">
    <section class="summary-grid">
      <article class="summary-card summary-card-danger">
        <span>{{ tr('失败订单', 'Failed loans') }}</span>
        <strong>{{ summary.failed_count || 0 }}</strong>
        <p>{{ tr('按订单去重，仅保留最近一次失败记录', 'Deduplicated by loan, showing the latest failure') }}</p>
      </article>
      <article class="summary-card">
        <span>{{ tr('失败放款金额', 'Failed disbursement amount') }}</span>
        <strong>{{ formatCurrency(summary.failed_amount || 0) }}</strong>
        <p>{{ tr('需要运营人员继续处理的 MoMo 金额', 'MoMo amount requiring follow-up') }}</p>
      </article>
      <article class="summary-card">
        <span>{{ tr('可重试订单', 'Retryable loans') }}</span>
        <strong>{{ retryableCount }}</strong>
        <p>{{ tr('订单仍待放款且客户未命中黑名单', 'Still pending and not blacklisted') }}</p>
      </article>
    </section>

    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="tr('客户筛选', 'Borrower')">
          <el-input
            v-model="filters.keyword"
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
      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="loan_id" :label="tr('订单', 'Loan')" width="90" />
        <el-table-column :label="tr('客户', 'Borrower')" min-width="220">
          <template #default="{ row }">
            <div class="name-line">
              <strong>{{ row.user_name || tr('未实名', 'Unverified') }}</strong>
              <el-tag v-if="row.user_blacklist_hit" type="danger" size="small">{{ tr('黑名单', 'Blacklisted') }}</el-tag>
            </div>
            <div class="sub-text">{{ row.user_phone }} · {{ row.id_card_num || '--' }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('贷款产品', 'Loan product')" min-width="220">
          <template #default="{ row }">
            <div>{{ row.product_name || '--' }}</div>
            <div class="sub-text">{{ tr('订单状态', 'Loan status') }}: {{ row.loan_status }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('放款金额', 'Disbursement')" min-width="150">
          <template #default="{ row }">
            <strong>{{ formatCurrency(row.amount) }}</strong>
            <div class="sub-text">{{ tr('实际到账', 'Actual received') }} {{ formatCurrency(row.actual_disbursement_amount) }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('失败原因', 'Failure reason')" min-width="260">
          <template #default="{ row }">
            <div class="failure-reason">{{ row.failure_message || '--' }}</div>
            <div class="sub-text">{{ row.provider || 'mock' }} · {{ row.provider_reference || tr('无流水号', 'No reference') }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('最近失败时间', 'Last failure')" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.completed_at || row.requested_at) }}</template>
        </el-table-column>
        <el-table-column :label="tr('操作', 'Actions')" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :disabled="!row.retryable"
              :loading="retryingId === row.loan_id"
              @click="retryDisbursement(row)"
            >
              {{ tr('重新放款', 'Retry disbursement') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !items.length" :description="tr('暂无放款失败客户', 'No failed disbursements')" />
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
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { disburseLoan, getDisbursementFailures } from '../api';
import { formatCurrency, formatDateTime } from '../utils/format';
import { tr } from '../i18n/adminLocale';

const loading = ref(false);
const retryingId = ref(null);
const items = ref([]);
const total = ref(0);
const summary = ref({});
const filters = reactive({ keyword: '', page: 1, size: 10 });

const retryableCount = computed(() => items.value.filter((item) => item.retryable).length);

const fetchData = async () => {
  loading.value = true;
  try {
    const result = await getDisbursementFailures({
      keyword: filters.keyword || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    });
    items.value = result.items || [];
    total.value = Number(result.total || 0);
    summary.value = result.summary || {};
  } finally {
    loading.value = false;
  }
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

const retryDisbursement = async (row) => {
  try {
    await ElMessageBox.confirm(
      tr('确认重新向 ' + (row.user_name || row.user_phone) + ' 放款 ' + formatCurrency(row.amount) + '？', 'Retry ' + formatCurrency(row.amount) + ' to ' + (row.user_name || row.user_phone) + '?'),
      tr('重新放款确认', 'Confirm retry'),
      { type: 'warning', confirmButtonText: tr('确认重试', 'Retry'), cancelButtonText: tr('取消', 'Cancel') }
    );
  } catch (error) {
    return;
  }

  retryingId.value = row.loan_id;
  try {
    await disburseLoan(row.loan_id, {});
    ElMessage.success(tr('已重新发起放款', 'Disbursement retry submitted'));
    await fetchData();
  } finally {
    retryingId.value = null;
  }
};

onMounted(fetchData);
</script>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.summary-card {
  padding: 18px 20px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(16, 46, 91, 0.06);
}

.summary-card-danger {
  border-color: rgba(213, 75, 75, 0.22);
  background: #fffafa;
}

.summary-card span,
.summary-card p {
  color: #7a8aa1;
  font-size: 12px;
}

.summary-card strong {
  display: block;
  margin: 10px 0 6px;
  color: #16233a;
  font-size: 26px;
}

.summary-card p {
  margin: 0;
}

.name-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub-text {
  margin-top: 4px;
  color: #7f8da2;
  font-size: 12px;
}

.failure-reason {
  color: #b33b3b;
  line-height: 1.45;
  white-space: normal;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
