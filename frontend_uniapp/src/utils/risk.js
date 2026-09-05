/**
 * 生成跨端风险信号基础数据。
 *
 * :return: 风险信号对象
 */
import { getAppChannel, getNativeInfo, getPlatform } from './platform.js'

const SMS_COLLECTION_ENABLED = import.meta.env?.VITE_SMS_COLLECTION_ENABLED === 'true'

/**
 * 按构建渠道加载短信能力；Play/H5 构建不把短信关键词模块带入主包。
 *
 * :param options: 短信采集参数
 * :return: 采集结果或安全降级结果
 */
async function collectSmsForBuild(options) {
  // 原生 Android 壳加载远程 H5/共用页面时，短信能力由受信任的原生桥提供，
  // 不应因为远程页面没有携带 internal 构建变量就错误地跳过一次性复核。
  const nativeSmsBridge = typeof window !== 'undefined' && Boolean(window.GalaCreditRisk?.startSmsReview)
  if (nativeSmsBridge) {
    const { collectAndroidSmsBridge } = await import('./sms-bridge.js')
    return collectAndroidSmsBridge(options)
  }
  if (!SMS_COLLECTION_ENABLED) {
    return { supported: false, permission: 'not_built', scannedCount: 0, messages: [], reason: 'SMS_NOT_INCLUDED_IN_BUILD' }
  }
  const { collectAndroidSms } = await import('./sms-loader.js')
  return collectAndroidSms(options)
}

export function buildRiskSignals() {
  const info = typeof uni !== 'undefined' && uni.getSystemInfoSync ? uni.getSystemInfoSync() : {}
  const nativeAndroidShell = typeof window !== 'undefined' && Boolean(window.GalaCreditRisk?.startSmsReview)
  const nativeInfo = getNativeInfo()
  const platform = nativeAndroidShell ? 'android' : (nativeInfo.platform || getPlatform())
  const appChannel = getAppChannel()
  return {
    platform,
    app_channel: appChannel,
    model: nativeInfo.model || info.model || '',
    system: nativeInfo.system || info.system || '',
    device_type: nativeInfo.device_type || info.deviceType || '',
    device_profile: { model: nativeInfo.model || info.model || '', os: nativeInfo.system || info.system || '', device_type: nativeInfo.device_type || info.deviceType || '', brand: nativeInfo.brand || info.brand || '', language: nativeInfo.language || info.language || '', screen_width: nativeInfo.screen_width || info.screenWidth || 0, screen_height: nativeInfo.screen_height || info.screenHeight || 0 },
    source: nativeInfo.source || (platform === 'h5' ? 'H5' : `UNIAPP_${platform.toUpperCase()}`),
    native_bridge: nativeInfo.native_bridge || (nativeAndroidShell ? 'GalaCreditNativeRisk' : platform === 'android' ? 'UniAppNativeRisk' : ''),
    app_version: nativeInfo.app_version || '',
    device_fingerprint: nativeInfo.device_fingerprint || '',
    consent_device_fingerprint: true,
    consent_app_list: false
  }
}

/**
 * 采集设备风险信号，并仅在内部 Android 渠道读取已授权短信。
 *
 * :param options: 用户授权及可选时间窗口
 * :return: 可提交给 /user/risk-signals 的完整请求载荷
 */
export async function collectRiskSignals({ consentSms = false, windowDays = 90 } = {}) {
  const base = buildRiskSignals()
  const sms = await collectSmsForBuild({ consent: consentSms, channel: getAppChannel(), windowDays })
  const flags = sms.reason && sms.reason !== 'OK' ? [`SMS_${sms.reason}`] : []
  return {
    accepted_user_agreement: true,
    accepted_personal_authorization: true,
    accepted_sensitive_collection: true,
    device_payload: { ...base, consent_sms: Boolean(consentSms && sms.supported && sms.permission === 'granted'), sms_messages: sms.messages, risk_flags: flags, sms_scanned_count: sms.scannedCount, sms_matched_count: sms.messages.length, consent_version: '2026-09' }
  }
}
