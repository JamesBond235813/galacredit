import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const currentDir = dirname(fileURLToPath(import.meta.url));
const riskDialogSource = readFileSync(resolve(currentDir, 'RiskReportDialog.vue'), 'utf-8');

describe('xiaohebao risk report dialog', () => {
  it('should show the merged report and hide panorama credit detail section', () => {
    expect(riskDialogSource).toContain('小荷包风险报告');
    expect(riskDialogSource).toContain('探针C信息');
    expect(riskDialogSource).toContain('payload.value?.panorama?.payload');
    expect(riskDialogSource).toContain('payload.value?.probe_c');
    expect(riskDialogSource).not.toContain('信用详情');
    expect(riskDialogSource).not.toContain('current_report_detail');
  });
});
