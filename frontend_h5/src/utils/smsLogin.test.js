import { describe, expect, it } from 'vitest';

import { getSmsButtonText, isValidSmsCode, normalizeSmsCode } from './smsLogin';

describe('smsLogin utils', () => {
  it('should normalize sms code to 6 digits', () => {
    expect(normalizeSmsCode('12a3-456789')).toBe('123456');
  });

  it('should validate sms code with 6 digits only', () => {
    expect(isValidSmsCode('123456')).toBe(true);
    expect(isValidSmsCode('12345')).toBe(false);
    expect(isValidSmsCode('1234ab')).toBe(false);
  });

  it('should format sms button text', () => {
    expect(getSmsButtonText(true, 0)).toBe('发送中...');
    expect(getSmsButtonText(false, 21)).toBe('21s后重试');
    expect(getSmsButtonText(false, 0)).toBe('发送验证码');
  });
});
