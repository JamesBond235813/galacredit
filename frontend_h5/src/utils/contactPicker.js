const GHANA_LOCAL_PHONE_PATTERN = /^0\d{9}$/;
const GHANA_SHORT_LOCAL_PHONE_PATTERN = /^\d{9}$/;
const GHANA_INTERNATIONAL_PHONE_PATTERN = /^233\d{9}$/;

export const normalizeGhanaContactPhone = (value) => {
  const digits = String(value || '').replace(/\D/g, '');
  if (GHANA_INTERNATIONAL_PHONE_PATTERN.test(digits)) {
    return digits;
  }
  if (GHANA_LOCAL_PHONE_PATTERN.test(digits)) {
    return `233${digits.slice(1)}`;
  }
  if (GHANA_SHORT_LOCAL_PHONE_PATTERN.test(digits)) {
    return `233${digits}`;
  }
  return '';
};

/**
 * Convert a normalized Ghana international phone number to a 9-digit local display value.
 *
 * :param value: Normalized phone number
 * :return: 9-digit local phone number
 */
export const formatGhanaContactLocalPhone = (value) => {
  const normalized = normalizeGhanaContactPhone(value);
  return normalized ? normalized.replace(/^233/, '') : '';
};

export const isContactPickerSupported = (navigatorObject = globalThis.navigator) =>
  typeof navigatorObject?.contacts?.select === 'function';

export const selectSingleContact = async (navigatorObject = globalThis.navigator) => {
  if (!isContactPickerSupported(navigatorObject)) {
    throw new Error('Contact selection is not supported on this device. Please use the GalaCredit app or a supported mobile browser.');
  }

  const selected = await navigatorObject.contacts.select(['name', 'tel'], { multiple: false });
  const contact = selected?.[0];
  if (!contact) {
    return null;
  }

  const name = String(contact.name?.[0] || '').trim();
  const phone = (contact.tel || []).map(normalizeGhanaContactPhone).find(Boolean) || '';
  if (!name || !phone) {
    throw new Error('Select a contact with a name and a valid Ghana mobile number.');
  }
  return { name, phone };
};
