import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(currentDirectory, 'Login.vue'), 'utf8');

describe('GalaCredit login layout', () => {
  it('places the brand identity before the login form', () => {
    const brandPosition = source.indexOf('class="logo-box brand-header"');
    const formPosition = source.indexOf('class="login-main"');

    expect(brandPosition).toBeGreaterThan(-1);
    expect(formPosition).toBeGreaterThan(brandPosition);
    expect(source).not.toContain('brand-footer');
  });

  it('keeps the Ghana phone prefix and nine-digit counter', () => {
    expect(source).toContain('<span>+233</span>');
    expect(source).toContain('{{ phone.length }}/9');
    expect(source).toContain("phone[index - 1] || '0'");
  });
});
