import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(currentDirectory, 'Login.vue'), 'utf8');
const logoSource = fs.readFileSync(path.join(currentDirectory, '../assets/logo.svg'), 'utf8');

describe('GalaCredit login layout', () => {
  it('renders a softened brand header above the form', () => {
    expect(source).toContain('class="brand-header"');
    expect(source).toContain('class="brand-mark"');
    expect(source).toContain('class="brand-copy"');
    expect(source).toContain('rgba(238, 246, 255, 0.22)');
    expect(source).toContain('GalaCredit');
    expect(source).toContain('Credit when it matters');
    expect(source).not.toContain('background: rgba(8, 34, 76, 0.28)');
    expect(source).not.toContain('Secure sign in for your account');
    expect(logoSource).toContain('fill="#ea9518"');
  });

  it('uses a compact single-line agreement consent and in-page policy reader', () => {
    expect(source).toContain("I agree to GalaCredit's");
    expect(source).toContain('Personal Data Authorization');
    expect(source).toContain('policyVisible');
    expect(source).toContain('openLegalPage');
    expect(source).not.toContain('Before you continue');
    expect(source).not.toContain('Permission Statement');
  });

  it('keeps captcha validation and keyboard handling intact', () => {
    expect(source).toContain('window.visualViewport');
    expect(source).toContain('verifySliderCaptcha');
    expect(source).toContain('updateKeyboardOffset');
    expect(source).toContain('--keyboard-offset');
  });
});
