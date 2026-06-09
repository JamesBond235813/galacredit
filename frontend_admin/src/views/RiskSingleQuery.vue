<template>
  <div class="admin-page risk-single-page">
    <el-card class="panel-card query-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>风控报告单查</h2>
            <p>三要素均可选填；系统会优先匹配已有客户，无法唯一匹配时需补齐三要素。</p>
          </div>
        </div>
      </template>
      <el-form :inline="true" :model="queryForm" class="risk-query-form">
        <el-form-item label="姓名">
          <el-input
            v-model="queryForm.name"
            placeholder="请输入客户姓名"
            clearable
            @keydown.enter.prevent="handleQueryReport"
          />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input
            v-model="queryForm.id_card"
            placeholder="请输入身份证号"
            clearable
            @keydown.enter.prevent="handleQueryReport"
          />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input
            v-model="queryForm.phone"
            placeholder="请输入手机号"
            clearable
            @keydown.enter.prevent="handleQueryReport"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="reportLoading" @click="handleQueryReport">查看报告</el-button>
          <el-button @click="resetQueryForm">清空</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <div class="history-head">
          <div>
            <h2>查询历史清单</h2>
            <p>历史记录按最近查询时间倒序展示，可直接打开报告。</p>
          </div>
          <div class="history-tools">
            <el-input
              v-model="historyKeyword"
              placeholder="姓名 / 手机号 / 身份证号"
              clearable
              @keydown.enter.prevent="fetchHistory"
            />
            <el-button type="primary" @click="fetchHistory">查询</el-button>
          </div>
        </div>
      </template>
      <el-table v-loading="historyLoading" :data="historyRows" stripe>
        <el-table-column prop="name" label="客户姓名" min-width="130" />
        <el-table-column prop="phone" label="手机号" min-width="140" />
        <el-table-column prop="id_card" label="身份证号" min-width="190" />
        <el-table-column label="查询时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.query_time || row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="报告查询" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :loading="openingReportId === row.id" @click="openHistoryReport(row)">
              查看报告
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next, sizes"
          :total="historyTotal"
          :current-page="historyPage"
          :page-size="historySize"
          :page-sizes="[10, 20, 50, 100]"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <RiskReportDialog v-model="riskDialogVisible" :loading="reportLoading" :report="riskReport" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import RiskReportDialog from '../components/RiskReportDialog.vue';
import { getSingleRiskReportDetail, getSingleRiskReportHistory, querySingleRiskReport } from '../api';
import { formatDateTime } from '../utils/format';

const queryForm = reactive({
  name: '',
  id_card: '',
  phone: ''
});
const historyKeyword = ref('');
const historyRows = ref([]);
const historyTotal = ref(0);
const historyPage = ref(1);
const historySize = ref(20);
const historyLoading = ref(false);
const reportLoading = ref(false);
const riskDialogVisible = ref(false);
const riskReport = ref(null);
const openingReportId = ref(null);

const buildQueryPayload = () => ({
  name: queryForm.name.trim() || undefined,
  id_card: queryForm.id_card.trim() || undefined,
  phone: queryForm.phone.trim() || undefined
});

const fetchHistory = async () => {
  historyLoading.value = true;
  try {
    const result = await getSingleRiskReportHistory({
      keyword: historyKeyword.value.trim() || undefined,
      skip: (historyPage.value - 1) * historySize.value,
      limit: historySize.value
    });
    historyRows.value = result.items || [];
    historyTotal.value = Number(result.total || 0);
  } finally {
    historyLoading.value = false;
  }
};

const handleQueryReport = async () => {
  reportLoading.value = true;
  riskReport.value = null;
  riskDialogVisible.value = true;
  try {
    riskReport.value = await querySingleRiskReport(buildQueryPayload());
    ElMessage.success('风控报告查询完成');
    historyPage.value = 1;
    await fetchHistory();
  } catch (error) {
    riskDialogVisible.value = false;
  } finally {
    reportLoading.value = false;
  }
};

const resetQueryForm = () => {
  queryForm.name = '';
  queryForm.id_card = '';
  queryForm.phone = '';
};

const openHistoryReport = async (row) => {
  openingReportId.value = row.id;
  reportLoading.value = true;
  riskReport.value = null;
  riskDialogVisible.value = true;
  try {
    riskReport.value = await getSingleRiskReportDetail(row.id);
  } catch (error) {
    riskDialogVisible.value = false;
  } finally {
    reportLoading.value = false;
    openingReportId.value = null;
  }
};

const handlePageChange = (page) => {
  historyPage.value = page;
  fetchHistory();
};

const handleSizeChange = (size) => {
  historySize.value = size;
  historyPage.value = 1;
  fetchHistory();
};

onMounted(fetchHistory);
</script>

<style scoped>
.risk-single-page {
  gap: 18px;
}

.query-card :deep(.el-card__header) {
  padding-bottom: 0;
}

.risk-query-form {
  row-gap: 8px;
}

.risk-query-form :deep(.el-input) {
  width: 220px;
}

.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.history-head h2 {
  margin: 0;
  font-size: 18px;
  color: #16233a;
}

.history-head p {
  margin: 6px 0 0;
  font-size: 12px;
  color: #73839a;
}

.history-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}

.history-tools .el-input {
  width: 260px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 960px) {
  .history-head {
    align-items: stretch;
    flex-direction: column;
  }

  .history-tools .el-input {
    width: 100%;
  }
}
</style>
