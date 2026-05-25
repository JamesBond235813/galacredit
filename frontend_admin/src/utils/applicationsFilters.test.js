import { describe, expect, it } from 'vitest';

import { buildApplicationsQueryParams } from './applicationsFilters';

describe('buildApplicationsQueryParams', () => {
  it('should use reviewing status by default', () => {
    const payload = buildApplicationsQueryParams(
      { phone: '', status: 'REVIEWING', reviewAdminId: '', relendFilter: 'ALL', page: 1, size: 10 },
      true
    );

    expect(payload).toEqual({
      scope: 'REVIEWING',
      phone: undefined,
      status: 'REVIEWING',
      review_admin_id: undefined,
      skip: 0,
      limit: 10
    });
  });

  it('should include reviewer and exact relend count for super admin', () => {
    const payload = buildApplicationsQueryParams(
      { phone: '138', status: 'ALL', reviewAdminId: 7, relendFilter: '2', page: 2, size: 20 },
      true
    );

    expect(payload).toEqual({
      scope: 'REVIEWING',
      phone: '138',
      status: undefined,
      review_admin_id: 7,
      relend_count: 2,
      skip: 20,
      limit: 20
    });
  });

  it('should include relend min count for three plus option', () => {
    const payload = buildApplicationsQueryParams(
      { phone: '', status: 'REVIEWING', reviewAdminId: 7, relendFilter: '3_PLUS', page: 1, size: 10 },
      false
    );

    expect(payload.review_admin_id).toBeUndefined();
    expect(payload.relend_min_count).toBe(3);
  });
});
