import { describe, expect, it } from 'vitest';
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
  });
});
