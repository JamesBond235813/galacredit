import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(currentDirectory, 'OCR.vue'), 'utf8');

describe('Ghana Card verification page', () => {
  it('uses the localized Ghana Card front-upload flow', () => {
    expect(source).toContain('Front of your');
    expect(source).toContain('Ghana Card');
    expect(source).toContain('Photos that would be rejected');
    expect(source).toContain(':disabled="!frontFile || !agreed"');
    expect(source).not.toContain('Upload ID Back');
  });

  it('keeps the existing OCR request field for backend compatibility', () => {
    expect(source).toContain("formData.append('front_image', frontFile.value)");
    expect(source).toContain('Ghana Card No.');
  });
});
