import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const currentDir = dirname(fileURLToPath(import.meta.url));
const repaymentsSource = readFileSync(resolve(currentDir, 'Repayments.vue'), 'utf-8');

describe('repayments bill progress display', () => {
  it('should only render settled tag for settled loans', () => {
    expect(repaymentsSource).toContain('v-if="isLoanSettled(row)"');
    expect(repaymentsSource).toContain('<template v-else>');
    expect(repaymentsSource).toContain("row?.status === 'SETTLED'");
  });
});
