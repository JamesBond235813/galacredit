import { describe, expect, it } from 'vitest';

import { getDealColumnConfig } from './usersDealColumns';

describe('getDealColumnConfig', () => {
  it('should return consultant deal columns', () => {
    expect(getDealColumnConfig(true)).toEqual({
      timeLabel: '成交时间',
      amountLabel: '成交金额',
      timeKey: 'first_disbursed_at',
      amountKey: 'first_deal_amount'
    });
  });

  it('should return non-consultant deal columns', () => {
    expect(getDealColumnConfig(false)).toEqual({
      timeLabel: '最近成交时间',
      amountLabel: '最近成交金额',
      timeKey: 'latest_disbursed_at',
      amountKey: 'latest_deal_amount'
    });
  });
});
