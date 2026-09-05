/**
 * 统一封装跨端存储，避免业务代码直接依赖 localStorage。
 *
 * :param key: 存储键
 * :param value: 要保存的值
 * :return: 无
 */
export function setStorage(key, value) {
  if (typeof uni !== 'undefined' && uni.setStorageSync) {
    uni.setStorageSync(key, value)
    return
  }
  if (typeof localStorage !== 'undefined') localStorage.setItem(key, JSON.stringify(value))
}

/**
 * 读取跨端存储。
 *
 * :param key: 存储键
 * :return: 存储值或 null
 */
export function getStorage(key) {
  if (typeof uni !== 'undefined' && uni.getStorageSync) return uni.getStorageSync(key)
  if (typeof localStorage === 'undefined') return null
  try { return JSON.parse(localStorage.getItem(key)) } catch { return null }
}

/**
 * 读取最近一次风控任务，必要时从原生安全会话恢复。
 *
 * :return: 风控任务摘要；不存在时返回 null
 */
export function getRiskTask() {
  const local = getStorage('galacredit_risk_task')
  if (local?.task_number) return local
  try {
    const nativeValue = typeof window !== 'undefined' && window.GalaCreditSession?.getRiskTask?.()
    if (nativeValue) {
      const parsed = JSON.parse(nativeValue)
      if (parsed?.task_number) {
        setStorage('galacredit_risk_task', parsed)
        return parsed
      }
    }
  } catch {
    // 原生桥接不可用或摘要损坏时按无任务处理，不能阻断风险页。
  }
  return null
}

/**
 * 读取原生壳提供的环境摘要。
 *
 * Android 原生壳可能先于页面脚本只暴露 JavaScriptInterface，因此同时兼容
 * document 注入对象和 RiskBridge 的同步 JSON 方法。
 *
 * :return: 原生环境摘要；不可用时返回空对象
 */
export function getNativeInfo() {
  try {
    const direct = typeof window !== 'undefined' && window.GalaCreditNativeInfo
    if (direct && typeof direct === 'object') return direct
    const raw = typeof window !== 'undefined' && window.GalaCreditRisk?.getNativeInfo?.()
    if (raw) {
      const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
      if (parsed && typeof parsed === 'object') return parsed
    }
  } catch {
    // 原生摘要不可用时按安全默认值继续，不阻断页面业务。
  }
  return {}
}

/**
 * 获取当前运行平台标识。
 *
 * :return: h5、android 或 ios
 */
export function getPlatform() {
  try {
    const nativePlatform = getNativeInfo().platform
    if (nativePlatform === 'ios' || nativePlatform === 'android') return nativePlatform
    // Android WebView 需要在登录页脚本执行前识别平台，不能等到短信桥回调时才判断。
    if (typeof window !== 'undefined' && window.GalaCreditRisk?.startSmsReview) return 'android'
  } catch {
    // 原生环境摘要不可用时继续走 UniApp/H5 的平台判断。
  }
  // #ifdef H5
  return 'h5'
  // #endif
  // #ifdef APP-PLUS
  return uni.getSystemInfoSync().platform === 'ios' ? 'ios' : 'android'
  // #endif
  return 'h5'
}

/**
 * 获取发行渠道，默认采用 Google Play 安全策略。
 *
 * :return: play 或 internal
 */
export function getAppChannel() {
  try {
    const nativeChannel = getNativeInfo().app_channel
    if (nativeChannel === 'appstore' || nativeChannel === 'internal' || nativeChannel === 'play') return nativeChannel
  } catch {
    // 原生环境摘要不可用时继续走已有桥接判断。
  }
  try {
    const nativeChannel = typeof window !== 'undefined' && window.GalaCreditRisk?.getAppChannel?.()
    if (nativeChannel === 'internal') return 'internal'
  } catch {
    // 原生桥接不可用时继续使用构建渠道，默认按 Play 安全策略处理。
  }
  try {
    const appId = typeof plus !== 'undefined' && plus.runtime?.appid
    if (String(appId || '').toLowerCase().includes('internal')) return 'internal'
  } catch {
    // 非 App-Plus 运行时没有 plus 对象。
  }
  return (typeof import.meta !== 'undefined' && import.meta.env?.VITE_APP_CHANNEL) === 'internal' ? 'internal' : 'play'
}

/**
 * 获取一次性当前位置。
 *
 * iOS 原生壳使用 Core Location 桥接以保证 WKWebView 权限回调稳定；其他运行时
 * 继续使用 UniApp 的系统定位 API。该函数不启动后台持续定位。
 *
 * :return: Promise<{latitude: number, longitude: number, accuracy: number}>
 */
export function getCurrentLocation() {
  const nativeLocation = typeof window !== 'undefined' && window.webkit?.messageHandlers?.galacreditLocation
  if (nativeLocation) {
    return new Promise((resolve, reject) => {
      const callbackName = `__gcLocation_${Date.now()}_${Math.random().toString(16).slice(2)}`
      let settled = false
      let timeout
      const cleanup = () => {
        if (typeof window !== 'undefined') delete window[callbackName]
        clearTimeout(timeout)
      }
      const finish = (payload) => {
        if (settled) return
        settled = true
        cleanup()
        const latitude = Number(payload?.latitude)
        const longitude = Number(payload?.longitude)
        const accuracy = Number(payload?.accuracy)
        if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
          resolve({ latitude, longitude, accuracy: Number.isFinite(accuracy) ? accuracy : 0 })
        } else {
          reject(new Error(payload?.error || 'Location is unavailable.'))
        }
      }
      timeout = setTimeout(() => finish({ error: 'Location request timed out.' }), 30000)
      window[callbackName] = finish
      try {
        nativeLocation.postMessage({ callbackName })
      } catch (error) {
        finish({ error: error?.message || 'Location request failed.' })
      }
    })
  }
  return new Promise((resolve, reject) => {
    if (typeof uni === 'undefined' || typeof uni.getLocation !== 'function') {
      reject(new Error('Location is not supported on this device.'))
      return
    }
    uni.getLocation({ type: 'wgs84', success: resolve, fail: reject })
  })
}

/**
 * 解析上传接口响应并将业务失败转换为可重试异常。
 *
 * :param data: 上传回调中的响应内容
 * :param statusCode: 可选 HTTP 状态码
 * :return: 解析后的接口响应
 */
function parseUploadResponse(data, statusCode) {
  if (statusCode !== undefined && (statusCode < 200 || statusCode >= 300)) throw new Error(`Upload failed (${statusCode})`)
  let parsed = data
  if (typeof data === 'string') {
    try { parsed = JSON.parse(data) } catch { parsed = { msg: data } }
  }
  if (parsed && typeof parsed === 'object' && parsed.code !== undefined && ![0, 200].includes(Number(parsed.code))) throw new Error(parsed.msg || 'Upload failed')
  return parsed
}

function uploadBaseUrl() {
  return (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || 'https://galacredit.ebamotor.com/api'
}

function nativeImagePickerAvailable() {
  return typeof window !== 'undefined' && Boolean(window.webkit?.messageHandlers?.galacreditImagePicker?.postMessage)
}

function dataUrlToFile(dataUrl, index) {
  const match = String(dataUrl || '').match(/^data:([^;,]+)?;base64,(.+)$/)
  if (!match || typeof atob !== 'function') return null
  const mime = match[1] || 'image/jpeg'
  const binary = atob(match[2])
  const bytes = new Uint8Array(binary.length)
  for (let offset = 0; offset < binary.length; offset += 1) bytes[offset] = binary.charCodeAt(offset)
  const blob = new Blob([bytes], { type: mime })
  return typeof File === 'function' ? new File([blob], `galacredit-${index + 1}.jpg`, { type: mime }) : blob
}

/**
 * 调用 iOS 原生图片选择降级桥接，兼容 iOS 18.0–18.3 的 WKWebView。
 *
 * :param count: 需要选择的图片数量
 * :return: 图片文件数组
 */
function chooseNativeShellImages(count) {
  return new Promise((resolve, reject) => {
    const callbackName = `__gcImagePicker_${Date.now()}_${Math.random().toString(16).slice(2)}`
    let settled = false
    let timeout
    const cleanup = () => {
      if (typeof window !== 'undefined') delete window[callbackName]
      clearTimeout(timeout)
    }
    const finish = (payload) => {
      if (settled) return
      settled = true
      cleanup()
      const files = (Array.isArray(payload?.images) ? payload.images : []).map(dataUrlToFile).filter(Boolean)
      files.length ? resolve(files) : reject(new Error('No image selected'))
    }
    timeout = setTimeout(() => {
      if (settled) return
      settled = true
      cleanup()
      reject(new Error('Image picker timed out'))
    }, 30000)
    window[callbackName] = finish
    try {
      window.webkit.messageHandlers.galacreditImagePicker.postMessage({ callbackName, count: Math.max(1, Math.min(2, Number(count) || 1)) })
    } catch (error) {
      settled = true
      cleanup()
      reject(error)
    }
  })
}

async function uploadNativeFiles(url, files, formData = {}, token = '', fieldNames = []) {
  const form = new FormData()
  files.forEach((file, index) => {
    const fieldName = fieldNames[index] || (index === 0 ? 'front_image' : 'back_image')
    form.append(fieldName, file, file.name || `galacredit-${index + 1}.jpg`)
  })
  Object.entries(formData).forEach(([key, value]) => form.append(key, String(value)))
  const controller = typeof AbortController === 'function' ? new AbortController() : null
  const timeout = setTimeout(() => controller?.abort(), 45000)
  let response
  try {
    response = await fetch(`${uploadBaseUrl()}${url}`, {
      method: 'POST',
      headers: { 'client-id': 'uniapp', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: form,
      signal: controller?.signal
    })
  } finally {
    clearTimeout(timeout)
  }
  return parseUploadResponse(await response.text(), response.status)
}

/**
 * 选择并上传图片到统一接口。
 *
 * :param url: 上传路径
 * :param formData: 附加表单字段
 * :return: Promise<接口响应>
 */
export function uploadImage(url, formData = {}, fileName = 'file') {
  if (nativeImagePickerAvailable()) {
    const token = getStorage('token')
    return chooseNativeShellImages(1).then((files) => uploadNativeFiles(url, files, formData, token, [fileName]))
  }
  return new Promise((resolve, reject) => {
    uni.chooseImage({ count: 1, success: ({ tempFilePaths }) => {
      const token = getStorage('token')
      const header = { 'client-id': 'uniapp', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
      uni.uploadFile({ url: `${uploadBaseUrl()}${url}`, filePath: tempFilePaths[0], name: fileName, formData, header, timeout: 45000, success: ({ data, statusCode }) => { try { resolve(parseUploadResponse(data, statusCode)) } catch (error) { reject(error) } }, fail: reject })
    }, fail: reject })
  })
}

/**
 * 选择并以同一个 multipart 请求上传 Ghana Card 正反面。
 *
 * :param url: 上传路径
 * :param formData: 附加表单字段
 * :return: Promise<接口响应>
 */
export function uploadIdentityImages(url, formData = {}) {
  return new Promise((resolve, reject) => {
    if (nativeImagePickerAvailable()) {
      const token = getStorage('token')
      chooseNativeShellImages(2).then((files) => uploadNativeFiles(url, files, formData, token, ['front_image', 'back_image'])).then(resolve).catch(reject)
      return
    }
    uni.chooseImage({ count: 2, success: ({ tempFilePaths }) => {
      if (!tempFilePaths || tempFilePaths.length < 2) {
        reject(new Error('Please choose both sides in the GalaCredit app.'))
        return
      }
      const token = getStorage('token')
      if (typeof plus === 'undefined' && uni.uploadFiles) {
        const header = { 'client-id': 'uniapp', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
        uni.uploadFiles({ url: `${uploadBaseUrl()}${url}`, files: [{ name: 'front_image', uri: tempFilePaths[0] }, { name: 'back_image', uri: tempFilePaths[1] }], formData, header, timeout: 45000, success: ({ data, statusCode }) => { try { resolve(parseUploadResponse(data, statusCode)) } catch (error) { reject(error) } }, fail: reject })
        return
      }
      if (typeof plus === 'undefined') { reject(new Error('This browser cannot upload both document sides together.')); return }
      const task = plus.uploader.createUpload(`${uploadBaseUrl()}${url}`, { method: 'POST', timeout: 45 }, (upload, status) => {
        if (status >= 200 && status < 300) {
          try { resolve(parseUploadResponse(upload.responseText || '{}', status)) } catch (error) { reject(error) }
        } else reject(new Error(`Upload failed (${status})`))
      })
      task.addFile(tempFilePaths[0], { key: 'front_image' })
      task.addFile(tempFilePaths[1], { key: 'back_image' })
      Object.entries(formData).forEach(([key, value]) => task.addData(key, String(value)))
      if (token) task.setRequestHeader('Authorization', `Bearer ${token}`)
      task.setRequestHeader('client-id', 'uniapp')
      task.start()
    }, fail: reject })
  })
}

/**
 * 规范化系统联系人选择结果，仅保留一条联系人所需的最小字段。
 *
 * :param name: 联系人姓名
 * :param phone: 联系人电话号码
 * :return: 联系人对象；字段不完整时返回 null
 */
export function normalizeContact(name, phone) {
  const normalizedName = String(name || '').trim().slice(0, 80)
  const digits = String(phone || '').replace(/\D/g, '')
  let normalizedPhone = ''
  if (/^233\d{9}$/.test(digits)) normalizedPhone = `+${digits}`
  else if (/^0\d{9}$/.test(digits)) normalizedPhone = `+233${digits.slice(1)}`
  else if (/^\d{9}$/.test(digits)) normalizedPhone = `+233${digits}`
  else if (/^\d{11}$/.test(digits)) normalizedPhone = digits
  return normalizedName && normalizedPhone ? { name: normalizedName, phone: normalizedPhone } : null
}

/**
 * 使用 Android 系统联系人选择器选择一条电话号码，避免读取完整通讯录。
 *
 * :return: Promise<{name: string, phone: string}>
 */
function chooseAndroidContact() {
  return new Promise((resolve, reject) => {
    let settled = false
    let timeout
    const finish = (error, contact) => {
      if (settled) return
      settled = true
      clearTimeout(timeout)
      error ? reject(error) : resolve(contact)
    }
    timeout = setTimeout(() => finish(new Error('Contact picker timed out')), 30000)
    try {
      const Intent = plus.android.importClass('android.content.Intent')
      const uri = plus.android.invoke('android.net.Uri', 'parse', 'content://com.android.contacts/data/phones')
      const intent = new Intent('android.intent.action.PICK', uri)
      plus.android.startActivityForResult(intent, (result) => {
        let cursor = null
        try {
          const dataIntent = result?.data || result
          const selectedUri = dataIntent ? plus.android.invoke(dataIntent, 'getData') : null
          if (!selectedUri) {
            finish(new Error('No contact selected'))
            return
          }
          const activity = plus.android.runtimeMainActivity()
          const resolver = activity.getContentResolver()
          cursor = resolver.query(selectedUri, ['display_name', 'data1'], null, null, null)
          if (!cursor) {
            finish(new Error('The selected contact could not be read'))
            return
          }
          plus.android.importClass(cursor)
          const hasRow = cursor.moveToFirst()
          const nameIndex = cursor.getColumnIndex('display_name')
          const phoneIndex = cursor.getColumnIndex('data1')
          const contact = hasRow
            ? normalizeContact(nameIndex >= 0 ? cursor.getString(nameIndex) : '', phoneIndex >= 0 ? cursor.getString(phoneIndex) : '')
            : null
          contact ? finish(null, contact) : finish(new Error('The selected contact has no usable phone number'))
        } catch (error) {
          finish(error)
        } finally {
          try { cursor?.close?.() } catch {
            // 游标关闭失败不应覆盖已返回的联系人结果。
          }
        }
      })
    } catch (error) {
      finish(error)
    }
  })
}

/**
 * 调用原生壳提供的联系人选择器桥接。
 *
 * :return: Promise<{name: string, phone: string}>
 */
function chooseNativeShellContact() {
  return new Promise((resolve, reject) => {
    const requestId = `contact_${Date.now()}_${Math.random().toString(16).slice(2)}`
    let timeout
    const cleanup = () => {
      if (typeof window !== 'undefined') {
        delete window.__gcContactPickerResolve
        delete window.__gcContactPickerReject
      }
      clearTimeout(timeout)
    }
    if (typeof window !== 'undefined' && window.webkit?.messageHandlers?.galacreditContactPicker) {
      window.__gcContactPickerResolve = (payload) => { const contact = normalizeContact(payload?.name, payload?.phone); cleanup(); contact ? resolve(contact) : reject(new Error('The selected contact has no usable phone number')) }
      window.__gcContactPickerReject = () => { cleanup(); reject(new Error('No contact selected')) }
      timeout = setTimeout(() => { cleanup(); reject(new Error('Contact picker timed out')) }, 30000)
      try { window.webkit.messageHandlers.galacreditContactPicker.postMessage({ requestId }) } catch (error) { cleanup(); reject(error) }
      return
    }
    if (typeof window !== 'undefined' && window.GalaCreditContacts?.pick) {
      window.__gcContactPickerResolve = (payload) => { const contact = normalizeContact(payload?.name, payload?.phone); cleanup(); contact ? resolve(contact) : reject(new Error('The selected contact has no usable phone number')) }
      window.__gcContactPickerReject = () => { cleanup(); reject(new Error('No contact selected')) }
      timeout = setTimeout(() => { cleanup(); reject(new Error('Contact picker timed out')) }, 30000)
      try { window.GalaCreditContacts.pick(requestId) } catch (error) { cleanup(); reject(error) }
      return
    }
    reject(new Error('Native contact picker is unavailable'))
  })
}

/**
 * 选择紧急联系人；只返回用户主动选择的一条联系人，不读取完整通讯录。
 *
 * :return: Promise<{name: string, phone: string}>
 */
export function chooseContact() {
  if (typeof window !== 'undefined' && (window.webkit?.messageHandlers?.galacreditContactPicker || window.GalaCreditContacts?.pick)) return chooseNativeShellContact()
  if (typeof plus === 'undefined') return Promise.reject(new Error('Contact selection is not supported on this browser'))
  const platform = typeof uni !== 'undefined' && uni.getSystemInfoSync ? uni.getSystemInfoSync().platform : ''
  if (platform === 'android') return chooseAndroidContact()
  return Promise.reject(new Error('Please use the native iOS contact picker'))
}
