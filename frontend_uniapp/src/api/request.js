import { getStorage } from '../utils/platform.js'

const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || 'https://galacredit.ebamotor.com/api'

/**
 * 统一发起 API 请求，H5 与 App 使用同一请求契约。
 *
 * :param options: 请求配置
 * :return: Promise<响应数据>
 */
export function request(options) {
  const method = String(options.method || 'GET').toUpperCase()
  const header = { ...(options.header || {}), 'client-id': options.clientId || 'uniapp' }
  const token = getStorage('token')
  if (token) header.Authorization = `Bearer ${token}`
  const retryLimit = Number.isInteger(options.retries) ? Math.max(0, options.retries) : (['GET', 'HEAD'].includes(method) ? 2 : 0)
  const timeout = Number(options.timeout || 20000)
  const { retries: _retries, timeout: _timeout, ...requestOptions } = options
  return new Promise((resolve, reject) => {
    let attempt = 0
    const send = () => {
      uni.request({ ...requestOptions, method, timeout, url: `${API_BASE_URL}${options.url}`, header,
        success: ({ data, statusCode }) => {
          if (statusCode >= 500 && attempt < retryLimit) {
            attempt += 1
            setTimeout(send, 250 * (2 ** (attempt - 1)))
            return
          }
          if (statusCode === 401) {
            try { uni.removeStorageSync('token') } catch {}
            if (typeof uni.reLaunch === 'function' && !String(options.url || '').startsWith('/auth/')) uni.reLaunch({ url: '/pages/login/index' })
            reject(new Error('登录已过期'))
            return
          }
          if (data && typeof data === 'object' && data.code !== undefined && ![0, 200].includes(Number(data.code))) { reject(new Error(data.msg || 'Request failed')); return }
          resolve(data)
        },
        fail: (error) => {
          if (attempt < retryLimit) {
            attempt += 1
            setTimeout(send, 250 * (2 ** (attempt - 1)))
            return
          }
          reject(error)
        } })
    }
    send()
  })
}
