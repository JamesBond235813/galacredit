import { describe, expect, it, vi } from 'vitest';
import { buildBrowserRiskProfile, buildRiskSignalPayload } from './riskSignals';

describe('risk signal helpers', () => {
  it('returns a browser profile object even without native bridge access', () => {
    const profile = buildBrowserRiskProfile();
    expect(profile).toHaveProperty('browser_name');
    expect(profile).toHaveProperty('timezone');
    expect(profile).toHaveProperty('screen_width');
  });

  it('builds a stable payload when no native bridge is available', async () => {
    const payload = await buildRiskSignalPayload({
      phone: '233240000001',
      consentSms: false,
      consentAppList: false,
      consentDeviceFingerprint: true
    });

    expect(payload.consent_sms).toBe(false);
    expect(payload.consent_app_list).toBe(false);
    expect(payload.consent_device_fingerprint).toBe(true);
    expect(payload.device_fingerprint).toBeTruthy();
    expect(payload.device_profile).toHaveProperty('browser_name');
    expect(payload.installed_apps).toEqual([]);
  });

  it('uses the Android internal bridge only after separate SMS consent', async () => {
    const startSmsReview = vi.fn((callbackName, consent) => {
      expect(consent).toBe(true);
      window[callbackName]?.({
        supported: true,
        permission: 'granted',
        reason: 'OK',
        scannedCount: 2,
        messages: [{ address: 'Bank', body: 'loan approved', time: new Date().toISOString() }]
      });
    });
    globalThis.window = {
      GalaCreditNativeInfo: { platform: 'android', app_channel: 'internal', native_bridge: 'GalaCreditNativeRisk' },
      GalaCreditRisk: { startSmsReview, getAppChannel: () => 'internal' }
    };
    const payload = await buildRiskSignalPayload({ phone: '233240000001', consentSms: true, consentAppList: true, consentDeviceFingerprint: false });
    expect(startSmsReview).toHaveBeenCalledTimes(1);
    expect(payload.platform).toBe('android');
    expect(payload.app_channel).toBe('internal');
    expect(payload.sms_messages).toHaveLength(1);
    expect(payload.installed_apps).toEqual([]);
    delete globalThis.window;
  });

  it('does not invoke Android SMS bridge without separate consent', async () => {
    const startSmsReview = vi.fn();
    globalThis.window = {
      GalaCreditNativeInfo: { platform: 'android', app_channel: 'internal' },
      GalaCreditRisk: { startSmsReview, getAppChannel: () => 'internal' }
    };
    const payload = await buildRiskSignalPayload({ phone: '233240000001', consentSms: false, consentAppList: false, consentDeviceFingerprint: false });
    expect(startSmsReview).not.toHaveBeenCalled();
    expect(payload.sms_messages).toEqual([]);
    delete globalThis.window;
  });
});
