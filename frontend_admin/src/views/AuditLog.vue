<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="tr('搜索', 'Search')">
          <el-input v-model="filters.keyword" :placeholder="tr('姓名 / 手机号 / 订单号 / 备注', 'Name / phone / loan ID / note')" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item label="操作者类型">
          <el-select v-model="filters.actorType" style="width: 160px">
            <el-option label="全部" value="ALL" />
            <el-option label="管理员" value="ADMIN" />
            <el-option label="系统" value="SYSTEM" />
          </el-select>
        </el-form-item>
        <el-form-item label="事件类型"><el-input v-model="filters.eventType" placeholder="如 KYC_APPROVE" clearable /></el-form-item>
        <el-form-item label="对象类型"><el-select v-model="filters.objectType" style="width: 130px"><el-option label="全部" value="ALL" /><el-option label="用户" value="USER" /><el-option label="订单" value="LOAN" /></el-select></el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">{{ tr('查询', 'Search') }}</el-button>
          <el-button @click="resetFilters">{{ tr('重置', 'Reset') }}</el-button>
          <el-button @click="exportData">{{ tr('导出CSV', 'Export CSV') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="created_at" label="时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="对象" min-width="180">
          <template #default="{ row }">
            <div>{{ row.user_name || '--' }}</div>
            <div class="sub-text">{{ row.user_phone || '--' }} <span v-if="row.loan_order_no">/{{ row.loan_order_no }}</span></div>
          </template>
        </el-table-column>
        <el-table-column prop="actor_type" label="类型" width="100" />
        <el-table-column prop="operator_name" label="操作者" min-width="130" />
        <el-table-column prop="event_type" label="事件" min-width="160" />
        <el-table-column prop="title" label="标题" min-width="170" />
        <el-table-column prop="detail" label="详情" min-width="300" show-overflow-tooltip />
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
import { getAdminAuditLogs, exportAdminAuditLogs } from '../api';
import { formatDateTime } from '../utils/format';
import { tr } from '../i18n/adminLocale';

const loading = ref(false);
const tableData = ref([]);
const total = ref(0);
const filters = reactive({ keyword: '', actorType: 'ALL', eventType: '', objectType: 'ALL', page: 1, size: 20 });

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getAdminAuditLogs({
      keyword: filters.keyword || undefined,
      actor_type: filters.actorType === 'ALL' ? undefined : filters.actorType,
      event_type: filters.eventType || undefined,
      object_type: filters.objectType === 'ALL' ? undefined : filters.objectType,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    });
    tableData.value = res.items || [];
    total.value = Number(res.total || 0);
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.keyword = '';
  filters.actorType = 'ALL';
  filters.eventType = '';
  filters.objectType = 'ALL';
  filters.page = 1;
  fetchData();
};

const exportData = async () => {
  const blob = await exportAdminAuditLogs({ keyword: filters.keyword || undefined, actor_type: filters.actorType === 'ALL' ? undefined : filters.actorType, event_type: filters.eventType || undefined, object_type: filters.objectType === 'ALL' ? undefined : filters.objectType });
  const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'audit-logs.csv'; link.click(); URL.revokeObjectURL(url);
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

onMounted(fetchData);
</script>
