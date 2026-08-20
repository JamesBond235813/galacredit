<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input v-model="filters.keyword" placeholder="手机号 / 姓名 / 身份证号" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="phone" label="手机号" min-width="150" />
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column prop="id_card_num" label="身份证号" min-width="180" />
        <el-table-column label="状态" min-width="180">
          <template #default="{ row }">
            <div>{{ row.real_name_status || '--' }} / {{ row.face_auth_status || '--' }}</div>
            <div class="sub-text">{{ row.suggested_action }}</div>
          </template>
        </el-table-column>
        <el-table-column label="风险标签" min-width="240">
          <template #default="{ row }">
            <el-tag v-for="flag in row.review_flags || []" :key="flag" class="flag-tag" type="warning" effect="plain">{{ flag }}</el-tag>
            <span v-if="!row.review_flags?.length">--</span>
          </template>
        </el-table-column>
        <el-table-column label="渠道" min-width="180">
          <template #default="{ row }">
            <div>{{ row.source_channel_sales_name || '--' }}</div>
            <div class="sub-text">{{ row.source_channel_name || '--' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.application_submitted_at || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="review(row, 'APPROVE')">通过</el-button>
            <el-button link type="danger" @click="review(row, 'REJECT')">拒绝</el-button>
            <el-button link type="primary" @click="openUserArchive(row)">查看档案</el-button>
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
  const note = await ElMessageBox.prompt('请输入处理备注（可选）', action === 'APPROVE' ? '通过KYC' : '拒绝KYC', { inputPlaceholder: '处理备注' }).catch(() => null);
  if (!note) return;
  await reviewKycUser(row.id, { action, note: note.value });
  ElMessage.success('处理成功');
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
