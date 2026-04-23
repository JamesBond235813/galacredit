import { submitUserLocation } from '../api';

const GEO_TIMEOUT = 12000;

const getCurrentPosition = () =>
  new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('GEO_UNSUPPORTED'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: GEO_TIMEOUT,
      maximumAge: 30000
    });
  });

export const captureAndUploadLocation = async () => {
  const position = await getCurrentPosition();
  const payload = {
    latitude: Number(position.coords.latitude),
    longitude: Number(position.coords.longitude),
    accuracy: Number(position.coords.accuracy || 0),
    source: 'h5-geolocation'
  };
  await submitUserLocation(payload);
  return payload;
};
