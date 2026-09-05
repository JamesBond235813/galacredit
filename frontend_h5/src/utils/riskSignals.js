const BRIDGE_NAMES = ['GalaCreditNative', 'GalaCreditBridge', 'AndroidRiskBridge'];

const normalizeText = (value) => String(value || '').replace(/\s+/g, ' ').trim();

const collectBridge = () => {
  if (typeof window === 'undefined') {
    return null;
  }
  for (const name of BRIDGE_NAMES) {
    const bridge = window[name];
    if (!bridge) {
      continue;
    }
    if (typeof bridge.collectRiskSignals === 'function') {
      return { name, value: bridge.collectRiskSignals };
    }
    if (typeof bridge.getRiskSignals === 'function') {
      return { name, value: bridge.getRiskSignals };
    }
  }
  return null;
};

const parseNativeInfo = () => {
  if (typeof window === 'undefined') return {};
  try {
    const direct = window.GalaCreditNativeInfo;
    if (direct && typeof direct === 'object') return direct;
    const raw = window.GalaCreditRisk?.getNativeInfo?.();
    if (raw) {
      const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
      return parsed && typeof parsed === 'object' ? parsed : {};
    }
  } catch (error) {
    // Fall back to the safe H5 defaults when the native summary is unavailable.
  }
  return {};
};

const collectAndroidSms = (consentSms) => new Promise((resolve) => {
  const bridge = typeof window !== 'undefined' ? window.GalaCreditRisk : null;
  if (!consentSms || typeof bridge?.startSmsReview !== 'function') {
    resolve({ messages: [], scannedCount: 0, reason: consentSms ? 'NATIVE_BRIDGE_UNAVAILABLE' : 'SMS_CONSENT_NOT_GRANTED' });
    return;
  }
  const callbackName = `__gcLegacySmsReview_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  let settled = false;
  let timeout;
  const finish = (payload = {}) => {
    if (settled) return;
    settled = true;
    clearTimeout(timeout);
    delete window[callbackName];
    resolve({
      messages: Array.isArray(payload.messages) ? payload.messages : [],
      scannedCount: Number(payload.scannedCount || 0),
      reason: payload.reason || 'SMS_READ_FAILED'
    });
  };
  timeout = setTimeout(() => finish({ reason: 'SMS_BRIDGE_TIMEOUT' }), 15000);
  window[callbackName] = finish;
  try {
    bridge.startSmsReview(callbackName, true);
  } catch (error) {
    finish({ reason: String(error?.message || error || 'SMS_BRIDGE_FAILED').slice(0, 160) });
  }
});

const safeStringify = (value) => {
  try {
    return JSON.stringify(value);
  } catch (error) {
    return '';
  }
};

const hashString = async (value) => {
  const source = new TextEncoder().encode(value);
  if (typeof crypto !== 'undefined' && crypto.subtle?.digest) {
    const digest = await crypto.subtle.digest('SHA-256', source);
    return Array.from(new Uint8Array(digest)).map((item) => item.toString(16).padStart(2, '0')).join('');
  }
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }
  return `fallback-${Math.abs(hash)}`;
};

export const buildBrowserRiskProfile = () => {
  if (typeof window === 'undefined') {
    return {
      browser_name: 'unknown',
      browser_version: 'unknown',
      platform: 'unknown',
      language: 'unknown',
      timezone: 'unknown',
      screen_width: 0,
      screen_height: 0
    };
  }
  const navigator = window.navigator || {};
  const ua = navigator.userAgent || '';
  const browserName = /Chrome/i.test(ua) ? 'Chrome' : /Safari/i.test(ua) ? 'Safari' : /Firefox/i.test(ua) ? 'Firefox' : 'Browser';
  const browserVersion = (ua.match(/(?:Chrome|Version|Firefox)\/([0-9.]+)/i) || [null, 'unknown'])[1];
  return {
    browser_name: browserName,
    browser_version: browserVersion || 'unknown',
    platform: navigator.platform || 'unknown',
    language: navigator.language || 'unknown',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'unknown',
    screen_width: window.screen?.width || 0,
    screen_height: window.screen?.height || 0
  };
};

export const collectNativeRiskSignals = async ({ consentSms = false } = {}) => {
  const nativeInfo = parseNativeInfo();
  const androidBridge = typeof window !== 'undefined' ? window.GalaCreditRisk : null;
  if (androidBridge?.startSmsReview) {
    const sms = await collectAndroidSms(consentSms);
    return {
      native_bridge: nativeInfo.native_bridge || 'GalaCreditNativeRisk',
      source: nativeInfo.source || 'NATIVE_ANDROID',
      platform: 'android',
      app_channel: nativeInfo.app_channel || (androidBridge.getAppChannel?.() || 'play'),
      sms_messages: sms.messages,
      installed_apps: [],
      device_profile: nativeInfo,
      risk_flags: sms.reason === 'OK' ? [] : [`SMS_${sms.reason}`],
      device_fingerprint: nativeInfo.device_fingerprint || null,
      sms_scanned_count: sms.scannedCount
    };
  }
  const bridge = collectBridge();
  if (!bridge) {
    return {
      native_bridge: null,
      source: 'H5',
      sms_messages: [],
      installed_apps: [],
      device_profile: {},
      risk_flags: [],
      app_channel: 'play'
    };
  }

  const result = await bridge.value();
  return {
    native_bridge: bridge.name,
    source: 'NATIVE',
    sms_messages: Array.isArray(result?.sms_messages) ? result.sms_messages : [],
    installed_apps: Array.isArray(result?.installed_apps) ? result.installed_apps : [],
    device_profile: result?.device_profile || {},
    risk_flags: Array.isArray(result?.risk_flags) ? result.risk_flags : [],
    device_fingerprint: result?.device_fingerprint || null,
    app_channel: result?.app_channel || 'play'
  };
};

export const buildRiskSignalPayload = async ({ phone, consentSms, consentAppList, consentDeviceFingerprint }) => {
  const browserProfile = buildBrowserRiskProfile();
  const nativePayload = await collectNativeRiskSignals({ consentSms: Boolean(consentSms) });
  const payload = {
    consent_sms: Boolean(consentSms),
    consent_app_list: Boolean(consentAppList),
    consent_device_fingerprint: Boolean(consentDeviceFingerprint),
    sms_messages: consentSms ? nativePayload.sms_messages : [],
    // The current version has no complete app-list collection capability; never upload it.
    installed_apps: [],
    device_profile: {
      ...browserProfile,
      ...(nativePayload.device_profile || {})
    },
    native_bridge: nativePayload.native_bridge,
    source: nativePayload.source,
    platform: nativePayload.platform || browserProfile.platform,
    app_channel: nativePayload.app_channel || 'play',
    browser_name: browserProfile.browser_name,
    browser_version: browserProfile.browser_version,
    screen_width: browserProfile.screen_width,
    screen_height: browserProfile.screen_height,
    timezone: browserProfile.timezone,
    language: browserProfile.language,
    risk_flags: nativePayload.risk_flags || [],
    device_fingerprint: consentDeviceFingerprint ? nativePayload.device_fingerprint || null : null,
    consent_version: '2026-08'
  };
  const appVersion = typeof window !== 'undefined' && window.__APP_VERSION__ ? window.__APP_VERSION__ : 'web';
  payload.app_version = appVersion;
  if (!payload.device_fingerprint) {
    payload.device_fingerprint = await hashString(
      safeStringify({
        phone: normalizeText(phone),
        browser_name: browserProfile.browser_name,
        browser_version: browserProfile.browser_version,
        screen_width: browserProfile.screen_width,
        screen_height: browserProfile.screen_height,
        timezone: browserProfile.timezone,
        language: browserProfile.language,
        native_bridge: payload.native_bridge,
        consent_sms: Boolean(consentSms),
        consent_app_list: Boolean(consentAppList),
        consent_device_fingerprint: Boolean(consentDeviceFingerprint)
      })
    );
  }
  return payload;
};
