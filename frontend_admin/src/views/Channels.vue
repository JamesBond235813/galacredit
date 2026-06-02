<template>
  <div class="admin-page">
    <section class="metrics-grid">
      <article v-for="card in metricCards" :key="card.label" class="metric-card">
        <div class="metric-label">{{ card.label }}</div>
        <div class="metric-value">{{ card.value }}</div>
        <div class="metric-tip">{{ card.tip }}</div>
      </article>
    </section>

    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="渠道名称 / 业务员"
            clearable
            @keyup.enter="fetchData"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" style="width: 150px">
            <el-option label="全部" value="ALL" />
            <el-option label="启用中" value="ACTIVE" />
            <el-option label="已停用" value="INACTIVE" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button plain @click="openCreateDrawer">新增渠道</el-button>
        </el-form-item>
      </el-form>
      <div class="filter-tip">专属链接格式：{{ sanitizedDomain }}/invite_code。用户首次通过有效链接登录后，将按首个渠道归因统计业绩。</div>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column label="渠道 / 业务员" min-width="220">
          <template #default="{ row }">
            <div>{{ row.sales_name }}</div>
            <div class="sub-text">顾问：{{ row.admin_user_name || '--' }}<span v-if="row.admin_user_id">（#{{ row.admin_user_id }}）</span></div>
            <div class="sub-text">/{{ row.invite_code }}</div>
          </template>
        </el-table-column>
        <el-table-column label="专属链接" min-width="260">
          <template #default="{ row }">
            <div class="link-cell">{{ getRowChannelLink(row) }}</div>
            <el-button link type="primary" @click="copyChannelLink(getRowChannelLink(row))">复制链接</el-button>
          </template>
        </el-table-column>
        <el-table-column label="二维码" width="120">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'ACTIVE'"
              link
              type="primary"
              @click="openQrDialog(row)"
            >
              查看
            </el-button>
            <span v-else>--</span>
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
        <el-table-column prop="application_count" label="申请量" width="90" />
        <el-table-column label="发卡表现" min-width="160">
          <template #default="{ row }">
            <div>{{ row.disbursed_user_count }} 人</div>
            <div class="sub-text">{{ formatCurrency(row.disbursed_amount) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="逾期表现" min-width="160">
          <template #default="{ row }">
            <div>{{ row.overdue_user_count }} 人</div>
            <div class="sub-text">{{ formatCurrency(row.overdue_amount) }} · {{ formatRateValue(row.overdue_rate) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="最近进件 / 发卡" min-width="180">
          <template #default="{ row }">
            <div>{{ formatDateTime(row.latest_application_at) }}</div>
            <div class="sub-text">{{ formatDateTime(row.latest_disbursed_at) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="180">
          <template #default="{ row }">
            {{ row.note || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDrawer(row)">编辑</el-button>
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
      v-model="qrDialogVisible"
      width="420px"
      title=""
      append-to-body
      destroy-on-close
      @opened="renderQrCode"
    >
      <div class="qr-dialog-shell">
        <div class="qr-brand">
          <strong>小荷包</strong>
          <span>解生活之所急</span>
        </div>
        <div class="qr-card">
          <div class="qr-canvas-wrap">
            <canvas ref="qrCanvasRef" class="qr-canvas" aria-label="专属链接二维码"></canvas>
            <img :src="logoUrl" class="qr-logo" alt="小荷包 logo" />
          </div>
        </div>
        <div class="qr-actions">
          <el-button @click="copyChannelLink(activeQrLink)">复制链接</el-button>
          <el-button type="primary" @click="qrDialogVisible = false">关闭</el-button>
        </div>
      </div>
    </el-dialog>

    <el-drawer v-model="drawerVisible" size="560px" :title="drawerTitle" destroy-on-close>
      <div class="detail-stack">
        <section class="detail-card">
          <h3>渠道配置</h3>
          <el-form label-width="88px">
            <el-form-item label="业务员">
              <el-input v-model="form.sales_name" maxlength="50" placeholder="填写业务员姓名" />
            </el-form-item>
            <el-form-item label="渠道名称">
              <el-input
                v-model="form.channel_name"
                maxlength="32"
                :disabled="form.mode === 'edit'"
                placeholder="例如 xiaojiang_01"
                @blur="normalizeFormChannelName"
              />
            </el-form-item>
            <el-form-item v-if="form.mode === 'edit'" label="邀请码">
              <el-input v-model="form.invite_code" disabled />
            </el-form-item>
            <el-form-item label="渠道状态">
              <el-radio-group v-model="form.status">
                <el-radio value="ACTIVE">启用中</el-radio>
                <el-radio value="INACTIVE">已停用</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="业务顾问">
              <el-select
                v-model="form.admin_user_id"
                filterable
                remote
                reserve-keyword
                clearable
                placeholder="输入用户ID或用户名搜索业务顾问"
                :remote-method="fetchBusinessAdvisorOptions"
                :loading="advisorOptionsLoading"
                style="width: 100%"
              >
                <el-option
                  v-for="item in advisorOptions"
                  :key="item.id"
                  :label="`${item.username} (#${item.id})`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="备注">
              <el-input
                v-model="form.note"
                type="textarea"
                :rows="3"
                maxlength="255"
                show-word-limit
                placeholder="填写渠道说明、投放场景或业务员备注"
              />
            </el-form-item>
          </el-form>
        </section>

        <section class="detail-card">
          <h3>专属链接预览</h3>
          <div class="preview-link-box">{{ buildChannelLink(form.invite_code || 'invite_code') }}</div>
          <div class="drawer-footer">
            <el-button @click="copyChannelLink(form.invite_code || 'invite_code')">复制链接</el-button>
          </div>
        </section>

        <section v-if="form.mode === 'edit'" class="detail-card">
          <h3>业绩快照</h3>
          <div class="channel-preview-grid">
            <article class="channel-preview-card">
              <span>归属用户</span>
              <strong>{{ activeRow?.attributed_user_count || 0 }}</strong>
            </article>
            <article class="channel-preview-card">
              <span>申请量</span>
              <strong>{{ activeRow?.application_count || 0 }}</strong>
            </article>
            <article class="channel-preview-card">
              <span>发卡金额</span>
              <strong>{{ formatCurrency(activeRow?.disbursed_amount || 0) }}</strong>
            </article>
            <article class="channel-preview-card">
              <span>逾期率</span>
              <strong>{{ formatRateValue(activeRow?.overdue_rate || 0) }}</strong>
            </article>
          </div>
        </section>

        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { createChannel, getBusinessAdvisors, getChannels, updateChannel } from '../api';
import logoUrl from '../assets/logo.svg';
import { generateChannelInviteCode } from '../utils/channel';
import { renderChannelQr } from '../utils/channelQr';
import { formatCurrency, formatDateTime } from '../utils/format';

const loading = ref(false);
const submitting = ref(false);
const drawerVisible = ref(false);
const tableData = ref([]);
const total = ref(0);
const summary = ref({});
const activeRow = ref(null);
const advisorOptions = ref([]);
const advisorOptionsLoading = ref(false);
const h5Domain = ref('https://xxx.xx');
const qrDialogVisible = ref(false);
const activeQrRow = ref(null);
const qrCanvasRef = ref(null);

const filters = reactive({
  keyword: '',
  status: 'ALL',
  page: 1,
  size: 10
});

const form = reactive({
  mode: 'create',
  id: null,
  sales_name: '',
  channel_name: '',
  invite_code: '',
  status: 'ACTIVE',
  note: '',
  admin_user_id: null
});

const upsertAdvisorOption = (item) => {
  if (!item || !item.id) {
    return;
  }
  const existed = advisorOptions.value.some((option) => Number(option.id) === Number(item.id));
  if (!existed) {
    advisorOptions.value = [item, ...advisorOptions.value];
  }
};

const fetchBusinessAdvisorOptions = async (keyword = '') => {
  advisorOptionsLoading.value = true;
  try {
    const items = await getBusinessAdvisors({
      keyword: keyword || undefined,
      limit: 20
    });
    advisorOptions.value = Array.isArray(items) ? items : [];
  } finally {
    advisorOptionsLoading.value = false;
  }
};

const sanitizedDomain = computed(() => {
  const value = (h5Domain.value || '').trim();
  return value.replace(/\/+$/, '') || 'https://xxx.xx';
});

const drawerTitle = computed(() => (form.mode === 'edit' ? '编辑渠道' : '新增渠道'));

const metricCards = computed(() => [
  {
    label: '渠道总数',
    value: summary.value.total_channels || 0,
    tip: `启用中 ${summary.value.active_channels || 0} 个`
  },
  {
    label: '归属用户',
    value: summary.value.attributed_user_count || 0,
    tip: `已提交资料 ${summary.value.submitted_user_count || 0} 人`
  },
  {
    label: '累计申请量',
    value: summary.value.application_count || 0,
    tip: '按归属渠道统计全部申请订单'
  },
  {
    label: '发卡人数',
    value: summary.value.disbursed_user_count || 0,
    tip: `发卡金额 ${formatCurrency(summary.value.disbursed_amount || 0)}`
  },
  {
    label: '逾期人数',
    value: summary.value.overdue_user_count || 0,
    tip: `逾期金额 ${formatCurrency(summary.value.overdue_amount || 0)}`
  },
  {
    label: '整体逾期率',
    value: formatRateValue(summary.value.overdue_rate || 0),
    tip: '逾期人数 / 发卡人数'
  }
]);

const formatRateValue = (value) => `${Number(value || 0).toFixed(2)}%`;

const buildChannelLink = (inviteCode) => `${sanitizedDomain.value}/${String(inviteCode || '').replace(/^\/+/, '')}`;
const getRowInviteCode = (row) => row?.daily_invite_code || row?.invite_code;
const getRowChannelLink = (row) => buildChannelLink(getRowInviteCode(row));
const activeQrLink = computed(() => (activeQrRow.value ? getRowChannelLink(activeQrRow.value) : ''));

const normalizeFormChannelName = () => {
  form.channel_name = String(form.channel_name || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9_-]/g, '');
};

const copyChannelLink = async (link) => {
  try {
    await navigator.clipboard.writeText(link);
    ElMessage.success('专属链接已复制');
  } catch (error) {
    ElMessage.error('复制失败，请手动复制');
  }
};

const renderQrCode = async () => {
  await nextTick();
  if (!qrCanvasRef.value || !activeQrLink.value) {
    return;
  }

  try {
    await renderChannelQr(qrCanvasRef.value, activeQrLink.value);
  } catch (error) {
    ElMessage.error('二维码生成失败，请稍后重试');
  }
};

const openQrDialog = (row) => {
  activeQrRow.value = row;
  qrDialogVisible.value = true;
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getChannels({
      keyword: filters.keyword || undefined,
      status: filters.status,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    h5Domain.value = String(res.channel_link_prefix || 'https://xxx.xx');
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.keyword = '';
  filters.status = 'ALL';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const resetForm = () => {
  form.mode = 'create';
  form.id = null;
  form.sales_name = '';
  form.channel_name = '';
  form.invite_code = '';
  form.status = 'ACTIVE';
  form.note = '';
  form.admin_user_id = null;
  activeRow.value = null;
};

const openCreateDrawer = () => {
  resetForm();
  form.invite_code = generateChannelInviteCode(16);
  drawerVisible.value = true;
};

const openEditDrawer = (row) => {
  form.mode = 'edit';
  form.id = row.id;
  form.sales_name = row.sales_name;
  form.channel_name = row.channel_name;
  form.invite_code = row.invite_code || '';
  form.status = row.status;
  form.note = row.note || '';
  form.admin_user_id = row.admin_user_id || null;
  upsertAdvisorOption({
    id: row.admin_user_id,
    username: row.admin_user_name
  });
  activeRow.value = row;
  drawerVisible.value = true;
};

const validateForm = () => {
  normalizeFormChannelName();

  if (!form.sales_name.trim()) {
    ElMessage.warning('请填写业务员姓名');
    return false;
  }

  if (!/^[a-z0-9][a-z0-9_-]{1,31}$/.test(form.channel_name)) {
    ElMessage.warning('渠道名称仅支持 2-32 位小写字母、数字、中划线和下划线');
    return false;
  }

  if (!form.admin_user_id) {
    ElMessage.warning('请选择业务顾问');
    return false;
  }

  return true;
};

const submitForm = async () => {
  if (!validateForm()) {
    return;
  }

  submitting.value = true;
  try {
    if (form.mode === 'edit') {
      await updateChannel(form.id, {
        sales_name: form.sales_name.trim(),
        status: form.status,
        note: form.note,
        admin_user_id: form.admin_user_id
      });
      ElMessage.success('渠道已更新');
    } else {
      await createChannel({
        sales_name: form.sales_name.trim(),
        channel_name: form.channel_name,
        invite_code: form.invite_code,
        status: form.status,
        note: form.note,
        admin_user_id: form.admin_user_id
      });
      ElMessage.success('渠道已创建');
    }

    drawerVisible.value = false;
    fetchData();
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  fetchBusinessAdvisorOptions();
  fetchData();
});
</script>

<style scoped>
.sub-text {
  margin-top: 4px;
  color: #7f8da2;
  font-size: 12px;
}

.filter-tip {
  margin-top: 10px;
  font-size: 12px;
  color: #6b7a90;
}

.link-cell {
  font-size: 13px;
  color: #20324d;
  word-break: break-all;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.preview-link-box {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: #ffffff;
  color: #1f2f46;
  font-size: 13px;
  line-height: 1.7;
  word-break: break-all;
}

.channel-preview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.channel-preview-card {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: #ffffff;
}

.channel-preview-card span {
  display: block;
  font-size: 12px;
  color: #7a8aa1;
}

.channel-preview-card strong {
  display: block;
  margin-top: 10px;
  font-size: 20px;
  color: #16233a;
}

.qr-dialog-shell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.qr-brand {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  color: #1d2f49;
}

.qr-brand strong {
  color: #1d2f49;
  font-size: 20px;
}

.qr-brand span {
  color: #7f8da2;
  font-size: 14px;
}

.qr-card {
  padding: 18px;
  border: 1px solid #e8eef7;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.qr-canvas-wrap,
.qr-canvas {
  width: 260px;
  height: 260px;
}

.qr-canvas-wrap {
  position: relative;
}

.qr-canvas {
  display: block;
}

.qr-logo {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 54px;
  height: 54px;
  padding: 6px;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(18, 46, 86, 0.14);
  transform: translate(-50%, -50%);
}

.qr-actions {
  display: flex;
  align-self: stretch;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-dialog__title) {
  display: none;
}
</style>
