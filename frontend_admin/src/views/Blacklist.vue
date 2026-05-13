<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input v-model="filters.keyword" placeholder="姓名 / 手机号 / 身份证号" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-upload :show-file-list="false" :http-request="handleUpload" accept=".xlsx,.xls,.txt,.csv">
            <el-button>上传名单</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="name" label="姓名" min-width="140">
          <template #default="{ row }">{{ row.name || '--' }}</template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" min-width="180">
          <template #default="{ row }">{{ row.phone || '--' }}</template>
        </el-table-column>
        <el-table-column prop="id_card_num" label="身份证号" min-width="220">
          <template #default="{ row }">{{ row.id_card_num || '--' }}</template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
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
import { ElMessage } from 'element-plus';
import { getBlacklist, uploadBlacklist } from '../api';
import { formatDateTime } from '../utils/format';

const loading = ref(false);
const tableData = ref([]);
const total = ref(0);
const filters = reactive({ keyword: '', page: 1, size: 20 });

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getBlacklist({
      keyword: filters.keyword || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const handleUpload = async ({ file }) => {
  const formData = new FormData();
  formData.append('file', file);
  const result = await uploadBlacklist(formData);
  ElMessage.success(`导入完成：新增 ${result.created || 0} 条，跳过 ${result.skipped || 0} 条`);
  fetchData();
};

onMounted(fetchData);
</script>

<style scoped>
.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}
</style>
