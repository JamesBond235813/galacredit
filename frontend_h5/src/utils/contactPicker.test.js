import { describe, expect, it, vi } from 'vitest';
import {
  formatGhanaContactLocalPhone,
  isContactPickerSupported,
  normalizeGhanaContactPhone,
  selectSingleContact
} from './contactPicker';

describe('contact picker', () => {
  it('normalizes Ghana local and international phone numbers', () => {
    expect(normalizeGhanaContactPhone('024 000 0001')).toBe('233240000001');
    expect(normalizeGhanaContactPhone('+233 24 000 0001')).toBe('233240000001');
    expect(normalizeGhanaContactPhone('241234567')).toBe('233241234567');
    expect(normalizeGhanaContactPhone('591234567')).toBe('233591234567');
    expect(normalizeGhanaContactPhone('020123')).toBe('');
  });

  it('formats Ghana phone numbers as 9-digit local display values', () => {
    expect(formatGhanaContactLocalPhone('233240000001')).toBe('240000001');
    expect(formatGhanaContactLocalPhone('024 000 0001')).toBe('240000001');
    expect(formatGhanaContactLocalPhone('020123')).toBe('');
  });

  it('selects one named Ghana contact from the address book', async () => {
    const select = vi.fn().mockResolvedValue([{ name: ['Ama Mensah'], tel: ['+233 24 000 0001'] }]);
    const navigatorObject = { contacts: { select } };

    await expect(selectSingleContact(navigatorObject)).resolves.toEqual({
      name: 'Ama Mensah',
      phone: '233240000001'
    });
    expect(select).toHaveBeenCalledWith(['name', 'tel'], { multiple: false });
  });

  it('does not offer manual entry when the contact picker is unavailable', async () => {
    expect(isContactPickerSupported({})).toBe(false);
    await expect(selectSingleContact({})).rejects.toThrow('Contact selection is not supported');
  });
});
