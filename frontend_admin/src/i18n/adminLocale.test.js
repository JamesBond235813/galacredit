import { beforeEach, describe, expect, it } from 'vitest';
import { adminLocale, setAdminLocale, t, tr, translateText } from './adminLocale';

describe('admin locale', () => {
  beforeEach(() => {
    const storage = new Map();
    globalThis.window = {
      localStorage: {
        clear: () => storage.clear(),
        getItem: (key) => storage.get(key) || null,
        setItem: (key, value) => storage.set(key, String(value))
      },
      dispatchEvent: () => {},
      setTimeout: () => {}
    };
    setAdminLocale('zh-CN');
  });

  it('falls back to Chinese and switches translations', () => {
    expect(t('products')).toBe('贷款产品');
    setAdminLocale('en-GH');
    expect(adminLocale.value).toBe('en-GH');
    expect(t('products')).toBe('Loan Products');
    expect(tr('放款', 'Disbursement')).toBe('Disbursement');
  });

  it('persists the selected locale locally', () => {
    setAdminLocale('en-GH');
    expect(window.localStorage.getItem('galacredit_admin_locale')).toBe('en-GH');
  });

  it('translates only complete UI labels and never creates mixed-language business text', () => {
    setAdminLocale('en-GH');
    expect(translateText('上传名单')).toBe('Upload blacklist');
    expect(translateText('  上传名单  ')).toBe('  Upload blacklist  ');
    expect(translateText('客户备注：上传名单后继续处理')).toBe('客户备注：上传名单后继续处理');
    expect(translateText('燕子')).toBe('燕子');
  });
});
