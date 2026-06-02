import { describe, expect, it } from 'vitest';

import { isValidPassword, isValidPhone, normalizePhone } from './passwordAuth';

describe('passwordAuth utils', () => {
  it('should normalize phone to 11 digits', () => {
    expect(normalizePhone('138-0000 12345')).toBe('13800001234');
  });

  it('should validate 11-digit phone only', () => {
    expect(isValidPhone('13800001234')).toBe(true);
    expect(isValidPhone('1380000123')).toBe(false);
  });

  it('should validate password length', () => {
    expect(isValidPassword('123456')).toBe(true);
    expect(isValidPassword('12345')).toBe(false);
  });
});
