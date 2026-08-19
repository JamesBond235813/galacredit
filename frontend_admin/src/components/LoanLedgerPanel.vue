<template>
  <section class="ledger-panel">
    <div v-if="loading" class="ledger-loading">
      <el-skeleton animated :rows="6" />
    </div>

    <template v-else-if="ledger">
      <div class="ledger-summary-grid">
        <article class="ledger-summary-card">
          <span>当前期数</span>
          <strong>{{ currentPeriodText }}</strong>
          <p>下一还款日 {{ formatDate(ledger.fund_flow_summary?.next_due_date) }}</p>
        </article>
        <article class="ledger-summary-card">
          <span>剩余待还</span>
          <strong>{{ formatCurrency(ledger.fund_flow_summary?.remaining_amount) }}</strong>
          <p>其中名义本金 {{ formatCurrency(ledger.fund_flow_summary?.principal_balance_amount) }}</p>
        </article>
        <article class="ledger-summary-card">
          <span>已实现收益</span>
          <strong>{{ formatCurrency(ledger.fund_flow_summary?.realized_income_amount) }}</strong>
          <p>预计收益 {{ formatCurrency(ledger.fund_flow_summary?.expected_income_amount) }}</p>
        </article>
        <article class="ledger-summary-card">
          <span>逾期账期</span>
          <strong>{{ ledger.fund_flow_summary?.overdue_installment_count || 0 }} 期</strong>
          <p>上扣费用余额 {{ formatCurrency(ledger.fund_flow_summary?.fee_balance_amount) }}</p>
        </article>
      </div>

      <div class="ledger-section">
        <div class="ledger-section-head">
          <h4>分期账单</h4>
          <span>{{ ledger.installments?.length || 0 }} 期</span>
        </div>
        <div v-if="ledger.installments?.length" class="installment-list">
          <article
            v-for="item in ledger.installments"
            :key="item.id || item.period_no"
            class="installment-item"
            :class="`installment-item-${String(item.status || '').toLowerCase()}`"
          >
            <div class="installment-row">
              <strong>第 {{ item.period_no }} 期</strong>
              <span class="installment-tag" :class="`installment-tag-${String(item.status || '').toLowerCase()}`">
                {{ getInstallmentStatusText(item.status) }}
              </span>
            </div>
            <div class="installment-meta-grid">
              <div>
                <span>还款日</span>
                <strong>{{ formatDate(item.due_date) }}</strong>
              </div>
              <div>
                <span>应还金额</span>
                <strong>{{ formatCurrency(item.due_amount) }}</strong>
              </div>
              <div>
                <span>剩余待还</span>
                <strong>{{ formatCurrency(item.remaining_amount) }}</strong>
              </div>
              <div>
                <span>已收/减免</span>
                <strong>{{ formatCurrency(item.paid_amount) }} / {{ formatCurrency(item.reduction_amount) }}</strong>
              </div>
            </div>
          </article>
        </div>
        <el-empty v-else description="暂无分期账单" />
      </div>

      <div class="ledger-section">
        <div class="ledger-section-head">
          <h4>资金流水</h4>
          <span>{{ ledger.transactions?.length || 0 }} 条</span>
        </div>
        <div v-if="ledger.transactions?.length" class="transaction-list">
          <article v-for="item in ledger.transactions" :key="item.id" class="transaction-item">
            <div class="transaction-row">
              <strong>{{ item.transaction_label }}</strong>
              <span>{{ formatCurrency(item.amount) }}</span>
            </div>
            <div class="transaction-breakdown">
              名义本金 {{ formatCurrency(item.principal_amount) }} · 上扣费用 {{ formatCurrency(Number(item.interest_amount || 0) + Number(item.guarantee_fee_amount || 0)) }} · 逾期费用 {{ formatCurrency(item.penalty_amount) }}
            </div>
            <div class="transaction-meta">
              <span>{{ item.operator_name || '系统' }}</span>
              <span>{{ formatDateTime(item.created_at) }}</span>
            </div>
            <p v-if="item.note" class="transaction-note">{{ item.note }}</p>
          </article>
        </div>
        <el-empty v-else description="暂无资金流水" />
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { formatCurrency, formatDate, formatDateTime } from '../utils/format';

const props = defineProps({
  ledger: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const currentPeriodText = computed(() => {
  const periodNo = props.ledger?.fund_flow_summary?.current_installment_period;
  if (!periodNo) {
    return '已结清';
  }
  return `第 ${periodNo} 期`;
});

const getInstallmentStatusText = (status) => ({
  CURRENT: '当前应还',
  PENDING: '待到期',
  OVERDUE: '已逾期',
  SETTLED: '已结清'
}[status] || status || '--');
</script>

<style scoped>
.ledger-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ledger-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.ledger-summary-card {
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: #ffffff;
}

.ledger-summary-card span {
  font-size: 12px;
  color: #7f8da2;
}

.ledger-summary-card strong {
  display: block;
  margin-top: 10px;
  font-size: 18px;
  color: #16233a;
}

.ledger-summary-card p {
  margin: 8px 0 0;
  font-size: 12px;
  color: #6b7a90;
}

.ledger-section {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: rgba(255, 255, 255, 0.88);
}

.ledger-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.ledger-section-head h4 {
  margin: 0;
  font-size: 15px;
  color: #16233a;
}

.ledger-section-head span {
  font-size: 12px;
  color: #7f8da2;
}

.installment-list,
.transaction-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.installment-item,
.transaction-item {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: #fff;
}

.installment-item-current {
  background: linear-gradient(180deg, rgba(245, 249, 255, 0.98) 0%, rgba(255, 255, 255, 1) 100%);
}

.installment-item-overdue {
  background: linear-gradient(180deg, rgba(255, 245, 245, 0.96) 0%, rgba(255, 255, 255, 1) 100%);
}

.installment-item-settled {
  background: linear-gradient(180deg, rgba(243, 251, 247, 0.96) 0%, rgba(255, 255, 255, 1) 100%);
}

.installment-row,
.transaction-row,
.transaction-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.installment-row strong,
.transaction-row strong {
  color: #16233a;
  font-size: 14px;
}

.installment-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
}

.installment-tag-current {
  background: rgba(47, 126, 247, 0.1);
  color: #2c72e5;
}

.installment-tag-pending {
  background: rgba(145, 159, 181, 0.12);
  color: #6d7b92;
}

.installment-tag-overdue {
  background: rgba(225, 88, 88, 0.12);
  color: #cf4c4c;
}

.installment-tag-settled {
  background: rgba(48, 215, 169, 0.14);
  color: #159b71;
}

.installment-meta-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.installment-meta-grid span,
.transaction-breakdown,
.transaction-meta,
.transaction-note {
  font-size: 12px;
  color: #6b7a90;
}

.installment-meta-grid strong {
  display: block;
  margin-top: 6px;
  font-size: 13px;
  color: #16233a;
}

.transaction-row span {
  font-size: 14px;
  font-weight: 700;
  color: #16233a;
}

.transaction-breakdown {
  margin-top: 8px;
  line-height: 1.7;
}

.transaction-meta {
  margin-top: 10px;
}

.transaction-note {
  margin: 8px 0 0;
  line-height: 1.7;
}

@media (max-width: 1280px) {
  .ledger-summary-grid,
  .installment-meta-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
