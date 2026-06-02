export const isOrderSmsCodeValid = (value) => /^\d{6}$/.test(String(value || ''));

export const getOrderSmsResendText = (sending, cooldownSeconds) => {
  if (sending) {
    return '发送中...';
  }
  if (Number(cooldownSeconds || 0) > 0) {
    return `${Number(cooldownSeconds)}s后重试`;
  }
  return '重新发送验证码';
};

export const isOrderSmsResendDisabled = (sending, cooldownSeconds) =>
  Boolean(sending || Number(cooldownSeconds || 0) > 0);
