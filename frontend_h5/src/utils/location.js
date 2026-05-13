import { submitUserLocation } from '../api';

const GEO_TIMEOUT = 4000;
const GEO_PROMPT_TIMEOUT = 5000;

export const getLocationErrorMessage = (error) => {
  if (error?.message === 'GEO_INSECURE_CONTEXT') {
    return '当前访问地址不是HTTPS安全环境，浏览器禁止读取定位。请使用HTTPS地址后重试。';
  }
  if (error?.message === 'GEO_PROMPT_TIMEOUT') {
    return '浏览器定位授权长时间未响应，请检查地址栏证书状态，并在浏览器权限中允许位置。';
  }
  if (error?.message === 'GEO_UNSUPPORTED') {
    return '当前浏览器不支持定位，请更换浏览器后重试';
  }
  if (error?.code === 1) {
    return '请在手机系统或浏览器中开启位置权限后重试';
  }
  if (error?.code === 2) {
    return '暂时无法获取当前位置，请确认定位服务已开启';
  }
  if (error?.code === 3) {
    return '获取当前位置超时，请开启定位后重试';
  }
  return error?.response?.data?.detail || error?.message || '暂时无法获取当前位置';
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
