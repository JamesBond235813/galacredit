import { describe, expect, it } from 'vitest';

import { buildEcardDisplayItems, buildEcardSecretParams, formatMaskedEcardValue } from './ecardDisplay';

describe('ecardDisplay', () => {
  it('should normalize multi ecard items for display', () => {
    const items = buildEcardDisplayItems({
      ecard_items: [
        { id: 57, index: 0, face_value: 500, account_masked: 'JDEZ********1336', password_masked: 'abcd****efgh' },
        { id: 58, index: 1, face_value: 1000, account_masked: 'JDTZ********4491', password_masked: '1234****5678' }
      ]
    });

    expect(items).toHaveLength(2);
    expect(items[0]).toMatchObject({ id: 57, index: 0, title: 'Legacy E-card 1', faceValue: 500 });
    expect(items[1]).toMatchObject({ id: 58, index: 1, title: 'Legacy E-card 2', faceValue: 1000 });
  });

  it('should fallback to legacy masked fields', () => {
    const items = buildEcardDisplayItems({
      ecard_face_value: 500,
      ecard_account_masked: 'JDEZ********1336',
      ecard_password_masked: 'abcd****efgh',
      ecard_expires_at: '2028-01-16T00:00:00'
    });

    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({ key: 'ecard-legacy', id: null, index: 0, faceValue: 500 });
  });

  it('should build precise secret query params', () => {
    expect(buildEcardSecretParams({ id: 57, index: 0 })).toEqual({ item_id: 57 });
    expect(buildEcardSecretParams({ index: 1 })).toEqual({ index: 1 });
  });

  it('should keep masked value readable', () => {
    expect(formatMaskedEcardValue('JDEZ********1336')).toBe('JDEZ-****-****-****-1336');
    expect(formatMaskedEcardValue('')).toBe('--');
  });
});
