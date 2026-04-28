import { beforeEach, describe, expect, it, vi } from 'vitest';

const requestUseHandlers = [];
const responseUseHandlers = [];
const requestInstance = {
  interceptors: {
    request: {
      use: (onFulfilled, onRejected) => {
        requestUseHandlers.push({ onFulfilled, onRejected });
      },
    },
    response: {
      use: (onFulfilled, onRejected) => {
        responseUseHandlers.push({ onFulfilled, onRejected });
      },
    },
  },
};

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => requestInstance),
  },
}));

vi.mock('vant', () => ({
  showToast: vi.fn(),
}));

describe('api request client-id header', () => {
  beforeEach(() => {
    requestUseHandlers.length = 0;
    responseUseHandlers.length = 0;
    localStorage.clear();
    vi.resetModules();
  });

  it('adds configured client-id for every request', async () => {
    const requestModule = await import('./request');
    expect(requestModule.default).toBe(requestInstance);
    expect(requestUseHandlers.length).toBeGreaterThan(0);

    const config = await requestUseHandlers[0].onFulfilled({});
    expect(config.headers['client-id']).toBe('h5-web');
  });

  it('keeps auth header and client-id together', async () => {
    localStorage.setItem('token', 'token-abc');

    await import('./request');
    const config = await requestUseHandlers[0].onFulfilled({});

    expect(config.headers['client-id']).toBe('h5-web');
    expect(config.headers.Authorization).toBe('Bearer token-abc');
  });
});
