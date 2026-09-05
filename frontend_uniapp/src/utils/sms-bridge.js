/**
 * 通过受信任原生壳请求一次性短信复核。
 *
 * 原生层已经执行 90 天窗口、关键词过滤和字段最小化；本模块故意不引用
 * 关键词库、Android 权限名或 content provider，允许 Play 页面安全调用桥接桩。
 *
 * :param options: 是否已取得用户单独同意及窗口配置
 * :return: 原生桥接返回的最小短信结果
 */
export function collectAndroidSmsBridge({ consent = false } = {}) {
  const bridge = typeof window !== 'undefined' ? window.GalaCreditRisk : null
  if (!consent || !bridge?.startSmsReview) {
    return Promise.resolve({ supported: false, permission: 'not_requested', scannedCount: 0, messages: [], reason: 'CHANNEL_OR_CONSENT' })
  }
  const callbackName = `__gcSmsBridge_${Date.now()}_${Math.random().toString(16).slice(2)}`
  return new Promise((resolve) => {
    let settled = false
    let timeout
    const cleanup = () => {
      if (typeof window !== 'undefined') delete window[callbackName]
      clearTimeout(timeout)
    }
    const finish = (payload = {}) => {
      if (settled) return
      settled = true
      cleanup()
      resolve({
        supported: Boolean(payload.supported),
        permission: payload.permission || 'denied_or_failed',
        scannedCount: Number(payload.scannedCount || 0),
        messages: Array.isArray(payload.messages) ? payload.messages : [],
        reason: payload.reason || 'SMS_READ_FAILED'
      })
    }
    timeout = setTimeout(() => finish({ supported: true, permission: 'timeout', reason: 'SMS_BRIDGE_TIMEOUT' }), 15000)
    window[callbackName] = finish
    try {
      bridge.startSmsReview(callbackName, true)
    } catch (error) {
      finish({ supported: true, permission: 'bridge_failed', reason: String(error?.message || error || 'SMS_BRIDGE_FAILED').slice(0, 160) })
    }
  })
}
