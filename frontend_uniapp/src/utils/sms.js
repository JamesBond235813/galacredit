import { SMS_KEYWORDS } from '../data/smsKeywords.js'
import { getPlatform } from './platform.js'

export const SMS_WINDOW_DAYS = 90
const MAX_SMS_ROWS = 5000

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^\${}()|[\]\\]/g, '\\$&')
}

function keywordPattern(keyword) {
  const escaped = escapeRegExp(keyword)
  // CSV 中的英文单词采用边界匹配，避免 loanapproved 被拆成 loan 命中。
  if (/^[a-z0-9][a-z0-9'-]*$/i.test(keyword)) {
    return new RegExp('(^|[^A-Za-z0-9_])' + escaped + '(?=$|[^A-Za-z0-9_])', 'i')
  }
  return new RegExp(escaped, 'i')
}

const COMPILED_KEYWORDS = SMS_KEYWORDS.map((keyword) => ({ keyword, pattern: keywordPattern(keyword) }))

/**
 * 解析 Android 毫秒时间戳或 ISO 文本。
 *
 * :param value: 短信时间
 * :return: 毫秒时间戳；无法解析时返回 null
 */
export function parseSmsTime(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return value < 100000000000 ? value * 1000 : value
  const parsed = Date.parse(String(value || ''))
  return Number.isFinite(parsed) ? parsed : null
}

/**
 * 返回短信正文命中的 CSV 关键词。
 *
 * :param text: 发送方、标题和正文
 * :return: 按 CSV 顺序排列的命中关键词
 */
export function matchSmsKeywords(text) {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim()
  if (!normalized) return []
  return COMPILED_KEYWORDS.filter(({ pattern }) => pattern.test(normalized)).map(({ keyword }) => keyword)
}

/**
 * 在设备端执行 90 天窗口和关键词过滤，并删除非必要字段。
 *
 * :param messages: 原始短信行
 * :param now: 过滤基准时间（毫秒）
 * :param windowDays: 时间窗口天数
 * :return: 可提交到服务端的最小短信集合
 */
export function filterSmsMessages(messages, now = Date.now(), windowDays = SMS_WINDOW_DAYS) {
  const cutoff = now - Math.max(1, Number(windowDays) || SMS_WINDOW_DAYS) * 86400000
  return (Array.isArray(messages) ? messages : []).slice(0, MAX_SMS_ROWS).flatMap((item) => {
    if (!item || typeof item !== 'object') return []
    const timestamp = parseSmsTime(item.time ?? item.timestamp ?? item.date)
    if (timestamp === null || timestamp < cutoff || timestamp > now) return []
    const address = String(item.address ?? item.sender ?? '').trim()
    const body = String(item.body ?? '').trim()
    const title = String(item.title ?? '').trim()
    const keywords = matchSmsKeywords([address, title, body].join(' '))
    if (!keywords.length) return []
    return [{
      address: address.slice(0, 120),
      body: body.slice(0, 2000),
      type: Number(item.type) === 2 ? 2 : 1,
      time: new Date(timestamp).toISOString(),
      read: Number(item.read) === 1 ? 1 : 0,
      keywords
    }]
  })
}

function androidPermission(permission) {
  return new Promise((resolve, reject) => {
    plus.android.requestPermissions([permission], (result) => {
      const granted = (result.granted || []).includes(permission)
      granted ? resolve(true) : reject(new Error('SMS permission was not granted.'))
    }, () => reject(new Error('SMS permission request failed.')))
  })
}

/**
 * 在获得用户明确授权的 Android 内部版本读取并过滤短信。
 *
 * Google Play 版本默认关闭此能力；该函数不会在 H5、iOS 或 Play 渠道
 * 请求权限。未授权、平台不支持或读取失败均返回可识别的降级结果。
 *
 * :param options: 是否已同意短信采集及时间窗口配置
 * :return: 采集状态、扫描数量和命中短信
 */
export async function collectAndroidSms({ consent = false, channel = '', now, windowDays = SMS_WINDOW_DAYS } = {}) {
  const currentChannel = channel || (typeof import.meta !== 'undefined' ? import.meta.env?.VITE_APP_CHANNEL : '') || 'play'
  const hasNativeShellBridge = typeof window !== 'undefined' && Boolean(window.GalaCreditRisk?.startSmsReview)
  const isAndroidAppRuntime = getPlatform() === 'android'
  if (!consent || (!hasNativeShellBridge && currentChannel !== 'internal') || (!hasNativeShellBridge && !isAndroidAppRuntime)) {
    return { supported: false, permission: 'not_requested', scannedCount: 0, messages: [], reason: 'CHANNEL_OR_CONSENT' }
  }
  // 原生登录壳中的远程 H5 没有 plus 运行时，优先使用受信任的原生桥接。
  if (hasNativeShellBridge) {
    const callbackName = `__gcSmsReview_${Date.now()}_${Math.random().toString(16).slice(2)}`
    return await new Promise((resolve) => {
      let settled = false
      const finish = (payload) => {
        if (settled) return
        settled = true
        clearTimeout(timeout)
        delete window[callbackName]
        // 原生桥接是异步的；未指定测试基准时以回调到达时刻为上界，避免几毫秒的
        // 线程调度延迟把刚读取的短信误判成未来时间。显式 now 仍保持完全可重复。
        const filterNow = Number.isFinite(now) ? now : Date.now()
        resolve({
          supported: Boolean(payload?.supported),
          permission: payload?.permission || 'denied_or_failed',
          scannedCount: Number(payload?.scannedCount || 0),
          messages: filterSmsMessages(payload?.messages || [], filterNow, windowDays),
          reason: payload?.reason || 'SMS_READ_FAILED'
        })
      }
      const timeout = setTimeout(() => finish({ supported: true, permission: 'timeout', reason: 'SMS_BRIDGE_TIMEOUT' }), 15000)
      window[callbackName] = finish
      try {
      // 原生层也会再次校验同意状态；这里不能把用户选择硬编码为 true。
      window.GalaCreditRisk.startSmsReview(callbackName, Boolean(consent))
      } catch (error) {
        finish({ supported: true, permission: 'bridge_failed', reason: String(error?.message || error || 'SMS_BRIDGE_FAILED').slice(0, 160) })
      }
    })
  }
  if (typeof plus === 'undefined') {
    return { supported: false, permission: 'not_supported', scannedCount: 0, messages: [], reason: 'NATIVE_BRIDGE_UNAVAILABLE' }
  }
  try {
    await androidPermission('android.permission.READ_SMS')
    const activity = plus.android.runtimeMainActivity()
    const resolver = activity.getContentResolver()
    const uri = plus.android.invoke('android.net.Uri', 'parse', 'content://sms')
    const projection = ['address', 'body', 'type', 'date', 'read']
    // 数据库查询本身同时限定上下界，避免未来时间短信先进入内存；本地过滤仍保留作为第二道防线。
    const collectionNow = Number.isFinite(now) ? now : Date.now()
    const cutoff = collectionNow - Math.max(1, Number(windowDays) || SMS_WINDOW_DAYS) * 86400000
    const cursor = resolver.query(uri, projection, 'date >= ? AND date <= ?', [String(cutoff), String(collectionNow)], 'date DESC')
    if (!cursor) return { supported: true, permission: 'granted', scannedCount: 0, messages: [], reason: 'EMPTY_CURSOR' }
    plus.android.importClass(cursor)
    const rows = []
    let scannedCount = 0
    try {
      while (cursor.moveToNext() && scannedCount < MAX_SMS_ROWS) {
        scannedCount += 1
        rows.push({
          address: cursor.getString(cursor.getColumnIndex('address')),
          body: cursor.getString(cursor.getColumnIndex('body')),
          type: cursor.getInt(cursor.getColumnIndex('type')),
          date: cursor.getLong(cursor.getColumnIndex('date')),
          read: cursor.getInt(cursor.getColumnIndex('read'))
        })
      }
    } finally {
      cursor.close()
    }
    return { supported: true, permission: 'granted', scannedCount, messages: filterSmsMessages(rows, collectionNow, windowDays), reason: 'OK' }
  } catch (error) {
    return { supported: true, permission: 'denied_or_failed', scannedCount: 0, messages: [], reason: String(error?.message || error || 'SMS_READ_FAILED').slice(0, 160) }
  }
}
