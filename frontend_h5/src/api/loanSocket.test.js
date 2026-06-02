import { beforeEach, describe, expect, it, vi } from 'vitest';

import { createLoanSnapshotSubscriber } from './loanSocket';

let instances = [];

class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = 0;
    this.onmessage = null;
    this.onerror = null;
    this.onclose = null;
    instances.push(this);
  }

  close() {
    if (typeof this.onclose === 'function') {
      this.onclose({ code: 1000 });
    }
  }
}

describe('createLoanSnapshotSubscriber', () => {
  beforeEach(() => {
    instances = [];
    localStorage.clear();
    localStorage.setItem('token', 'token-abc');
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  it('should receive loan snapshot payload from websocket message', () => {
    const onSnapshot = vi.fn();
    const subscriber = createLoanSnapshotSubscriber({ onSnapshot });

    subscriber.start();

    expect(instances.length).toBe(1);
    expect(instances[0].url).toContain('/api/loan/ws/status?token=token-abc');

    instances[0].onmessage({
      data: JSON.stringify({
        type: 'loan_snapshot',
        data: { status: 'APPROVED', credit_limit: 8000 },
      }),
    });

    expect(onSnapshot).toHaveBeenCalledWith({ status: 'APPROVED', credit_limit: 8000 });
    subscriber.stop();
  });

  it('should stop reconnecting and clear token when auth failed with 1008', () => {
    vi.useFakeTimers();
    const onAuthFailed = vi.fn();
    const subscriber = createLoanSnapshotSubscriber({ onAuthFailed });

    subscriber.start();
    expect(instances.length).toBe(1);

    instances[0].onclose({ code: 1008 });
    vi.runAllTimers();

    expect(onAuthFailed).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('token')).toBeNull();
    expect(instances.length).toBe(1);
    vi.useRealTimers();
  });
});
