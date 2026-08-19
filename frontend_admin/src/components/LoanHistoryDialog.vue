<template>
  <el-dialog
    v-model="dialogVisible"
    width="720px"
    title="最近一次正常结清账单"
    append-to-body
    destroy-on-close
  >
    <div v-if="loan" class="history-shell">
      <section class="history-hero">
        <div>
          <span class="history-eyebrow">{{ borrowerName || '借款人' }}</span>
          <h3>最近一次正常结清账单</h3>
          <p>仅展示最近一次正常结清的借款账单，其余历史账单继续保留在数据库中。</p>
        </div>
        <el-tag type="success" effect="plain">已结清</el-tag>
      </section>

      <section class="history-grid">
        <article class="history-card">
          <span>名义本金</span>
          <strong>{{ formatCurrency(resolveNominalAmount(loan)) }}</strong>
        </article>
        <article class="history-card">
          <span>账期</span>
          <strong>{{ loan.term_days ? `${loan.term_days} 天` : '--' }}</strong>
        </article>
        <article class="history-card">
          <span>上扣费用</span>
          <strong>{{ formatCurrency(resolveUpfrontFee(loan)) }}</strong>
        </article>
        <article class="history-card">
          <span>MoMo到账</span>
          <strong>{{ formatCurrency(resolveDisbursementAmount(loan)) }}</strong>
        </article>
        <article class="history-card">
          <span>总还款额</span>
          <strong>{{ formatCurrency(loan.total_repayment_amount) }}</strong>
        </article>
        <article class="history-card">
          <span>实际结清额</span>
          <strong>{{ formatCurrency(Number(loan.repaid_amount || 0) + Number(loan.reduction_amount || 0)) }}</strong>
        </article>
      </section>

      <section class="history-meta">
        <div class="meta-row">
          <span>放款时间</span>
          <strong>{{ formatDateTime(loan.disbursed_at) }}</strong>
        </div>
        <div class="meta-row">
          <span>还款日</span>
          <strong>{{ formatDateTime(loan.due_date) }}</strong>
        </div>
        <div class="meta-row">
          <span>减免金额</span>
          <strong>{{ formatCurrency(loan.reduction_amount) }}</strong>
        </div>
        <div class="meta-row">
          <span>剩余还款额</span>
          <strong>{{ formatCurrency(loan.remaining_repayment_amount) }}</strong>
        </div>
      </section>
    </div>
    <el-empty v-else description="暂无历史结清账单" />
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue';
import { formatCurrency, formatDateTime } from '../utils/format';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  loan: {
    type: Object,
    default: null
  },
  borrowerName: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue']);

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const resolveEcardFaceValue = (row) => Number(row?.ecard_face_value || row?.credit_limit || 0);
const resolveNominalAmount = (row) => Number(row?.nominal_loan_amount || row?.total_repayment_amount || row?.credit_limit || resolveEcardFaceValue(row));
const resolveDisbursementAmount = (row) => Number(row?.actual_disbursement_amount || row?.ecard_face_value || 0);
const resolveUpfrontFee = (row) => Number(row?.upfront_fee_amount || row?.fee_amount || Math.max(resolveNominalAmount(row) - resolveDisbursementAmount(row), 0));
</script>

<style scoped>
.history-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(44, 114, 229, 0.08) 0%, rgba(104, 213, 181, 0.08) 100%);
  border: 1px solid rgba(44, 114, 229, 0.1);
}

.history-eyebrow {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #5f7188;
}

.history-hero h3 {
  margin: 0;
  font-size: 20px;
  color: #16233a;
}

.history-hero p {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: #6f8097;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.history-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.94) 100%);
}

.history-card span {
  display: block;
  font-size: 12px;
  color: #7a8aa1;
}

.history-card strong {
  display: block;
  margin-top: 10px;
  font-size: 20px;
  color: #16233a;
}

.history-meta {
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid rgba(13, 63, 131, 0.08);
  background: rgba(248, 251, 255, 0.9);
}

.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed rgba(13, 63, 131, 0.08);
  color: #66788f;
}

.meta-row:last-child {
  border-bottom: none;
}

.meta-row strong {
  color: #16233a;
}

@media (max-width: 960px) {
  .history-grid {
    grid-template-columns: 1fr;
  }
}
</style>
