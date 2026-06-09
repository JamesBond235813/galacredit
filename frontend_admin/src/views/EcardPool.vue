<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="卡号">
          <el-input v-model="filters.keyword" placeholder="输入卡号关键词" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" style="width: 140px">
            <el-option label="全部" value="ALL" />
            <el-option label="可发放" value="AVAILABLE" />
            <el-option label="已发放" value="ASSIGNED" />
            <el-option label="已过期" value="EXPIRED" />
            <el-option label="作废" value="VOID" />
          </el-select>
        </el-form-item>
        <el-form-item label="面额">
          <el-input-number v-model="filters.faceValue" :min="0" :step="100" :controls="false" style="width: 140px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="warning" @click="openUploadDialog">批量上传</el-button>
          <el-button type="info" @click="downloadTemplate">下载模板</el-button>
          <el-button type="success" @click="openCreateDialog">新增卡密</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="account" label="卡号(脱敏)" min-width="180" />
        <el-table-column prop="password" label="卡密(脱敏)" min-width="150" />
        <el-table-column label="面额" min-width="100">
          <template #default="{ row }">{{ formatCurrency(row.face_value) }}</template>
        </el-table-column>
        <el-table-column label="有效期" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.expires_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="loan_id" label="绑定订单" width="110" />
        <el-table-column label="备注" min-width="180">
          <template #default="{ row }">{{ row.note || '--' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
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

    <el-dialog v-model="createVisible" width="600px" title="新增卡池卡密" destroy-on-close>
      <el-form label-width="110px">
        <el-form-item label="卡号">
          <el-input v-model="createForm.account" placeholder="请输入京东E卡卡号" />
        </el-form-item>
        <el-form-item label="卡密">
          <el-input v-model="createForm.password" placeholder="请输入京东E卡卡密" />
        </el-form-item>
        <el-form-item label="面额">
          <el-input-number v-model="createForm.face_value" :min="0" :step="100" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-date-picker v-model="createForm.expires_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="请选择有效期截止时间" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.note" type="textarea" :rows="2" placeholder="可选，填写来源说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="uploadVisible" width="640px" title="批量上传E卡" destroy-on-close>
      <div style="margin-bottom: 12px; color: #606266; line-height: 1.6;">
        请上传包含卡号、密码、面额、有效期四列的 Excel 文件（xls/xlsx）。
        <br />模板可通过“下载模板”按钮获取。
      </div>
      <el-upload
        :before-upload="beforeUpload"
        :on-remove="handleRemove"
        :file-list="uploadFileList"
        accept=".xls,.xlsx"
        list-type="text"
        drag
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
      </el-upload>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploadLoading" @click="submitUpload">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" width="560px" title="编辑卡池记录" destroy-on-close>
      <el-form label-width="110px">
        <el-form-item label="当前状态">
          <el-select v-model="editForm.status" style="width: 180px">
            <el-option label="可发放" value="AVAILABLE" />
            <el-option label="已发放" value="ASSIGNED" />
            <el-option label="已过期" value="EXPIRED" />
            <el-option label="作废" value="VOID" />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期">
          <el-date-picker v-model="editForm.expires_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="请选择有效期截止时间" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { createEcardPoolItem, getEcardPool, updateEcardPoolItem, uploadEcardPoolExcel, downloadEcardPoolTemplate } from '../api';
import { formatCurrency, formatDateTime } from '../utils/format';

const loading = ref(false);
const saving = ref(false);
const total = ref(0);
const tableData = ref([]);

const createVisible = ref(false);
const editVisible = ref(false);
const uploadVisible = ref(false);
const uploadFile = ref(null);
const uploadFileList = ref([]);
const uploadLoading = ref(false);
const editingId = ref(null);

const filters = reactive({
  keyword: '',
  status: 'ALL',
  faceValue: null,
  page: 1,
  size: 10
});

const createForm = reactive({
  account: '',
  password: '',
  face_value: 1000,
  expires_at: '',
  note: ''
});

const editForm = reactive({
  status: 'AVAILABLE',
  expires_at: '',
  note: ''
});

const statusTextMap = {
  AVAILABLE: '可发放',
  ASSIGNED: '已发放',
  EXPIRED: '已过期',
  VOID: '作废'
};

const getStatusText = (status) => statusTextMap[status] || status || '--';
const getStatusType = (status) => {
  if (status === 'AVAILABLE') return 'success';
  if (status === 'ASSIGNED') return 'primary';
  if (status === 'EXPIRED') return 'warning';
  if (status === 'VOID') return 'info';
  return 'info';
};

const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      keyword: filters.keyword || undefined,
      status: filters.status || 'ALL',
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    };
    if (filters.faceValue) {
      params.face_value = Number(filters.faceValue);
    }
    const res = await getEcardPool(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.keyword = '';
  filters.status = 'ALL';
  filters.faceValue = null;
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const openCreateDialog = () => {
  createForm.account = '';
  createForm.password = '';
  createForm.face_value = 1000;
  createForm.expires_at = '';
  createForm.note = '';
  createVisible.value = true;
};

const openUploadDialog = () => {
  uploadFile.value = null;
  uploadFileList.value = [];
  uploadVisible.value = true;
};

const beforeUpload = (file) => {
  const validExt = /\.(xls|xlsx)$/i;
  if (!validExt.test(file.name)) {
    ElMessage.warning('仅支持 xls 或 xlsx 文件');
    return false;
  }
  uploadFile.value = file;
  uploadFileList.value = [file];
  return false;
};

const handleRemove = () => {
  uploadFile.value = null;
  uploadFileList.value = [];
};

const submitUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先选择Excel文件');
    return;
  }

  uploadLoading.value = true;
  try {
    const formData = new FormData();
    formData.append('file', uploadFile.value);
    const res = await uploadEcardPoolExcel(formData);
    const errorCount = res.errors?.length || 0;
    ElMessage.success(`成功导入 ${res.created} 条，失败 ${errorCount} 条`);
    if (errorCount > 0) {
      await ElMessageBox.alert(
        res.errors.map((item) => `第${item.row}行：${item.reason}`).join('\n'),
        '批量上传结果',
        {
          confirmButtonText: '知道了',
          type: 'warning',
          dangerouslyUseHTMLString: false,
        }
      );
    }
    uploadVisible.value = false;
    fetchData();
  } finally {
    uploadLoading.value = false;
  }
};

const downloadTemplate = async () => {
  try {
    const blob = await downloadEcardPoolTemplate();
    const url = window.URL.createObjectURL(new Blob([blob]));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'ecard_pool_template.xlsx';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    // 统一错误提示由拦截器处理
  }
};

const openEditDialog = (row) => {
  editingId.value = row.id;
  editForm.status = row.status || 'AVAILABLE';
  editForm.expires_at = row.expires_at ? row.expires_at.replace('T', ' ').slice(0, 19) : '';
  editForm.note = row.note || '';
  editVisible.value = true;
};

const submitCreate = async () => {
  if (!createForm.account.trim() || !createForm.password.trim()) {
    ElMessage.warning('请填写卡号和卡密');
    return;
  }
  if (!createForm.expires_at) {
    ElMessage.warning('请选择有效期');
    return;
  }
  if (Number(createForm.face_value) <= 0) {
    ElMessage.warning('面额必须大于0');
    return;
  }

  saving.value = true;
  try {
    await createEcardPoolItem({
      account: createForm.account.trim(),
      password: createForm.password.trim(),
      face_value: Number(createForm.face_value),
      expires_at: createForm.expires_at,
      note: createForm.note.trim() || undefined
    });
    ElMessage.success('卡池记录已创建');
    createVisible.value = false;
    fetchData();
  } finally {
    saving.value = false;
  }
};

const submitEdit = async () => {
  if (!editingId.value) {
    return;
  }
  saving.value = true;
  try {
    await updateEcardPoolItem(editingId.value, {
      status: editForm.status,
      expires_at: editForm.expires_at || undefined,
      note: editForm.note.trim() || undefined
    });
    ElMessage.success('卡池记录已更新');
    editVisible.value = false;
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
</style>
