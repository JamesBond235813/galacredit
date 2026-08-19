import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(currentDirectory, '..', '..');

const collectFiles = (directory) => {
  const entries = fs.readdirSync(directory, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      return collectFiles(entryPath);
    }
    return /\.(vue|js|txt)$/.test(entry.name) ? [entryPath] : [];
  });
};

describe('H5 English content', () => {
  it('does not contain Chinese characters in customer-facing source and public text', () => {
    const files = [
      ...collectFiles(path.join(projectRoot, 'src')),
      ...collectFiles(path.join(projectRoot, 'public'))
    ];
    const chinesePattern = /[\u3400-\u9fff]/u;
    const violations = files.filter((filePath) => chinesePattern.test(fs.readFileSync(filePath, 'utf8')));
    expect(violations).toEqual([]);
  });
});
