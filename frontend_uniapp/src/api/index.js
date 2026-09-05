import { request } from './request.js'
import { uploadIdentityImages, uploadImage } from '../utils/platform.js'

export function sendCode(payload) { return request({ url: '/auth/send-code', method: 'POST', data: payload }) }
export function smsLogin(payload) { return request({ url: '/auth/sms-login', method: 'POST', data: payload }) }
export function getUserInfo() { return request({ url: '/user/info', method: 'GET' }) }
export function getProducts(params = {}) { return request({ url: '/loan/products', method: 'GET', data: params }) }
export function getLoanHistory() { return request({ url: '/loan/status', method: 'GET' }) }
export function logout(payload) { return request({ url: '/auth/logout', method: 'POST', data: payload }) }
export function createSliderCaptcha(payload) { return request({ url: '/auth/slider-captcha/create', method: 'POST', data: payload }) }
export function verifySliderCaptcha(payload) { return request({ url: '/auth/slider-captcha/verify', method: 'POST', data: payload }) }

/**
 * 获取用户首页聚合数据。
 *
 * :return: 用户资料、借款状态和产品列表
 */
export async function loadHomeData() {
  const [profile, status, products] = await Promise.all([
    request({ url: '/user/info', method: 'GET' }),
    request({ url: '/loan/status', method: 'GET' }),
    request({ url: '/loan/products', method: 'GET' })
  ])
  return { profile, status, products }
}

/**
 * 提交用户借款申请。
 *
 * :param payload: 申请表单
 * :return: 接口响应
 */
export function submitApplication(payload) { return request({ url: '/user/application', method: 'POST', data: payload }) }

/**
 * 提交身份材料。
 *
 * :param payload: OCR 材料数据
 * :return: 接口响应
 */
export function submitIdentity(payload) { return request({ url: '/user/ocr', method: 'POST', data: payload }) }

/**
 * 提交人脸认证结果。
 *
 * :param payload: 人脸认证数据
 * :return: 接口响应
 */
export function submitFaceAuth(formData) { return uploadImage('/user/face-auth', formData, 'face_image') }

/**
 * 提交提现申请。
 *
 * :param payload: 提现数据
 * :return: 接口响应
 */
export function submitWithdraw(payload) { return request({ url: '/loan/withdraw', method: 'POST', data: payload }) }

/**
 * 修改登录密码。
 *
 * :param payload: 新旧密码数据
 * :return: 接口响应
 */
export function changePassword(payload) { return request({ url: '/user/change-password', method: 'POST', data: payload }) }

/**
 * 发起还款支持请求。
 *
 * :param payload: 还款请求数据
 * :return: 接口响应
 */
export function requestRepayment(payload) { return request({ url: '/loan/repay-attempt', method: 'POST', data: payload }) }
export function submitOCR(formData) { return uploadIdentityImages('/user/ocr', formData) }
export function submitLocation(payload) { return request({ url: '/user/location', method: 'POST', data: payload }) }
export function submitRiskSignals(payload) { return request({ url: '/user/risk-signals', method: 'POST', data: payload }) }
export function queryRiskTask(payload) { return request({ url: '/user/risk-query', method: 'POST', data: payload }) }
export function bindUserChannel(payload) { return request({ url: '/user/channel-bind', method: 'POST', data: payload }) }
export function applyLimit() { return request({ url: '/loan/apply', method: 'POST' }) }
export function previewPurchaseContract(payload) { return request({ url: '/loan/purchase-contract/preview', method: 'POST', data: payload }) }
export function signPurchaseContract(payload) { return request({ url: '/loan/purchase-contract/sign', method: 'POST', data: payload }) }
export function sendOrderSmsCode() { return request({ url: '/loan/order-sms-code', method: 'POST' }) }
export function getEcardSecret(field, params = {}) { return request({ url: '/loan/ecard-secret', method: 'GET', data: { field, ...params } }) }
export function getLoanStatus() { return request({ url: '/loan/status', method: 'GET' }) }
export function getBill() { return request({ url: '/loan/bill', method: 'GET' }) }
