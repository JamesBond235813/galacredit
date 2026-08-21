<template>
  <div class="admin-page monitoring-page">
    <section class="summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="summary-card">
        <span>{{ card.label }}</span>
        <strong class="drilldown-value" @click="openDrilldown(card.metric)">{{ card.value }}</strong>
        <p>{{ card.tip }}</p>
      </article>
    </section>

    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>{{ tr('调度与运行状态', 'Scheduling and runtime status') }}</h2>
            <p>{{ tr('聚合审计、KYC、消息、资金与定时任务状态，帮助值班同学快速判断系统是否健康。', 'Combined audit, KYC, messaging, fund and scheduled-job status for fast operational health checks.') }}</p>
          </div>
          <el-button @click="fetchData">{{ tr('刷新', 'Refresh') }}</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="jobs" stripe>
        <el-table-column prop="job_id" :label="tr('任务ID', 'Job ID')" min-width="180" />
        <el-table-column :label="tr('下一次执行', 'Next run')" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.next_run_time) }}</template>
        </el-table-column>
        <el-table-column prop="trigger" :label="tr('调度器', 'Scheduler')" min-width="180" />
        <el-table-column :label="tr('状态', 'Status')" width="110">
          <template #default="{ row }">
            <el-tag :type="row.pending ? 'danger' : 'success'">{{ row.pending ? tr('待执行', 'Pending') : tr('正常', 'Healthy') }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { getMonitoringSummary, getMonitoringDrilldown } from '../api';
import { ElMessageBox } from 'element-plus';
import { formatDateTime } from '../utils/format';
import { tr } from '../i18n/adminLocale';

const loading = ref(false);
const summary = ref({
  admin_event_count_24h: 0,
  kyc_pending_count: 0,
  reminder_event_count_24h: 0,
  collection_event_count_24h: 0,
  momo_pending_count: 0,
  momo_failed_count: 0,
  active_compliance_rule_count: 0,
  overdue_loan_count: 0,
  scheduled_jobs: []
});

const summaryCards = computed(() => ([
  { label: tr('24h 审计操作', '24h audit actions'), value: Number(summary.value.admin_event_count_24h || 0), tip: tr('管理员动作与运营处理记录', 'Admin and operational actions') },
  { label: tr('待复核 KYC', 'Pending KYC review'), metric: 'kyc_pending', value: Number(summary.value.kyc_pending_count || 0), tip: tr('需要人工继续处理的客户', 'Borrowers requiring manual review') },
  { label: tr('24h 提醒', '24h reminders'), value: Number(summary.value.reminder_event_count_24h || 0), tip: tr('到期提醒发送量', 'Due reminders sent') },
  { label: tr('24h 催收', '24h collections'), value: Number(summary.value.collection_event_count_24h || 0), tip: tr('催收动作数量', 'Collection action count') },
  { label: tr('待处理 MoMo', 'Pending MoMo'), metric: 'momo_pending', value: Number(summary.value.momo_pending_count || 0), tip: tr('待确认交易流水', 'Transactions awaiting confirmation') },
  { label: tr('失败 MoMo', 'Failed MoMo'), metric: 'momo_failed', value: Number(summary.value.momo_failed_count || 0), tip: tr('需要补偿的失败流水', 'Failed transactions requiring remediation') },
  { label: tr('有效合规规则', 'Active compliance rules'), value: Number(summary.value.active_compliance_rule_count || 0), tip: tr('当前启用中的合规配置', 'Currently active compliance configurations') },
  { label: tr('逾期订单', 'Overdue loans'), value: Number(summary.value.overdue_loan_count || 0), tip: tr('当前逾期资产规模', 'Current overdue portfolio') }
]));

const jobs = computed(() => summary.value.scheduled_jobs || []);
const openDrilldown = async (metric) => { if (!metric) return; const data = await getMonitoringDrilldown(metric); await ElMessageBox.alert((data.items || []).map(item => `${item.id || ''} ${item.phone || item.loan_id || ''} ${item.status || ''}`).join('\n') || tr('暂无明细', 'No details'), `${tr('指标下钻', 'Metric drilldown')}: ${metric}`); };

const fetchData = async () => {
  loading.value = true;
  try {
    summary.value = await getMonitoringSummary();
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);
</script>
