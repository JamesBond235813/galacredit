import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const currentDir = dirname(fileURLToPath(import.meta.url));
const repaymentsSource = readFileSync(resolve(currentDir, 'Repayments.vue'), 'utf-8');
const collectionsSource = readFileSync(resolve(currentDir, 'Collections.vue'), 'utf-8');
const financialSource = readFileSync(resolve(currentDir, 'FinancialReconciliation.vue'), 'utf-8');

describe('repayments bill progress display', () => {
  it('should only render settled tag for settled loans', () => {
    expect(repaymentsSource).toContain('v-if="isLoanSettled(row)"');
    expect(repaymentsSource).toContain('<template v-else>');
    expect(repaymentsSource).toContain("row?.status === 'SETTLED'");
  });

  it('should use separate query buttons for keyword and repayment time filters', () => {
    expect(repaymentsSource).toContain('@click="handleSearch"');
    expect(repaymentsSource).toContain('@click="handleDueDateSearch"');
    expect(repaymentsSource).toContain('@click="handleActualRepaymentSearch"');
    expect(repaymentsSource).toContain('@click="handleRepaymentStatusSearch"');
    expect(repaymentsSource).toContain("if (scope === 'keyword')");
    expect(repaymentsSource).toContain('params.phone = filters.phone || undefined;');
    expect(repaymentsSource).toContain("if (scope === 'dueRange')");
    expect(repaymentsSource).toContain('params.due_date_start = filters.dueDateRange[0];');
    expect(repaymentsSource).toContain('params.due_date_end = filters.dueDateRange[1];');
    expect(repaymentsSource).toContain("if (scope === 'actualRepayment')");
    expect(repaymentsSource).toContain('params.actual_repayment_start = filters.actualRepaymentRange[0];');
    expect(repaymentsSource).toContain('params.actual_repayment_end = filters.actualRepaymentRange[1];');
    expect(repaymentsSource).toContain("if (scope === 'repaymentStatus')");
    expect(repaymentsSource).toContain('params.repayment_status = filters.repaymentStatus;');
    expect(repaymentsSource).not.toContain('phone: filters.phone || undefined,');
  });

  it('should render repayment status filter options on repayments page', () => {
    expect(repaymentsSource).toContain('label="还款状态"');
    expect(repaymentsSource).toContain('repaymentStatusOptions');
    expect(repaymentsSource).toContain("label: '未到期', value: 'NOT_DUE'");
    expect(repaymentsSource).toContain("label: '今日到期', value: 'DUE_TODAY'");
    expect(repaymentsSource).toContain("label: '已逾期', value: 'OVERDUE'");
    expect(repaymentsSource).toContain("label: '待支付', value: 'UNPAID'");
    expect(repaymentsSource).toContain("label: '部分支付', value: 'PARTIAL_PAID'");
    expect(repaymentsSource).toContain("label: '已结清', value: 'SETTLED'");
  });

  it('should show and filter due time and actual repayment time on all repayment-related pages', () => {
    for (const source of [repaymentsSource, collectionsSource, financialSource]) {
      expect(source).toContain('label="应还款时间"');
      expect(source).toContain('label="实际还款时间"');
      expect(source).toContain('params.due_date_start');
      expect(source).toContain('params.due_date_end');
      expect(source).toContain('params.actual_repayment_start');
      expect(source).toContain('params.actual_repayment_end');
      expect(source).toContain('row.actual_repayment_date');
    }
  });
});
