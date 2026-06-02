import QRCode from 'qrcode';

const QR_OPTIONS = {
  errorCorrectionLevel: 'H',
  margin: 2,
  width: 260,
  color: {
    dark: '#16355f',
    light: '#ffffff'
  }
};

export const renderChannelQr = (canvas, text) => QRCode.toCanvas(canvas, text, QR_OPTIONS);
