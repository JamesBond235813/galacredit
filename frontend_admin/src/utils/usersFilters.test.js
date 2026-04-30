import { describe, expect, it } from 'vitest';
import { buildUsersQueryParams } from './usersFilters';

describe('buildUsersQueryParams', () => {
  it('should include deal time range for business consultant', () => {
    const payload = buildUsersQueryParams(
      {
        keyword: '138',
        page: 2,
        size: 10,
        dealDateRange: ['2026-04-01', '2026-04-30']
      },
      true
    );

    expect(payload).toEqual({
      keyword: '138',
      skip: 10,
      limit: 10,
      deal_time_start: '2026-04-01',
      deal_time_end: '2026-04-30'
    });
  });

  it('should omit deal time range for non consultant', () => {
    const payload = buildUsersQueryParams(
      {
        keyword: '',
        page: 1,
        size: 20,
        dealDateRange: ['2026-04-01', '2026-04-30']
      },
      false
    );

    expect(payload).toEqual({
      keyword: undefined,
      skip: 0,
      limit: 20
    });
  });
});
