export const normalizePhone = (value) => String(value || '').replace(/\D/g, '').slice(0, 11);

export const isValidPhone = (value) => /^\d{11}$/.test(String(value || ''));

export const isValidPassword = (value) => String(value || '').length >= 6;
