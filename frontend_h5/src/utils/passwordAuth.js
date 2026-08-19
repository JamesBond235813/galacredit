export const GHANA_COUNTRY_CODE = '233';
export const GHANA_PHONE_DIGITS = 9;

export const normalizePhone = (value) => String(value || '').replace(/\D/g, '').slice(0, GHANA_PHONE_DIGITS);

export const isValidPhone = (value) => new RegExp(`^\\d{${GHANA_PHONE_DIGITS}}$`).test(String(value || ''));

export const toGhanaPhone = (value) => {
  const normalized = normalizePhone(value);
  return isValidPhone(normalized) ? `${GHANA_COUNTRY_CODE}${normalized}` : '';
};

export const isValidPassword = (value) => String(value || '').length >= 6;
