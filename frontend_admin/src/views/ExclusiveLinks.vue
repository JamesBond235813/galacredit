<template>
  <div class="admin-page">
    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column label="渠道 / 业务员" min-width="220">
          <template #default="{ row }">
            <div>{{ row.channel_name || '--' }}</div>
            <div class="sub-text">{{ row.sales_name || '--' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="专属链接" min-width="280">
          <template #default="{ row }">
            <template v-if="row.status === 'ACTIVE'">
              <div class="link-cell">{{ getRowChannelLink(row) }}</div>
              <el-button link type="primary" @click="copyChannelLink(getRowChannelLink(row))">复制链接</el-button>
            </template>
            <template v-else>--</template>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'info'">
              {{ row.status === 'ACTIVE' ? '启用中' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="attributed_user_count" label="归属用户" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { getExclusiveLinks } from '../api';

const loading = ref(false);
const tableData = ref([]);
const linkPrefix = ref('https://xxx.xx');

const buildChannelLink = (inviteCode) => {
  const domain = String(linkPrefix.value || '').trim().replace(/\/+$/, '') || 'https://xxx.xx';
  return `${domain}/${String(inviteCode || '').replace(/^\/+/, '')}`;
};

const getRowChannelLink = (row) => buildChannelLink(row?.invite_code);

const copyChannelLink = async (link) => {
  try {
    await navigator.clipboard.writeText(link);
    ElMessage.success('专属链接已复制');
  } catch (error) {
    ElMessage.error('复制失败，请手动复制');
  }
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getExclusiveLinks();
    tableData.value = Array.isArray(res.items) ? res.items : [];
    linkPrefix.value = String(res.channel_link_prefix || 'https://xxx.xx');
  } finally {
    loading.value = false;
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

.link-cell {
  font-size: 13px;
  color: #20324d;
  word-break: break-all;
}
</style>
