<template>
  <div class="admin-page message-center-page">
    <section class="summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="summary-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.tip }}</p>
      </article>
    </section>

    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>提醒队列</h2>
            <p>基于当前到期和逾期订单生成可发送队列，发送动作会回写到现有业务事件里。</p>
          </div>
          <el-button @click="fetchData">刷新</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="reminderQueue" stripe>
        <el-table-column label="客户" min-width="180">
          <template #default="{ row }">
            <div>{{ row.user_name || '--' }}</div>
            <div class="sub-text">{{ row.user_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="loan_id" label="订单号" width="100" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'OVERDUE' ? 'danger' : 'warning'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="应还金额" min-width="140">
          <template #default="{ row }">{{ formatCurrency(row.remaining_repayment_amount || row.total_repayment_amount || 0) }}</template>
        </el-table-column>
        <el-table-column label="到期日" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.due_date) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :loading="sendingLoanId === row.id" @click="sendReminder(row)">
              发送提醒
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>模板库</h2>
            <p>当前先提供预设模板，后续接短信供应商与文案版本库时可直接切换为服务端配置。</p>
          </div>
        </div>
      </template>

      <div class="template-grid">
        <article v-for="item in templates" :key="item.key" class="template-card">
          <div class="template-top">
            <strong>{{ item.title }}</strong>
            <el-tag :type="item.enabled ? 'success' : 'info'">{{ item.enabled ? '启用' : '停用' }}</el-tag>
          </div>
          <div class="sub-text">{{ item.channel }} / {{ item.trigger }}</div>
          <p>{{ item.body }}</p>
        </article>
      </div>

      <el-divider content-position="left">服务端模板版本</el-divider>
      <el-button type="primary" @click="openTemplateDialog()">新建模板版本</el-button>
      <el-table :data="serverTemplates" stripe style="margin-top: 12px">
        <el-table-column prop="template_key" label="标识" />
        <el-table-column prop="version_no" label="版本" width="80" />
        <el-table-column prop="title" label="标题" />
        <el-table-column label="状态" width="100"><template #default="{row}"><el-switch v-model="row.is_active" @change="toggleTemplate(row)" /></template></el-table-column>
        <el-table-column label="操作" width="100"><template #default="{row}"><el-button link type="primary" @click="openTemplateDialog(row)">编辑新版本</el-button></template></el-table-column>
      </el-table>

      <el-table :data="recentLogs" stripe class="recent-log-table">
        <el-table-column prop="created_at" label="发送时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="detail" label="详情" min-width="300" show-overflow-tooltip />
      </el-table>
    </el-card>
    <el-dialog v-model="templateDialog" title="消息模板版本" width="560px">
      <el-form label-position="top"><el-form-item label="模板标识"><el-input v-model="templateForm.template_key" /></el-form-item><el-form-item label="标题"><el-input v-model="templateForm.title" /></el-form-item><el-form-item label="内容"><el-input v-model="templateForm.content" type="textarea" rows="5" /></el-form-item></el-form>
      <template #footer><el-button @click="templateDialog=false">取消</el-button><el-button type="primary" @click="saveTemplate">保存新版本</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { getMessageCenter, sendAdminReminder, getMessageTemplates, saveMessageTemplate, toggleMessageTemplate } from '../api';
import { formatCurrency, formatDateTime } from '../utils/format';

const loading = ref(false);
const sendingLoanId = ref(null);
const summary = ref({ template_count: 0, enabled_template_count: 0, recent_message_count: 0 });
const templates = ref([]);
const recentLogs = ref([]);
const reminderQueue = ref([]);
const serverTemplates = ref([]); const templateDialog = ref(false); const templateForm = ref({ template_key: '', title: '', content: '' });

const summaryCards = computed(() => ([
  { label: '模板总数', value: Number(summary.value.template_count || 0), tip: '预设提醒模板数量' },
  { label: '启用模板', value: Number(summary.value.enabled_template_count || 0), tip: '当前可直接使用的模板' },
  { label: '历史触达', value: Number(summary.value.recent_message_count || 0), tip: '已记录的提醒/催收动作' },
  { label: '待提醒订单', value: Number(summary.value.reminder_queue_count || reminderQueue.value.length || 0), tip: '今天先补足的触达队列' }
]));

const fetchData = async () => {
  loading.value = true;
  try {
    const center = await getMessageCenter({ skip: 0, limit: 20 });
    summary.value = center.summary || summary.value;
    templates.value = center.templates || [];
    recentLogs.value = center.recent_logs || [];
    reminderQueue.value = center.reminder_queue || [];
    serverTemplates.value = (await getMessageTemplates()).items || [];
  } finally {
    loading.value = false;
  }
};

const openTemplateDialog = (row) => { templateForm.value = row ? { template_key: row.template_key, title: row.title, content: row.content } : { template_key: '', title: '', content: '' }; templateDialog.value = true; };
const saveTemplate = async () => { await saveMessageTemplate(templateForm.value); templateDialog.value = false; ElMessage.success('模板版本已保存'); await fetchData(); };
const toggleTemplate = async (row) => { await toggleMessageTemplate(row.id, { is_active: row.is_active }); ElMessage.success('模板状态已更新'); };

const sendReminder = async (row) => {
  sendingLoanId.value = row.id;
  try {
    await sendAdminReminder(row.id, { note: '运营中心批量提醒' });
    ElMessage.success('提醒已发送');
    await fetchData();
  } finally {
    sendingLoanId.value = null;
  }
};

onMounted(fetchData);
</script>
