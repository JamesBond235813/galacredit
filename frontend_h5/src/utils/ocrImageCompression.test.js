import { describe, expect, it } from 'vitest';
import {
  OCR_IMAGE_MAX_SIDE,
  getOcrImageCompressionPlan
} from './ocrImageCompression';

describe('ocr image compression plan', () => {
  it('compresses medium identity images to reduce OCR timeout risk', () => {
    const plan = getOcrImageCompressionPlan({
      size: 1.1 * 1024 * 1024,
      width: 1500,
      height: 950
    });

    expect(plan.shouldCompress).toBe(true);
    expect(plan.scale).toBeCloseTo(OCR_IMAGE_MAX_SIDE / 1500);
    expect(plan.quality).toBeLessThan(0.8);
  });

  it('keeps small images unchanged', () => {
    const plan = getOcrImageCompressionPlan({
      size: 240 * 1024,
      width: 900,
      height: 580
    });

    expect(plan.shouldCompress).toBe(false);
    expect(plan.scale).toBe(1);
  });
});
