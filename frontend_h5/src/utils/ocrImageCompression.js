export const OCR_IMAGE_COMPRESS_LIMIT = 600 * 1024;
export const OCR_IMAGE_MAX_SIDE = 1280;
export const OCR_IMAGE_QUALITY = 0.72;

export const getOcrImageCompressionPlan = ({ size = 0, width = 0, height = 0 } = {}) => {
  const maxSide = Math.max(Number(width) || 0, Number(height) || 0);
  const shouldCompress = Number(size) > OCR_IMAGE_COMPRESS_LIMIT || maxSide > OCR_IMAGE_MAX_SIDE;
  const scale = maxSide > 0 ? Math.min(1, OCR_IMAGE_MAX_SIDE / maxSide) : 1;

  return {
    shouldCompress,
    scale,
    quality: OCR_IMAGE_QUALITY
  };
};
