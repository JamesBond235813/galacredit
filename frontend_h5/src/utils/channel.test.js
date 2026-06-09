import { beforeEach, describe, expect, it } from 'vitest';

import { clearEntryChannel, getEntryInviteCode, isValidInviteCode, saveEntryInviteCode } from './channel';

describe('channel invite code utils', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should validate invite code format', () => {
    expect(isValidInviteCode('abcd1234abcd5678')).toBe(true);
    expect(isValidInviteCode('0000049bad855673c404cdfe')).toBe(true);
    expect(isValidInviteCode('abcd1234abcd567_')).toBe(false);
    expect(isValidInviteCode('abc')).toBe(false);
  });

  it('should persist and overwrite invite code', () => {
    saveEntryInviteCode('abcd1234abcd5678');
    expect(getEntryInviteCode()).toBe('abcd1234abcd5678');
    saveEntryInviteCode('0000049bad855673c404cdfe');
    expect(getEntryInviteCode()).toBe('0000049bad855673c404cdfe');
    clearEntryChannel();
    expect(getEntryInviteCode()).toBe('');
  });
});
