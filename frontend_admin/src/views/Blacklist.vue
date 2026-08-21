<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="tr('搜索', 'Search')">
          <el-input v-model="filters.keyword" :placeholder="tr('姓名 / 手机号 / 身份证号', 'Name / phone / National ID')" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">{{ tr('查询', 'Search') }}</el-button>
          <el-upload :show-file-list="false" :http-request="handleUpload" accept=".xlsx,.xls,.txt,.csv">
            <el-button>{{ tr('上传名单', 'Upload blacklist') }}</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="name" :label="tr('姓名', 'Name')" min-width="140">
          <template #default="{ row }">{{ row.name || '--' }}</template>
        </el-table-column>
        <el-table-column prop="phone" :label="tr('手机号', 'Phone')" min-width="180">
          <template #default="{ row }">{{ row.phone || '--' }}</template>
        </el-table-column>
        <el-table-column prop="id_card_num" :label="tr('身份证号', 'National ID')" min-width="220">
          <template #default="{ row }">{{ row.id_card_num || '--' }}</template>
        </el-table-column>
        <el-table-column :label="tr('创建时间', 'Created at')" min-width="170">
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
import { tr } from '../i18n/adminLocale';

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
  ElMessage.success(tr(`导入完成：新增 ${result.created || 0} 条，跳过 ${result.skipped || 0} 条`, `Import completed: ${result.created || 0} added, ${result.skipped || 0} skipped`));
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
