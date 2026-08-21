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
          <h2>{{ tr('提醒队列', 'Reminder queue') }}</h2>
            <p>{{ tr('基于当前到期和逾期订单生成可发送队列，发送动作会回写到现有业务事件里。', 'A sendable queue based on due and overdue loans. Sends are recorded in business events.') }}</p>
          </div>
          <el-button @click="fetchData">{{ tr('刷新', 'Refresh') }}</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="reminderQueue" stripe>
        <el-table-column :label="tr('客户', 'Borrower')" min-width="180">
          <template #default="{ row }">
            <div>{{ row.user_name || '--' }}</div>
            <div class="sub-text">{{ row.user_phone }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="loan_id" :label="tr('订单号', 'Loan ID')" width="100" />
        <el-table-column :label="tr('状态', 'Status')" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'OVERDUE' ? 'danger' : 'warning'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="tr('应还金额', 'Amount due')" min-width="140">
          <template #default="{ row }">{{ formatCurrency(row.remaining_repayment_amount || row.total_repayment_amount || 0) }}</template>
        </el-table-column>
        <el-table-column :label="tr('到期日', 'Due date')" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.due_date) }}</template>
        </el-table-column>
        <el-table-column :label="tr('操作', 'Actions')" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :loading="sendingLoanId === row.id" @click="sendReminder(row)">
              {{ tr('发送提醒', 'Send reminder') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
          <h2>{{ tr('模板库', 'Template library') }}</h2>
            <p>{{ tr('当前先提供预设模板，后续接短信供应商与文案版本库时可直接切换为服务端配置。', 'Preset templates are shown here and can later be switched to provider-managed versions.') }}</p>
          </div>
        </div>
      </template>

      <div class="template-grid">
        <article v-for="item in templates" :key="item.key" class="template-card">
          <div class="template-top">
            <strong>{{ displayText(item.title) }}</strong>
            <el-tag :type="item.enabled ? 'success' : 'info'">{{ item.enabled ? tr('启用', 'Active') : tr('停用', 'Inactive') }}</el-tag>
          </div>
          <div class="sub-text">{{ item.channel }} / {{ item.trigger }}</div>
          <p>{{ displayText(item.body) }}</p>
        </article>
      </div>

      <el-divider content-position="left">{{ tr('服务端模板版本', 'Server template versions') }}</el-divider>
      <el-button type="primary" @click="openTemplateDialog()">{{ tr('新建模板版本', 'New template version') }}</el-button>
      <el-table :data="serverTemplates" stripe style="margin-top: 12px">
        <el-table-column prop="template_key" :label="tr('标识', 'Key')" />
        <el-table-column prop="version_no" :label="tr('版本', 'Version')" width="80" />
        <el-table-column prop="title" :label="tr('标题', 'Title')" />
        <el-table-column :label="tr('状态', 'Status')" width="100"><template #default="{row}"><el-switch v-model="row.is_active" @change="toggleTemplate(row)" /></template></el-table-column>
        <el-table-column :label="tr('操作', 'Actions')" width="100"><template #default="{row}"><el-button link type="primary" @click="openTemplateDialog(row)">{{ tr('编辑新版本', 'Edit version') }}</el-button></template></el-table-column>
      </el-table>

      <el-table :data="recentLogs" stripe class="recent-log-table">
        <el-table-column prop="created_at" :label="tr('发送时间', 'Sent at')" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="title" :label="tr('标题', 'Title')" min-width="180" />
        <el-table-column prop="detail" :label="tr('详情', 'Details')" min-width="300" show-overflow-tooltip />
      </el-table>
    </el-card>
    <el-dialog v-model="templateDialog" :title="tr('消息模板版本', 'Message template version')" width="560px">
      <el-form label-position="top"><el-form-item :label="tr('模板标识', 'Template key')"><el-input v-model="templateForm.template_key" /></el-form-item><el-form-item :label="tr('标题', 'Title')"><el-input v-model="templateForm.title" /></el-form-item><el-form-item :label="tr('内容', 'Content')"><el-input v-model="templateForm.content" type="textarea" rows="5" /></el-form-item></el-form>
      <template #footer><el-button @click="templateDialog=false">{{ tr('取消', 'Cancel') }}</el-button><el-button type="primary" @click="saveTemplate">{{ tr('保存新版本', 'Save new version') }}</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { getMessageCenter, sendAdminReminder, getMessageTemplates, saveMessageTemplate, toggleMessageTemplate } from '../api';
import { formatCurrency, formatDateTime } from '../utils/format';
import { adminLocale, tr } from '../i18n/adminLocale';

const loading = ref(false);
const sendingLoanId = ref(null);
const summary = ref({ template_count: 0, enabled_template_count: 0, recent_message_count: 0 });
const templates = ref([]);
const recentLogs = ref([]);
const reminderQueue = ref([]);
const serverTemplates = ref([]); const templateDialog = ref(false); const templateForm = ref({ template_key: '', title: '', content: '' });
const displayText = (value) => {
  if (!value) return value;
  const translations = {
    'Due日提醒': 'Due date reminder',
    'Overdue第一大提醒': 'First overdue reminder',
    'Overdue第二大提醒': 'Second overdue reminder',
    '您的还款今天Due，请尽快完成还款。': 'Your repayment is due today. Please complete it as soon as possible.',
    '您的账单已Overdue 1天，请尽快处理。': 'Your loan is 1 day overdue. Please take action.',
    '您的账单已Overdue 3天，请及时联系催收。': 'Your loan is 3 days overdue. Please contact collections promptly.'
  };
  return adminLocale.value === 'en-GH' ? (translations[value] || value) : value;
};

const summaryCards = computed(() => ([
  { label: tr('模板总数', 'Total templates'), value: Number(summary.value.template_count || 0), tip: tr('预设提醒模板数量', 'Preset reminder templates') },
  { label: tr('启用模板', 'Active templates'), value: Number(summary.value.enabled_template_count || 0), tip: tr('当前可直接使用的模板', 'Templates ready to use') },
  { label: tr('历史触达', 'Historical sends'), value: Number(summary.value.recent_message_count || 0), tip: tr('已记录的提醒/催收动作', 'Recorded reminder and collection actions') },
  { label: tr('待提醒订单', 'Loans to remind'), value: Number(summary.value.reminder_queue_count || reminderQueue.value.length || 0), tip: tr('今天先补足的触达队列', 'Queue requiring attention today') }
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
const saveTemplate = async () => { await saveMessageTemplate(templateForm.value); templateDialog.value = false; ElMessage.success(tr('模板版本已保存', 'Template version saved')); await fetchData(); };
const toggleTemplate = async (row) => { await toggleMessageTemplate(row.id, { is_active: row.is_active }); ElMessage.success(tr('模板状态已更新', 'Template status updated')); };

const sendReminder = async (row) => {
  sendingLoanId.value = row.id;
  try {
    await sendAdminReminder(row.id, { note: '运营中心批量提醒' });
    ElMessage.success(tr('提醒已发送', 'Reminder sent'));
    await fetchData();
  } finally {
    sendingLoanId.value = null;
  }
};

onMounted(fetchData);
</script>
