import { describe, expect, it } from 'vitest';

import { buildPermissionsFromRoles } from './adminPages';

describe('adminPages role permission mapping', () => {
  it('should map BUSINESS_CONSULTANT to users page only', () => {
    expect(buildPermissionsFromRoles(['BUSINESS_CONSULTANT'])).toEqual(['users']);
  });

  it('should merge BUSINESS_CONSULTANT with other roles', () => {
    expect(buildPermissionsFromRoles(['BUSINESS_CONSULTANT', 'COLLECTION'])).toEqual(['users', 'collections']);
  });
});
