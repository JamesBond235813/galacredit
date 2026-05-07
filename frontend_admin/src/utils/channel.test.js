import { describe, expect, it } from 'vitest';

import { CHANNEL_INVITE_CODE_LENGTH, generateChannelInviteCode } from './channel';

describe('channel utils', () => {
  it('should generate invite code with default length and charset', () => {
    const code = generateChannelInviteCode();
    expect(code).toHaveLength(CHANNEL_INVITE_CODE_LENGTH);
    expect(code).toMatch(/^[a-z0-9]{16}$/);
    expect(code).toMatch(/[a-z]/);
    expect(code).toMatch(/\d/);
  });

  it('should generate invite code with custom length', () => {
    const code = generateChannelInviteCode(20);
    expect(code).toHaveLength(20);
    expect(code).toMatch(/^[a-z0-9]{20}$/);
    expect(code).toMatch(/[a-z]/);
    expect(code).toMatch(/\d/);
  });
});
