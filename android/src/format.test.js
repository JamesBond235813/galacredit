import { describe, expect, it } from 'vitest';

import { compactPhone, formatCurrency, getPaymentSummary, getRiskSummary, getRiskTags, getRoleLabels, getStatusText, resolveUserId } from './format.js';

describe('mobile console format helpers', () => {
  it('formats money with Chinese separators', () => {
    expect(formatCurrency(1600)).toBe('¥1,600');
    expect(formatCurrency(12.5)).toBe('¥12.50');
  });

  it('compacts 11-digit phone numbers for mobile cards', () => {
    expect(compactPhone('18800130712')).toBe('188 0013 0712');
  });

  it('maps backend loan status to Chinese label', () => {
    expect(getStatusText('WITHDRAWING')).toBe('待发卡');
  });

  it('builds risk tags from backend loan fields', () => {
    const tags = getRiskTags({
      user_blacklist_hit: true,
      user_risk_list_hit: true,
      user_location_risk_hit: true,
    });
    expect(tags.map((item) => item.label)).toEqual(['风险区域', '风险名单', '黑名单']);
    expect(getRiskSummary({ user_risk_list_hit: true })).toBe('风险名单');
  });

  it('summarizes repayment progress for compact mobile cards', () => {
    expect(getPaymentSummary({ total_repayment_amount: 1600, remaining_repayment_amount: 600 })).toBe('¥1,000 / ¥1,600');
  });

  it('resolves ids across user and loan rows', () => {
    expect(resolveUserId({ user_id: 8, id: 9 })).toBe(8);
    expect(resolveUserId({ id: 9 })).toBe(9);
  });

  it('formats admin roles for the compact header', () => {
    expect(getRoleLabels({ roles: ['ADMIN', 'FINANCE'] })).toEqual(['超管', '财务']);
  });
});
