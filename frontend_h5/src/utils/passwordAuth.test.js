import { describe, expect, it } from 'vitest';

import { isValidPassword, isValidPhone, normalizePhone, toGhanaPhone } from './passwordAuth';

describe('passwordAuth utils', () => {
  it('should normalize phone to 9 local digits', () => {
    expect(normalizePhone('24-000 0001')).toBe('240000001');
  });

  it('should validate 9-digit Ghana local phone only', () => {
    expect(isValidPhone('240000001')).toBe(true);
    expect(isValidPhone('1234567')).toBe(true);
    expect(isValidPhone('24000001')).toBe(false);
  });

  it('should add the Ghana country code for API requests', () => {
    expect(toGhanaPhone('240000001')).toBe('233240000001');
    expect(toGhanaPhone('1234567')).toBe('233001234567');
    expect(toGhanaPhone('24000001')).toBe('');
  });

  it('should validate password length', () => {
    expect(isValidPassword('123456')).toBe(true);
    expect(isValidPassword('12345')).toBe(false);
  });
});
