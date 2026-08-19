import { submitUserLocation } from '../api';

const GEO_TIMEOUT = 4000;
const GEO_PROMPT_TIMEOUT = 5000;

export const getLocationErrorMessage = (error) => {
  if (error?.message === 'GEO_INSECURE_CONTEXT') {
    return 'Location access requires a secure HTTPS connection. Please use the secure site and try again.';
  }
  if (error?.message === 'GEO_PROMPT_TIMEOUT') {
    return 'The location request did not respond. Check the site certificate and allow location access in your browser settings.';
  }
  if (error?.message === 'GEO_UNSUPPORTED') {
    return 'This browser does not support location services. Please try another browser.';
  }
  if (error?.code === 1) {
    return 'Enable location permission in your phone or browser settings, then try again.';
  }
  if (error?.code === 2) {
    return 'Your location is unavailable. Make sure location services are enabled.';
  }
  if (error?.code === 3) {
    return 'The location request timed out. Enable location services and try again.';
  }
  return error?.response?.data?.msg || error?.response?.data?.detail || error?.message || 'Your location is currently unavailable.';
};

const getCurrentPosition = () =>
  new Promise((resolve, reject) => {
    let settled = false;
    const promptTimer = window.setTimeout(() => {
      if (!settled) {
        settled = true;
        reject(new Error('GEO_PROMPT_TIMEOUT'));
      }
    }, GEO_PROMPT_TIMEOUT);
    const finish = (callback, value) => {
      if (settled) {
        return;
      }
      settled = true;
      window.clearTimeout(promptTimer);
      callback(value);
    };
    if (!window.isSecureContext && !['localhost', '127.0.0.1'].includes(window.location.hostname)) {
      finish(reject, new Error('GEO_INSECURE_CONTEXT'));
      return;
    }
    if (!navigator.geolocation) {
      finish(reject, new Error('GEO_UNSUPPORTED'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => finish(resolve, position),
      (error) => finish(reject, error),
      {
        enableHighAccuracy: false,
        timeout: GEO_TIMEOUT,
        maximumAge: 300000
      }
    );
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
