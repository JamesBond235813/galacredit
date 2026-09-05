import { getStorage, setStorage } from './platform.js'

export const APP_VERSION = '1.1.0'
export const GHANA_COUNTRY_CODE = '+233'

/**
 * 规范化加纳手机号为后端接受的国际格式。
 *
 * :param value: 用户输入的手机号
 * :return: 233 开头的国际手机号，无法识别时返回空字符串
 */
export function normalizeGhanaPhone(value) {
  let digits = String(value || '').replace(/\D/g, '')
  if (digits.startsWith('233')) return digits.slice(0, 12)
  if (digits.startsWith('0')) digits = digits.slice(1)
  if (digits.length === 7) digits = digits.padStart(9, '0')
  return digits.length === 9 ? `233${digits}` : ''
}

/**
 * 判断手机号是否符合当前 Ghana 登录规则。
 *
 * :param value: 用户输入的手机号
 * :return: 是否有效
 */
export function isValidGhanaPhone(value) {
  return /^233\d{9}$/.test(normalizeGhanaPhone(value))
}

/**
 * 格式化金额显示，避免页面出现过多小数位。
 *
 * :param value: 金额
 * :return: GHS 金额文本
 */
export function formatMoney(value) {
  const amount = Number(value || 0)
  return `GHS ${Number.isFinite(amount) ? amount.toLocaleString('en-GH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}`
}

/**
 * 将后端时间转换为用户可读的日期。
 *
 * :param value: ISO 或日期字符串
 * :return: 日期文本
 */
export function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString('en-GH', { year: 'numeric', month: 'short', day: 'numeric' })
}

/**
 * 将后端借款状态转换为用户可读文案。
 *
 * :param value: 后端状态枚举
 * :return: 英文状态文案
 */
export function loanStatusLabel(value) {
  return ({
    INIT: 'Ready when you are',
    REVIEWING: 'Application under review',
    APPROVED: 'Credit approved',
    WITHDRAWING: 'Preparing disbursement',
    DISBURSED: 'Repayment in progress',
    OVERDUE: 'Action required',
    SETTLED: 'Previous loan settled',
    REJECTED: 'Application needs an update'
  })[String(value || '').toUpperCase()] || 'Account update'
}

/**
 * 将第三方风控任务状态转换为用户可读文案。
 *
 * :param value: 任务状态枚举
 * :return: 英文状态文案
 */
export function riskTaskStatusLabel(value) {
  return ({ '0': 'Queued', '1': 'In progress', '2': 'Completed', '3': 'Unable to complete' })[String(value ?? '')] || 'Pending'
}

/**
 * 将身份核验状态转换为用户可读文案。
 *
 * :param value: 身份核验状态枚举
 * :return: 英文状态文案
 */
export function verificationStatusLabel(value) {
  return ({ VERIFIED: 'Verified', APPROVED: 'Verified', PASSED: 'Verified', PENDING: 'Under review', REVIEWING: 'Under review', REJECTED: 'Needs an update', FAILED: 'Needs an update' })[String(value || '').toUpperCase()] || 'Not started'
}

/**
 * 将分期状态转换为用户可读文案。
 *
 * :param value: 分期状态枚举
 * :return: 英文状态文案
 */
export function installmentStatusLabel(value) {
  return ({ PAID: 'Paid', PENDING: 'Upcoming', DUE: 'Due', OVERDUE: 'Overdue', PARTIAL: 'Partially paid' })[String(value || '').toUpperCase()] || 'Upcoming'
}

/**
 * 读取当前登录令牌并在无令牌时跳转登录页。
 *
 * :return: 是否存在登录态
 */
export function requireSession() {
  if (getStorage('token')) return true
  uni.reLaunch({ url: '/pages/login/index' })
  return false
}

/**
 * 清除登录态并回到登录页面。
 *
 * :return: 无
 */
export function signOut() {
  setStorage('token', '')
  try { uni.removeStorageSync('token') } catch {}
  // 风控任务号属于账号上下文，退出时一并清理，避免下一位用户看到上一位用户的结果。
  try { uni.removeStorageSync('galacredit_risk_task') } catch {}
  // 原生壳也必须清除自己的安全会话，避免 H5 退出后下次启动又被恢复登录。
  try {
    if (typeof window !== 'undefined' && window.webkit?.messageHandlers?.galacreditLogout) {
      window.webkit.messageHandlers.galacreditLogout.postMessage({})
    } else if (typeof window !== 'undefined' && window.GalaCreditSession?.logout) {
      window.GalaCreditSession.logout()
    }
  } catch {
    // 桥接不存在或调用失败时，H5 本地退出仍然有效。
  }
  uni.reLaunch({ url: '/pages/login/index' })
}

/**
 * 将业务异常转换为稳定的用户提示。
 *
 * :param error: 请求异常
 * :param fallback: 默认提示
 * :return: 用户提示文本
 */
export function errorMessage(error, fallback = 'Something went wrong. Please try again.') {
  return error?.message || error?.data?.msg || fallback
}
