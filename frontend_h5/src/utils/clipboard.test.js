import { describe, expect, it, vi } from 'vitest';

import { copyTextSafely } from './clipboard';

describe('copyTextSafely', () => {
  it('should fallback to textarea copy when clipboard api rejects', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('not allowed'));
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText }
    });
    const execCommand = vi.fn().mockReturnValue(true);
    Object.defineProperty(document, 'execCommand', {
      configurable: true,
      value: execCommand
    });

    const result = await copyTextSafely('CARD_SECRET_VALUE');

    expect(result).toBe(true);
    expect(writeText).toHaveBeenCalledWith('CARD_SECRET_VALUE');
    expect(execCommand).toHaveBeenCalledWith('copy');

    delete document.execCommand;
  });
});
