export const GHANA_COUNTRY_CODE = '233';
export const GHANA_PHONE_DIGITS = 9;
export const TEST_PHONE_DIGITS = 7;

export const normalizePhone = (value) => String(value || '').replace(/\D/g, '').slice(0, GHANA_PHONE_DIGITS);

export const isValidPhone = (value) => {
  const normalized = normalizePhone(value);
  return new RegExp(`^\\d{${GHANA_PHONE_DIGITS}}$`).test(normalized) || new RegExp(`^\\d{${TEST_PHONE_DIGITS}}$`).test(normalized);
};

export const toGhanaPhone = (value) => {
  const normalized = normalizePhone(value);
  if (/^\d{7}$/.test(normalized)) {
    return `${GHANA_COUNTRY_CODE}${normalized.padStart(GHANA_PHONE_DIGITS, '0')}`;
  }
  return /^\d{9}$/.test(normalized) ? `${GHANA_COUNTRY_CODE}${normalized}` : '';
};

export const isValidPassword = (value) => String(value || '').length >= 6;
