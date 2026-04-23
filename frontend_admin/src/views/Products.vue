<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input v-model="filters.keyword" placeholder="商品名称" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.isActive" style="width: 140px">
            <el-option label="全部" value="ALL" />
            <el-option label="上架" :value="true" />
            <el-option label="下架" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="success" @click="openDialog()">新增商品</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="商品名称" min-width="240" />
        <el-table-column label="E卡面值" min-width="120">
          <template #default="{ row }">{{ formatCurrency(row.ecard_face_value) }}</template>
        </el-table-column>
        <el-table-column label="旅游权益" min-width="120">
          <template #default="{ row }">{{ formatCurrency(row.rights_price) }}</template>
        </el-table-column>
        <el-table-column prop="term_days" label="账期(天)" width="110" />
        <el-table-column label="支付金额" min-width="120">
          <template #default="{ row }">{{ formatCurrency(row.payment_amount) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '上架' : '下架' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" width="720px" :title="editingId ? '编辑商品' : '新增商品'" destroy-on-close>
      <el-form label-width="120px">
        <el-form-item label="商品名称">
          <el-input v-model="form.name" placeholder="例如：京东E卡1000元 + 韶关丹霞山2日旅游" />
        </el-form-item>
        <el-form-item label="E卡面值">
          <el-input-number v-model="form.ecard_face_value" :min="0" :step="100" />
        </el-form-item>
        <el-form-item label="旅游权益金额">
          <el-input-number v-model="form.rights_price" :min="0" :step="100" />
        </el-form-item>
        <el-form-item label="旅游权益标题">
          <el-input v-model="form.rights_title" placeholder="例如：韶关丹霞山2日旅游" />
        </el-form-item>
        <el-form-item label="旅游权益说明">
          <el-input v-model="form.rights_desc" type="textarea" :rows="3" placeholder="填写酒店、门票、晚餐等权益内容" />
        </el-form-item>
        <el-form-item label="账期天数">
          <el-input-number v-model="form.term_days" :min="7" :max="364" :step="7" />
        </el-form-item>
        <el-form-item label="支付金额">
          <el-input-number v-model="form.payment_amount" :min="0" :step="100" />
          <span class="inline-tip">默认建议：E卡面值 + 旅游权益金额</span>
        </el-form-item>
        <el-form-item label="是否上架">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { createProduct, getProducts, updateProduct } from '../api';
import { formatCurrency, formatDateTime } from '../utils/format';

const loading = ref(false);
const saving = ref(false);
const total = ref(0);
const tableData = ref([]);
const dialogVisible = ref(false);
const editingId = ref(null);

const filters = reactive({
  keyword: '',
  isActive: 'ALL',
  page: 1,
  size: 10
});

const form = reactive({
  name: '',
  ecard_face_value: 1000,
  rights_price: 600,
  rights_title: '韶关丹霞山旅游权益',
  rights_desc: '',
  term_days: 7,
  payment_amount: 1600,
  is_active: true
});

const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      keyword: filters.keyword || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    };
    if (filters.isActive !== 'ALL') {
      params.is_active = filters.isActive;
    }
    const res = await getProducts(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.keyword = '';
  filters.isActive = 'ALL';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const resetForm = () => {
  form.name = '';
  form.ecard_face_value = 1000;
  form.rights_price = 600;
  form.rights_title = '韶关丹霞山旅游权益';
  form.rights_desc = '';
  form.term_days = 7;
  form.payment_amount = 1600;
  form.is_active = true;
};

const openDialog = (row = null) => {
  if (!row) {
    editingId.value = null;
    resetForm();
    dialogVisible.value = true;
    return;
  }

  editingId.value = row.id;
  form.name = row.name;
  form.ecard_face_value = Number(row.ecard_face_value || 0);
  form.rights_price = Number(row.rights_price || 0);
  form.rights_title = row.rights_title || '';
  form.rights_desc = row.rights_desc || '';
  form.term_days = Number(row.term_days || 7);
  form.payment_amount = Number(row.payment_amount || 0);
  form.is_active = Boolean(row.is_active);
  dialogVisible.value = true;
};

const submit = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请填写商品名称');
    return;
  }
  if (!form.rights_title.trim()) {
    ElMessage.warning('请填写旅游权益标题');
    return;
  }
  if (Number(form.ecard_face_value) <= 0 || Number(form.rights_price) < 0 || Number(form.payment_amount) <= 0) {
    ElMessage.warning('请检查金额配置');
    return;
  }
  if (Number(form.term_days) < 7 || Number(form.term_days) % 7 !== 0) {
    ElMessage.warning('账期天数需为7天的倍数');
    return;
  }

  saving.value = true;
  try {
    const payload = {
      name: form.name.trim(),
      ecard_face_value: Number(form.ecard_face_value),
      rights_price: Number(form.rights_price),
      rights_title: form.rights_title.trim(),
      rights_desc: form.rights_desc.trim() || undefined,
      term_days: Number(form.term_days),
      payment_amount: Number(form.payment_amount),
      is_active: form.is_active
    };
    if (editingId.value) {
      await updateProduct(editingId.value, payload);
      ElMessage.success('商品已更新');
    } else {
      await createProduct(payload);
      ElMessage.success('商品已创建');
    }
    dialogVisible.value = false;
    fetchData();
  } finally {
    saving.value = false;
  }
};

fetchData();
</script>

<style scoped>
.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.inline-tip {
  margin-left: 10px;
  color: #7f8da2;
  font-size: 12px;
}
</style>
