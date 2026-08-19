<template>
  <div class="admin-page insight-page">
    <section v-if="!loading && notes.length" class="board-notes">
      <span v-for="(note, idx) in notes" :key="`note-${idx}`">{{ note }}</span>
    </section>

    <section v-loading="loading" class="metrics-grid">
      <article v-for="card in cards" :key="card.key" class="metric-card">
        <h3>{{ translateInsightText(card.title) }}</h3>
        <strong class="metric-value">{{ formatCardValue(card.value, card.value_type) }}</strong>

        <div class="metric-foot">
          <span>{{ translateInsightText(card.sub_label) }}</span>
          <strong>{{ formatSubValue(card) }}</strong>
        </div>
      </article>

      <el-empty v-if="!loading && !cards.length" description="暂无可展示的洞察数据" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { getProjectCashInsights } from '../api';
import { formatCurrency } from '../utils/format';
import { tr } from '../i18n/adminLocale';

const loading = ref(false);
const insightSummary = ref({
  notes: [],
  cards: []
});

const cards = computed(() => insightSummary.value.cards || []);
const notes = computed(() => insightSummary.value.notes || []);

const formatCardValue = (value, valueType = 'currency') => {
  const amount = Number(value || 0);
  if (valueType === 'count') {
    return amount.toLocaleString('zh-CN');
  }
  return formatCurrency(amount);
};

const formatSubValue = (card) => {
  if (card?.sub_label === '--') {
    return '--';
  }
  return formatCardValue(card?.sub_value, card?.value_type);
};

const translateInsightText = (value) => {
  const map = {
    '注册数': ['注册数', 'Registrations'], '今日注册数': ['今日注册数', "Today's registrations"],
    '下单数': ['申请数', 'Applications'], '今日下单数': ['今日申请数', "Today's applications"],
    'E卡发放总额': ['MoMo放款总额', 'Total MoMo disbursement'],
    '今日E卡发放总额': ['今日MoMo放款总额', "Today's MoMo disbursement"],
    '发卡单数': ['放款单数', 'Disbursement count'],
    '今日发卡单数': ['今日放款单数', "Today's disbursement count"],
    '权益成本': ['上扣费用', 'Upfront fees'],
    '今日权益成本': ['今日上扣费用', "Today's upfront fees"],
    '逾期总额': ['逾期总额', 'Total overdue'], '昨日累计逾期金额': ['昨日累计逾期金额', "Yesterday's overdue amount"],
    '订单总额': ['应还总额', 'Total repayment'], '今日订单总额': ['今日应还总额', "Today's total repayment"],
    '收款金额': ['收款金额', 'Collected amount'], '今日收款金额': ['今日收款金额', "Today's collections"],
    '其他费用': ['其他费用', 'Other fees'], '今日其他费用': ['今日其他费用', "Today's other fees"],
    '应收金额': ['应收金额', 'Receivables'], '今日新增应收金额': ['今日新增应收金额', "Today's new receivables"],
    '待回收未逾期总资金': ['待回收未逾期资金', 'Pending non-overdue receivables']
  };
  const pair = map[value];
  return pair ? tr(pair[0], pair[1]) : value;
};

const loadData = async () => {
  loading.value = true;
  try {
    insightSummary.value = await getProjectCashInsights();
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.insight-page {
  gap: 16px;
}

.board-notes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.board-notes span {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(232, 239, 250, 0.9);
  color: #62758f;
  font-size: 12px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  border: 1px solid rgba(13, 63, 131, 0.08);
  border-radius: 22px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.94) 100%);
  box-shadow: 0 16px 36px rgba(16, 46, 91, 0.06);
}

.metric-card {
  min-height: 132px;
  padding: 16px 18px;
  border-right: 1px solid rgba(44, 114, 229, 0.08);
  border-bottom: 1px solid rgba(44, 114, 229, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.metric-card:nth-child(4n) {
  border-right: none;
}

.metric-card h3 {
  margin: 0;
  color: #16233a;
  font-size: 15px;
  font-weight: 700;
}

.metric-value {
  margin-top: 8px;
  color: #2c72e5;
  font-size: 26px;
  line-height: 1.2;
  font-weight: 700;
}

.metric-foot {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #7a8aa1;
  font-size: 12px;
}

.metric-foot strong {
  color: #7a8aa1;
  font-size: 14px;
  font-weight: 600;
}

@media (max-width: 1120px) {
  .metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .metric-card:nth-child(4n) {
    border-right: 1px solid rgba(44, 114, 229, 0.08);
  }

  .metric-card:nth-child(2n) {
    border-right: none;
  }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .metric-card {
    border-right: none;
  }

  .metric-value {
    font-size: 24px;
  }

  .metric-foot strong {
    font-size: 14px;
  }
}
</style>
