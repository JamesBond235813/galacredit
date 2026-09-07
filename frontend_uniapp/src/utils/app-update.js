import { getPlatform } from './platform.js'

export const VERSION_MANIFEST_URL = 'https://galacredit.ebamotor.com/download/galacredit-version.json'

/**
 * 判断远端版本是否高于当前版本。
 *
 * :param currentCode: 当前 versionCode
 * :param targetCode: 远端 versionCode
 * :return: 是否需要升级
 */
export function shouldUpdate(currentCode, targetCode) {
  return Number(targetCode || 0) > Number(currentCode || 0)
}

/**
 * 读取当前 App-plus 版本号。
 *
 * :return: Promise<number> 当前 versionCode
 */
export function getCurrentVersionCode() {
  return new Promise((resolve) => {
    try {
      if (typeof plus !== 'undefined' && plus.runtime?.getProperty) {
        plus.runtime.getProperty(plus.runtime.appid, (info) => resolve(Number(info?.versionCode || 0)))
        return
      }
    } catch {}
    resolve(0)
  })
}

/**
 * 计算下载文件的 SHA-256。
 *
 * :param filePath: UniApp 临时文件路径
 * :return: Promise<string> 小写十六进制摘要
 */
export async function sha256File(filePath) {
  if (typeof plus === 'undefined' || !plus.io?.resolveLocalFileSystemURL) throw new Error('APK verification is only available in the Android app.')
  const buffer = await new Promise((resolve, reject) => {
    plus.io.resolveLocalFileSystemURL(filePath, (entry) => entry.file((file) => {
      const reader = new plus.io.FileReader()
      reader.onload = (event) => {
        try { resolve(Uint8Array.from(atob(String(event.target.result).split(',')[1] || ''), (char) => char.charCodeAt(0))) } catch (error) { reject(error) }
      }
      reader.onerror = reject
      reader.readAsDataURL(file)
    }, reject), reject)
  })
  if (globalThis.crypto?.subtle) {
    const digest = await crypto.subtle.digest('SHA-256', buffer)
    return Array.from(new Uint8Array(digest), (item) => item.toString(16).padStart(2, '0')).join('')
  }
  throw new Error('SHA-256 is not supported by this Android WebView.')
}

/**
 * 检查并按用户确认升级网络版 APK。
 *
 * :param options: 是否强制升级及提示回调
 * :return: Promise<boolean> 是否发现并处理了新版本
 */
export async function checkForAppUpdate({ silent = true } = {}) {
  if (getPlatform() !== 'android' || typeof plus === 'undefined') return false
  const currentCode = await getCurrentVersionCode()
  const manifest = await new Promise((resolve, reject) => uni.request({ url: VERSION_MANIFEST_URL, timeout: 12000, success: ({ data, statusCode }) => statusCode === 200 ? resolve(data) : reject(new Error('Version manifest unavailable')), fail: reject }))
  const targetCode = Number(manifest?.versionCode || 0)
  if (!shouldUpdate(currentCode, targetCode) || !manifest?.apkUrl || !manifest?.sha256) return false
  const proceed = await new Promise((resolve) => uni.showModal({ title: 'New version available', content: manifest.notes || `Version ${manifest.versionName || targetCode} is ready to install.`, confirmText: 'Update', cancelText: 'Later', success: ({ confirm }) => resolve(confirm) }))
  if (!proceed) return false
  uni.showLoading({ title: 'Downloading…', mask: true })
  try {
    const result = await new Promise((resolve, reject) => uni.downloadFile({ url: manifest.apkUrl, success: resolve, fail: reject }))
    if (result.statusCode !== 200 || !result.tempFilePath) throw new Error('APK download failed')
    const digest = await sha256File(result.tempFilePath)
    if (digest.toLowerCase() !== String(manifest.sha256).toLowerCase()) throw new Error('APK integrity check failed')
    plus.runtime.install(result.tempFilePath, { force: Boolean(manifest.force) }, () => {}, () => {})
    return true
  } catch (error) {
    if (!silent) uni.showModal({ title: 'Update failed', content: error?.message || 'Please try again later.', showCancel: false })
    return false
  } finally { uni.hideLoading() }
}
