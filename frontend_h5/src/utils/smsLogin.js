export const SMS_COOLDOWN_SECONDS = 60;

export const normalizeSmsCode = (value) => value.replace(/\D/g, '').slice(0, 6);

export const isValidSmsCode = (value) => /^\d{6}$/.test(value);

export const getSmsButtonText = (loading, cooldownSeconds) => {
  if (loading) {
    return '发送中...';
  }
  if (cooldownSeconds > 0) {
    return `${cooldownSeconds}s后重试`;
  }
  return '发送验证码';
};
