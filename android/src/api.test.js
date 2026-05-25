import { afterEach, describe, expect, it, vi } from 'vitest';

import { api, buildRequestUrl } from './api.js';

afterEach(() => {
  vi.restoreAllMocks();
  delete global.fetch;
  delete global.localStorage;
  delete global.window;
});

describe('mobile console api url builder', () => {
  it('keeps relative api paths for local proxy mode', () => {
    expect(buildRequestUrl('/admin/users', { skip: 0, limit: 20 }, '/api', 'http://localhost:2004')).toBe('/api/admin/users?skip=0&limit=20');
  });

  it('keeps absolute backend origins for packaged android app mode', () => {
    expect(buildRequestUrl('/admin/users', { keyword: '188' }, 'https://api.example.com/api', 'http://localhost:2004')).toBe(
      'https://api.example.com/api/admin/users?keyword=188',
    );
  });

  it('marks admin login as mobile client', async () => {
    const setItem = vi.fn();
    global.localStorage = {
      getItem: vi.fn(() => ''),
      setItem,
      removeItem: vi.fn(),
    };
    global.window = { location: { origin: 'http://localhost:2003' } };
    global.fetch = vi.fn(async () => ({
      ok: true,
      text: async () => JSON.stringify({ access_token: 'token-1' }),
    }));

    await api.login('xiaojiang', 'secret');

    const [, requestOptions] = global.fetch.mock.calls[0];
    expect(JSON.parse(requestOptions.body)).toEqual({
      username: 'xiaojiang',
      password: 'secret',
      client_type: 'MOBILE',
    });
    expect(setItem).toHaveBeenCalledWith('xhb_android_admin_token', 'token-1');
  });
});
