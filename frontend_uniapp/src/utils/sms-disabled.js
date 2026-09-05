/**
 * Google Play、iOS 和 H5 构建中的短信能力安全桩。
 *
 * 该模块故意不引用关键词库、Android 权限名或原生短信 API，确保安全渠道的
 * 构建产物不会携带短信采集实现。短信能力只在 Internal Android 构建中由
 * `sms.js` 提供。
 *
 * :param options: 与真实采集器兼容的参数
 * :return: 不采集短信的安全降级结果
 */
export async function collectAndroidSms(options = {}) {
  void options
  return {
    supported: false,
    permission: 'not_built',
    scannedCount: 0,
    messages: [],
    reason: 'SMS_NOT_INCLUDED_IN_BUILD'
  }
}

