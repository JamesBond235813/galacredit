<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <div class="toolbar">
        <el-form :inline="true" :model="filters">
          <el-form-item label="搜索">
            <el-input
              v-model="filters.keyword"
              placeholder="请输入后台用户名"
              clearable
              @keyup.enter="fetchData"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchData">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <el-button type="primary" @click="openCreateDialog">新建后台用户</el-button>
      </div>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <div class="card-header">
          <div>
            <strong>后台用户列表</strong>
            <p>按角色分配后台职能，页面权限由角色自动映射。</p>
          </div>
          <el-tag type="info" effect="plain">共 {{ total }} 个账号</el-tag>
        </div>
      </template>

      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="账号信息" min-width="180">
          <template #default="{ row }">
            <div class="user-name-row">
              <span class="username">{{ row.username }}</span>
              <el-tag v-if="row.is_current" size="small" type="success" effect="plain">当前登录</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="220">
          <template #default="{ row }">
            <div class="permission-tags">
              <el-tag
                v-for="role in mapRoleLabels(row.roles)"
                :key="`${row.id}-role-${role}`"
                size="small"
                type="success"
                effect="plain"
              >
                {{ role }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="页面权限" min-width="320">
          <template #default="{ row }">
            <div class="permission-tags">
              <el-tag
                v-for="permission in mapPermissionLabels(row.permissions)"
                :key="`${row.id}-${permission}`"
                size="small"
                effect="plain"
              >
                {{ permission }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.is_active === false ? 'danger' : 'success'">{{ row.is_active === false ? '已禁用' : '启用' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <div class="action-group">
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link :type="row.is_active === false ? 'success' : 'warning'" :disabled="row.is_current" @click="toggleActive(row)">{{ row.is_active === false ? '启用' : '禁用' }}</el-button>
              <el-button link @click="showLoginHistory(row)">登录历史</el-button>
              <el-button
                link
                type="danger"
                :disabled="row.is_current"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </div>
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

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑后台用户' : '新建后台用户'"
      width="720px"
      destroy-on-close
    >
      <el-form label-position="top">
        <div class="form-grid">
          <el-form-item label="后台用户名" required>
            <el-input v-model="form.username" maxlength="50" placeholder="请输入后台用户名" />
          </el-form-item>
          <el-form-item :label="editingId ? '登录密码（留空则不修改）' : '登录密码'" required>
            <el-input
              v-model="form.password"
              type="password"
              show-password
              maxlength="50"
              :placeholder="editingId ? '如需修改密码请重新输入' : '请输入登录密码，至少 6 位'"
            />
          </el-form-item>
        </div>

        <el-form-item label="角色配置" required>
          <el-checkbox-group v-model="form.roles" class="permission-selector">
            <div
              v-for="item in ADMIN_ROLE_OPTIONS"
              :key="item.key"
              class="permission-option"
              :class="{ selected: form.roles.includes(item.key) }"
              @click="toggleRole(item.key)"
            >
              <div class="permission-title-row">
                <el-checkbox :value="item.key" @click.stop />
                <span class="permission-title">{{ item.label }}</span>
              </div>
              <span class="permission-route">{{ item.description }}</span>
            </div>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="角色映射权限">
          <div class="permission-tags">
            <el-tag
              v-for="permission in selectedPermissionLabels"
              :key="`preview-${permission}`"
              size="small"
              effect="plain"
            >
              {{ permission }}
            </el-tag>
            <el-empty
              v-if="!selectedPermissionLabels.length"
              :image-size="42"
              description="请选择角色后自动展示权限"
            />
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">
            {{ editingId ? '保存修改' : '创建账号' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
  <el-dialog v-model="loginHistoryVisible" title="登录历史"><el-table :data="loginHistory"><el-table-column prop="created_at" label="时间" /><el-table-column prop="client_type" label="客户端" /><el-table-column prop="success" label="结果"><template #default="{row}"><el-tag :type="row.success ? 'success' : 'danger'">{{ row.success ? '成功' : '失败' }}</el-tag></template></el-table-column><el-table-column prop="failure_reason" label="原因" /></el-table></el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  createAdminUser,
  deleteAdminUser,
  getAdminUsers,
  updateAdminUser
  ,getAdminLoginHistory
} from '../api';
import {
  ADMIN_ROLE_OPTIONS,
  ADMIN_PAGE_OPTIONS,
  buildPermissionsFromRoles,
  clearStoredAdminAuth
} from '../constants/adminPages';
import { formatDateTime } from '../utils/format';

const router = useRouter();
const loading = ref(false);
const loginHistoryVisible = ref(false); const loginHistory = ref([]);
const showLoginHistory = async (row) => { loginHistory.value = (await getAdminLoginHistory(row.id)).items || []; loginHistoryVisible.value = true; };
const saving = ref(false);
const dialogVisible = ref(false);
const editingId = ref(null);
const tableData = ref([]);
const total = ref(0);

const filters = reactive({
  keyword: '',
  page: 1,
  size: 10
});

const form = reactive({
  username: '',
  password: '',
  roles: []
});

const resetForm = () => {
  editingId.value = null;
  form.username = '';
  form.password = '';
  form.roles = [];
};

const mapPermissionLabels = (permissions) => {
  const labels = [];
  ADMIN_PAGE_OPTIONS.forEach((item) => {
    if ((permissions || []).includes(item.key)) {
      labels.push(item.label);
    }
  });
  return labels;
};

const mapRoleLabels = (roles) => {
  const labels = [];
  ADMIN_ROLE_OPTIONS.forEach((item) => {
    if ((roles || []).includes(item.key)) {
      labels.push(item.label);
    }
  });
  return labels;
};

const toggleRole = (roleKey) => {
  if (form.roles.includes(roleKey)) {
    form.roles = form.roles.filter((item) => item !== roleKey);
    return;
  }
  form.roles = [...form.roles, roleKey];
};

const selectedPermissionLabels = computed(() => mapPermissionLabels(buildPermissionsFromRoles(form.roles)));

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getAdminUsers({
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

const resetFilters = () => {
  filters.keyword = '';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const openCreateDialog = () => {
  resetForm();
  dialogVisible.value = true;
};

const openEditDialog = (row) => {
  editingId.value = row.id;
  form.username = row.username;
  form.password = '';
  form.roles = [...(row.roles || [])];
  dialogVisible.value = true;
};

const validateForm = () => {
  if (!form.username.trim()) {
    ElMessage.warning('请输入后台用户名');
    return false;
  }
  if (!editingId.value && form.password.trim().length < 6) {
    ElMessage.warning('新建账号时密码至少 6 位');
    return false;
  }
  if (editingId.value && form.password && form.password.trim().length < 6) {
    ElMessage.warning('修改密码时请输入至少 6 位的新密码');
    return false;
  }
  if (!form.roles.length) {
    ElMessage.warning('请至少勾选一个角色');
    return false;
  }
  return true;
};

const submitForm = async () => {
  if (!validateForm()) {
    return;
  }

  saving.value = true;
  try {
    const payload = {
      username: form.username.trim(),
      roles: [...form.roles]
    };

    if (!editingId.value || form.password.trim()) {
      payload.password = form.password.trim();
    }

    const res = editingId.value
      ? await updateAdminUser(editingId.value, payload)
      : await createAdminUser(payload);

    dialogVisible.value = false;

    if (res.is_current) {
      clearStoredAdminAuth();
      ElMessage.success('当前账号资料已更新，请重新登录');
      router.replace('/login');
      return;
    }

    ElMessage.success(editingId.value ? '后台用户已更新' : '后台用户已创建');
    fetchData();
  } finally {
    saving.value = false;
  }
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除后台用户“${row.username}”吗？删除后该账号将无法登录。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    );

    await deleteAdminUser(row.id);
    ElMessage.success('后台用户已删除');
    if (tableData.value.length === 1 && filters.page > 1) {
      filters.page -= 1;
    }
    fetchData();
  } catch (error) {
    //
  }
};

const toggleActive = async (row) => {
  await updateAdminUser(row.id, { is_active: row.is_active === false });
  ElMessage.success(row.is_active === false ? '账号已启用' : '账号已禁用');
  fetchData();
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.card-header strong {
  display: block;
  font-size: 16px;
  color: #16233a;
}

.card-header p {
  margin: 6px 0 0;
  font-size: 12px;
  color: #7b8ca4;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.username {
  font-weight: 600;
  color: #16233a;
}

.permission-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.permission-selector {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 12px;
  width: 100%;
}

.permission-option {
  border: 1px solid rgba(13, 63, 131, 0.1);
  border-radius: 18px;
  padding: 12px 14px;
  background: rgba(247, 250, 255, 0.76);
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 86px;
  cursor: pointer;
  box-sizing: border-box;
}

.permission-option.selected {
  border-color: rgba(44, 114, 229, 0.32);
  background: linear-gradient(180deg, rgba(44, 114, 229, 0.08) 0%, rgba(255, 255, 255, 0.96) 100%);
  box-shadow: 0 12px 24px rgba(21, 75, 159, 0.08);
}

.permission-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 22px;
}

.permission-title {
  font-size: 16px;
  color: #243852;
  line-height: 1.2;
  font-weight: 600;
}

.permission-route {
  padding-left: 26px;
  font-size: 12px;
  color: #7d8ea8;
  line-height: 1.45;
  white-space: normal;
  overflow-wrap: anywhere;
}

:deep(.permission-title-row .el-checkbox) {
  margin-right: 0;
}

:deep(.permission-title-row .el-checkbox__label) {
  display: none;
}

@media (max-width: 1200px) {
  .permission-selector {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .form-grid,
  .permission-selector {
    grid-template-columns: 1fr;
  }
}
</style>
