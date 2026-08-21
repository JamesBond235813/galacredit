<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="tr('搜索', 'Search')">
          <el-input v-model="filters.keyword" :placeholder="tr('手机号 / 姓名 / 身份证号', 'Phone / name / National ID')" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">{{ tr('查询', 'Search') }}</el-button>
          <el-button @click="resetFilters">{{ tr('重置', 'Reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="phone" :label="tr('手机号', 'Phone')" min-width="150" />
        <el-table-column prop="name" :label="tr('姓名', 'Name')" min-width="120" />
        <el-table-column prop="id_card_num" :label="tr('身份证号', 'National ID')" min-width="180" />
        <el-table-column :label="tr('状态', 'Status')" min-width="180">
          <template #default="{ row }">
            <div>{{ row.real_name_status || '--' }} / {{ row.face_auth_status || '--' }}</div>
            <div class="sub-text">{{ row.suggested_action }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('风险标签', 'Risk flags')" min-width="240">
          <template #default="{ row }">
            <el-tag v-for="flag in row.review_flags || []" :key="flag" class="flag-tag" type="warning" effect="plain">{{ flag }}</el-tag>
            <span v-if="!row.review_flags?.length">--</span>
          </template>
        </el-table-column>
        <el-table-column :label="tr('渠道', 'Channel')" min-width="180">
          <template #default="{ row }">
            <div>{{ row.source_channel_sales_name || '--' }}</div>
            <div class="sub-text">{{ row.source_channel_name || '--' }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="tr('提交时间', 'Submitted at')" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.application_submitted_at || row.created_at) }}</template>
        </el-table-column>
        <el-table-column :label="tr('操作', 'Actions')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="review(row, 'APPROVE')">{{ tr('通过', 'Approve') }}</el-button>
            <el-button link type="danger" @click="review(row, 'REJECT')">{{ tr('拒绝', 'Reject') }}</el-button>
            <el-button link type="primary" @click="openUserArchive(row)">{{ tr('查看档案', 'View profile') }}</el-button>
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
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { getKycReviewQueue, reviewKycUser } from '../api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { formatDateTime } from '../utils/format';
import { tr } from '../i18n/adminLocale';

const router = useRouter();
const loading = ref(false);
const tableData = ref([]);
const total = ref(0);
const filters = reactive({ keyword: '', page: 1, size: 20 });

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getKycReviewQueue({
      keyword: filters.keyword || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    });
    tableData.value = res.items || [];
    total.value = Number(res.total || 0);
  } finally {
    loading.value = false;
  }
};

const openUserArchive = (row) => {
  router.push({ path: '/users', query: { keyword: row.phone } });
};

const review = async (row, action) => {
  const note = await ElMessageBox.prompt(tr('请输入处理备注（可选）', 'Enter a processing note (optional)'), action === 'APPROVE' ? tr('通过KYC', 'Approve KYC') : tr('拒绝KYC', 'Reject KYC'), { inputPlaceholder: tr('处理备注', 'Processing note') }).catch(() => null);
  if (!note) return;
  await reviewKycUser(row.id, { action, note: note.value });
  ElMessage.success(tr('处理成功', 'Processed successfully'));
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

onMounted(fetchData);
</script>
