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
            <h2>调度与运行状态</h2>
            <p>聚合审计、KYC、消息、资金与定时任务状态，帮助值班同学快速判断系统是否健康。</p>
          </div>
          <el-button @click="fetchData">刷新</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="jobs" stripe>
        <el-table-column prop="job_id" label="任务ID" min-width="180" />
        <el-table-column label="下一次执行" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.next_run_time) }}</template>
        </el-table-column>
        <el-table-column prop="trigger" label="调度器" min-width="180" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.pending ? 'danger' : 'success'">{{ row.pending ? '待执行' : '正常' }}</el-tag>
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
  { label: '24h 审计操作', value: Number(summary.value.admin_event_count_24h || 0), tip: '管理员动作与运营处理记录' },
  { label: '待复核 KYC', metric: 'kyc_pending', value: Number(summary.value.kyc_pending_count || 0), tip: '需要人工继续处理的客户' },
  { label: '24h 提醒', value: Number(summary.value.reminder_event_count_24h || 0), tip: '到期提醒发送量' },
  { label: '24h 催收', value: Number(summary.value.collection_event_count_24h || 0), tip: '催收动作数量' },
  { label: '待处理 MoMo', metric: 'momo_pending', value: Number(summary.value.momo_pending_count || 0), tip: '待确认交易流水' },
  { label: '失败 MoMo', metric: 'momo_failed', value: Number(summary.value.momo_failed_count || 0), tip: '需要补偿的失败流水' },
  { label: '有效合规规则', value: Number(summary.value.active_compliance_rule_count || 0), tip: '当前启用中的合规配置' },
  { label: '逾期订单', value: Number(summary.value.overdue_loan_count || 0), tip: '当前逾期资产规模' }
]));

const jobs = computed(() => summary.value.scheduled_jobs || []);
const openDrilldown = async (metric) => { if (!metric) return; const data = await getMonitoringDrilldown(metric); await ElMessageBox.alert((data.items || []).map(item => `${item.id || ''} ${item.phone || item.loan_id || ''} ${item.status || ''}`).join('\n') || '暂无明细', `指标下钻：${metric}`); };

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
