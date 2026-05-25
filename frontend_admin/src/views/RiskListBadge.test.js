import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const currentDir = dirname(fileURLToPath(import.meta.url));
const applicationsSource = readFileSync(resolve(currentDir, 'Applications.vue'), 'utf-8');
const disbursementsSource = readFileSync(resolve(currentDir, 'Disbursements.vue'), 'utf-8');

describe('risk list badge display', () => {
  it('should show red risk badge on application and disbursement pages', () => {
    expect(applicationsSource).toContain('row.user_risk_list_hit');
    expect(applicationsSource).toContain('risk-list-badge');
    expect(applicationsSource).toContain('风');
    expect(disbursementsSource).toContain('row.user_risk_list_hit');
    expect(disbursementsSource).toContain('risk-list-badge');
    expect(disbursementsSource).toContain('风');
  });
});
