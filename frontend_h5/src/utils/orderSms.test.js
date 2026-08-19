import { describe, expect, it } from 'vitest';

import { getOrderSmsResendText, isOrderSmsCodeValid, isOrderSmsResendDisabled } from './orderSms';

describe('order sms utils', () => {
  it('validates 6 digit sms code', () => {
    expect(isOrderSmsCodeValid('123456')).toBe(true);
    expect(isOrderSmsCodeValid('12345')).toBe(false);
    expect(isOrderSmsCodeValid('1234ab')).toBe(false);
  });

  it('formats resend button text', () => {
    expect(getOrderSmsResendText(true, 0)).toBe('Sending...');
    expect(getOrderSmsResendText(false, 59)).toBe('Retry in 59s');
    expect(getOrderSmsResendText(false, 0)).toBe('Resend code');
  });

  it('controls resend button disabled state', () => {
    expect(isOrderSmsResendDisabled(true, 0)).toBe(true);
    expect(isOrderSmsResendDisabled(false, 5)).toBe(true);
    expect(isOrderSmsResendDisabled(false, 0)).toBe(false);
  });
});
