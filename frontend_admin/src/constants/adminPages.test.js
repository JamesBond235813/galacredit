import { describe, expect, it } from 'vitest';

import { ADMIN_MENU_GROUPS, ADMIN_PAGE_OPTIONS, buildPermissionsFromRoles } from './adminPages';

describe('adminPages role permission mapping', () => {
  it('should group every page exactly once in the sidebar taxonomy', () => {
    const groupedKeys = ADMIN_MENU_GROUPS.flatMap((group) => group.itemKeys);
    expect(groupedKeys).toHaveLength(ADMIN_PAGE_OPTIONS.length);
    expect(new Set(groupedKeys).size).toBe(ADMIN_PAGE_OPTIONS.length);
    expect(groupedKeys.sort()).toEqual(ADMIN_PAGE_OPTIONS.map((item) => item.key).sort());
  });

  it('should map BUSINESS_CONSULTANT to users and exclusive-links pages', () => {
    expect(buildPermissionsFromRoles(['BUSINESS_CONSULTANT'])).toEqual(['users', 'exclusive-links']);
  });

  it('should merge BUSINESS_CONSULTANT with other roles', () => {
    expect(buildPermissionsFromRoles(['BUSINESS_CONSULTANT', 'COLLECTION'])).toEqual([
      'users',
      'exclusive-links',
      'collections',
      'blacklist',
      'message-center',
      'audit-log'
    ]);
  });

  it('should include operations and ops-prep pages in the navigation taxonomy', () => {
    const keys = ADMIN_PAGE_OPTIONS.map((item) => item.key);
    expect(keys).toEqual(expect.arrayContaining([
      'monitoring',
      'message-center',
      'audit-log',
      'kyc-review',
      'risk-strategy',
      'content-config'
    ]));
  });
});
