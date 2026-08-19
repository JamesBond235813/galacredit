import { describe, expect, it } from 'vitest';
import { formatCurrency, formatPhone, getStatusText } from './format';

describe('Ghana admin formatting', () => {
  it('formats GHS amounts and Ghana phone numbers', () => {
    expect(formatCurrency(1000)).toContain('GHS');
    expect(formatPhone('233240000001')).toBe('+233 24 0000001');
  });

  it('localizes loan status text', () => {
    expect(getStatusText('WITHDRAWING')).toBeTruthy();
  });
});
