<template>
  <div class="page-wrap">
    <div class="toolbar">
      <div>
        <h3>逾期费用标准</h3>
        <p>新标准仅对生效日（含）之后进入逾期的账单生效，历史账单不重算。</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">新增配置</el-button>
    </div>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="effective_date" label="生效日" width="140" />
        <el-table-column label="逾期费用" width="160">
          <template #default="{ row }">{{ formatCurrency(row.daily_penalty_amount) }} / 天</template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="220">
          <template #default="{ row }">{{ row.note || '--' }}</template>
        </el-table-column>
        <el-table-column prop="created_by" label="创建人" width="120">
          <template #default="{ row }">{{ row.created_by || '--' }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          layout="total, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" width="460px" title="新增逾期配置" destroy-on-close>
      <el-form label-width="110px">
        <el-form-item label="逾期费用" required>
          <el-input-number v-model="form.daily_penalty_amount" :min="0" :step="1" :precision="2" />
          <span class="unit-text">元/天</span>
        </el-form-item>
        <el-form-item label="生效日" required>
          <el-date-picker v-model="form.effective_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="3" maxlength="255" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { createOverdueFeeConfig, getOverdueFeeConfigs } from '../api';
import { formatCurrency, formatDateTime } from '../utils/format';

const loading = ref(false);
const saving = ref(false);
const dialogVisible = ref(false);
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;
const form = reactive({
  daily_penalty_amount: 10,
  effective_date: '',
  note: ''
});

const fetchData = async () => {
  loading.value = true;
  try {
    const resp = await getOverdueFeeConfigs({ skip: (page.value - 1) * pageSize, limit: pageSize });
    items.value = resp.items || [];
    total.value = Number(resp.total || 0);
  } finally {
    loading.value = false;
  }
};

const openCreateDialog = () => {
  form.daily_penalty_amount = 10;
  form.effective_date = new Date().toISOString().slice(0, 10);
  form.note = '';
  dialogVisible.value = true;
};

const submitCreate = async () => {
  if (!form.effective_date) {
    ElMessage.warning('请选择生效日');
    return;
  }
  saving.value = true;
  try {
    await createOverdueFeeConfig({ ...form });
    ElMessage.success('逾期配置已保存');
    dialogVisible.value = false;
    fetchData();
  } finally {
    saving.value = false;
  }
};

const handlePageChange = (nextPage) => {
  page.value = nextPage;
  fetchData();
};

onMounted(fetchData);
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.toolbar h3 {
  margin: 0;
  color: #16233a;
}

.toolbar p {
  margin: 6px 0 0;
  color: #6b7a90;
  font-size: 13px;
}

.unit-text {
  margin-left: 8px;
  color: #6b7a90;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
