import { afterEach, describe, expect, it, vi } from 'vitest'
import { buildRiskSignals, collectRiskSignals } from './risk.js'

describe('native risk environment bridge', () => {
  afterEach(() => {
    delete globalThis.window
    delete globalThis.uni
  })

  it('keeps iOS WebView signals as iOS instead of misclassifying them as H5', () => {
    globalThis.window = {
      GalaCreditNativeInfo: {
        platform: 'ios',
        app_channel: 'appstore',
        source: 'NATIVE_IOS',
        native_bridge: 'GalaCreditIOS',
        model: 'iPhone',
        system: 'iOS 18.6',
        device_type: 'phone',
        device_fingerprint: 'hash-1'
      }
    }
    globalThis.uni = { getSystemInfoSync: () => ({ platform: 'h5', model: 'browser' }) }

    expect(buildRiskSignals()).toMatchObject({
      platform: 'ios',
      app_channel: 'appstore',
      source: 'NATIVE_IOS',
      native_bridge: 'GalaCreditIOS',
      model: 'iPhone',
      device_fingerprint: 'hash-1'
    })
  })

  it('falls back to the safe Play channel when no native metadata exists', () => {
    globalThis.window = {}
    globalThis.uni = { getSystemInfoSync: () => ({ platform: 'h5', model: 'browser' }) }

    expect(buildRiskSignals()).toMatchObject({ platform: 'h5', app_channel: 'play', source: 'H5' })
  })

  it('recognises Android from the native risk bridge and keeps its metadata', () => {
    globalThis.window = {
      GalaCreditRisk: {
        getNativeInfo: () => JSON.stringify({ platform: 'android', app_channel: 'internal', source: 'NATIVE_ANDROID', native_bridge: 'GalaCreditNativeRisk', model: 'Pixel' })
      }
    }

    expect(buildRiskSignals()).toMatchObject({
      platform: 'android',
      app_channel: 'internal',
      source: 'NATIVE_ANDROID',
      native_bridge: 'GalaCreditNativeRisk',
      model: 'Pixel'
    })
  })

  it('uses the native Android SMS bridge even when the page build flag is disabled', async () => {
    const startSmsReview = vi.fn((callbackName) => {
      window[callbackName]?.({ supported: true, permission: 'granted', reason: 'OK', scannedCount: 1, messages: [{ address: 'Bank', body: 'loan approved', time: Date.now(), type: 1, read: 1 }] })
    })
    globalThis.window = { GalaCreditRisk: { getNativeInfo: () => JSON.stringify({ platform: 'android', app_channel: 'internal' }), startSmsReview } }
    const result = await collectRiskSignals({ consentSms: true })
    expect(startSmsReview).toHaveBeenCalledWith(expect.any(String), true)
    expect(result.device_payload.sms_messages).toHaveLength(1)
    expect(result.device_payload.consent_sms).toBe(true)
  })

  it('does not put SMS keywords or permission code into the bridge-only path', async () => {
    const source = await import('./sms-bridge.js?source-check')
    expect(source.collectAndroidSmsBridge).toBeTypeOf('function')
  })
})
