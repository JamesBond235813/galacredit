import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const currentDir = dirname(fileURLToPath(import.meta.url));

describe('H5 channel invite link handoff', () => {
  it('keeps invite code in login URL after channel entry succeeds', () => {
    const source = readFileSync(resolve(currentDir, 'assets/ChannelEntry-B4gdj5VD.js'), 'utf-8');

    expect(source).toContain('path:`/login`');
    expect(source).toContain('query:{invite_code:t}');
  });

  it('uses invite code from login URL when submitting sms login', () => {
    const source = readFileSync(resolve(currentDir, 'assets/Login-B0QnKs2G.js'), 'utf-8');

    expect(source).toContain('new URLSearchParams(window.location.search).get(`invite_code`)');
    expect(source).toContain('invite_code:M.value');
  });
});
