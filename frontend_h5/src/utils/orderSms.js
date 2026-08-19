export const isOrderSmsCodeValid = (value) => /^\d{6}$/.test(String(value || ''));

export const getOrderSmsResendText = (sending, cooldownSeconds) => {
  if (sending) {
    return 'Sending...';
  }
  if (Number(cooldownSeconds || 0) > 0) {
    return `Retry in ${Number(cooldownSeconds)}s`;
  }
  return 'Resend code';
};

export const isOrderSmsResendDisabled = (sending, cooldownSeconds) =>
  Boolean(sending || Number(cooldownSeconds || 0) > 0);
