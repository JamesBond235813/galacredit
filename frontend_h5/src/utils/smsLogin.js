export const SMS_COOLDOWN_SECONDS = 60;

export const normalizeSmsCode = (value) => value.replace(/\D/g, '').slice(0, 6);

export const isValidSmsCode = (value) => /^\d{6}$/.test(value);

export const getSmsButtonText = (loading, cooldownSeconds) => {
  if (loading) {
    return 'Sending...';
  }
  if (cooldownSeconds > 0) {
    return `Retry in ${cooldownSeconds}s`;
  }
  return 'Send code';
};
