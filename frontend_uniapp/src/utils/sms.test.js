import { describe, expect, it, vi } from 'vitest'
import { filterSmsMessages, matchSmsKeywords } from './sms.js'
import { chooseContact, getAppChannel, getCurrentLocation, normalizeContact, uploadIdentityImages, uploadImage } from './platform.js'

describe('device SMS minimisation', () => {
  it('uses the native package channel when the internal Android shell exposes it', () => {
    globalThis.window = { GalaCreditRisk: { getAppChannel: () => 'internal' } }
    expect(getAppChannel()).toBe('internal')
    delete globalThis.window
  })

  it('matches the published keywords without partial word matches', () => {
    expect(matchSmsKeywords('Your loan is approved')).toEqual(expect.arrayContaining(['loan', 'approved']))
    expect(matchSmsKeywords('loanapproved')).not.toContain('loan')
  })

  it('keeps only recent, future-safe, keyword-matched rows', () => {
    const now = Date.parse('2026-09-04T12:00:00Z')
    const rows = filterSmsMessages([
      { address: 'Bank', body: 'loan approved', date: now - 1000 },
      { address: 'Bank', body: 'loan approved', date: now - 91 * 86400000 },
      { address: 'Bank', body: 'hello friend', date: now - 1000 },
      { address: 'Bank', body: 'loan approved', date: now + 1000 }
    ], now)
    expect(rows).toHaveLength(1)
    expect(rows[0].keywords).toEqual(expect.arrayContaining(['loan', 'approved']))
    expect(rows[0]).not.toHaveProperty('date')
  })

  it('normalizes Ghana contact formats before upload', () => {
    expect(normalizeContact('Ama', '024 000 0000')).toEqual({ name: 'Ama', phone: '+233240000000' })
    expect(normalizeContact('Kojo', '240000000')).toEqual({ name: 'Kojo', phone: '+233240000000' })
    expect(normalizeContact('Esi', '123')).toBeNull()
  })

  it('rejects a business error returned with HTTP 200 during image upload', async () => {
    globalThis.uni = {
      getStorageSync: () => 'token-1',
      chooseImage: ({ success }) => success({ tempFilePaths: ['blob:image-1'] }),
      uploadFile: vi.fn(({ success }) => success({ statusCode: 200, data: JSON.stringify({ code: 400, msg: 'Document is unreadable' }) }))
    }
    await expect(uploadImage('/user/face-auth', { source: 'test' })).rejects.toThrow('Document is unreadable')
    expect(uni.uploadFile).toHaveBeenCalledWith(expect.objectContaining({
      header: expect.objectContaining({ Authorization: 'Bearer token-1', 'client-id': 'uniapp' })
    }))
  })

  it('uses the native shell bridge and re-applies the local 90-day filter', async () => {
    const now = Date.parse('2026-09-04T12:00:00Z')
    globalThis.window = {
      GalaCreditRisk: {
        startSmsReview: vi.fn((callbackName, consentAccepted) => {
          expect(consentAccepted).toBe(true)
          setTimeout(() => window[callbackName]?.({
            supported: true,
            permission: 'granted',
            scannedCount: 3,
            reason: 'OK',
            messages: [
              { address: 'Bank', body: 'loan approved', date: now - 1000 },
              { address: 'Bank', body: 'hello', date: now - 1000 },
              { address: 'Bank', body: 'loan approved', date: now + 1000 }
            ]
          }), 0)
        })
      }
    }
    const { collectAndroidSms } = await import('./sms.js')
    const result = await collectAndroidSms({ consent: true, channel: 'play', now })
    expect(result.permission).toBe('granted')
    expect(result.scannedCount).toBe(3)
    expect(result.messages).toHaveLength(1)
    expect(result.messages[0].keywords).toEqual(expect.arrayContaining(['loan', 'approved']))
    delete globalThis.window
  })

  it('uses the bridge callback time when no fixed filter time is provided', async () => {
    vi.useFakeTimers()
    globalThis.window = {
      GalaCreditRisk: {
        startSmsReview: vi.fn((callbackName) => {
          setTimeout(() => window[callbackName]?.({
            supported: true,
            permission: 'granted',
            scannedCount: 1,
            reason: 'OK',
            messages: [{ address: 'Bank', body: 'loan approved', time: Date.now(), type: 1, read: 1 }]
          }), 25)
        })
      }
    }
    const pending = import('./sms.js').then(({ collectAndroidSms }) => collectAndroidSms({ consent: true, channel: 'play' }))
    await vi.advanceTimersByTimeAsync(25)
    const result = await pending
    expect(result.messages).toHaveLength(1)
    vi.useRealTimers()
    delete globalThis.window
  })

  it('uses the iOS one-time location bridge and rejects malformed callbacks', async () => {
    const postMessage = vi.fn(({ callbackName }) => window[callbackName]?.({ latitude: 5.6037, longitude: -0.187, accuracy: 18 }))
    globalThis.window = { webkit: { messageHandlers: { galacreditLocation: { postMessage } } } }
    await expect(getCurrentLocation()).resolves.toEqual({ latitude: 5.6037, longitude: -0.187, accuracy: 18 })
    expect(postMessage).toHaveBeenCalledWith({ callbackName: expect.any(String) })
    delete globalThis.window
  })

  it('never asks the native bridge to read SMS without separate consent', async () => {
    const startSmsReview = vi.fn()
    globalThis.window = { GalaCreditRisk: { startSmsReview } }
    const { collectAndroidSms } = await import('./sms.js')
    const result = await collectAndroidSms({ consent: false, channel: 'internal' })
    expect(result.reason).toBe('CHANNEL_OR_CONSENT')
    expect(startSmsReview).not.toHaveBeenCalled()
    delete globalThis.window
  })

  it('uses the iOS native image bridge when WKWebView file panels are unavailable', async () => {
    const dataUrl = 'data:image/jpeg;base64,AA=='
    globalThis.uni = { getStorageSync: () => 'token-1' }
    globalThis.window = {
      webkit: {
        messageHandlers: {
          galacreditImagePicker: {
            postMessage: ({ callbackName }) => window[callbackName]?.({ images: [dataUrl, dataUrl] })
          }
        }
      }
    }
    globalThis.fetch = vi.fn(async (_url, options) => {
      expect(options.headers.Authorization).toBe('Bearer token-1')
      expect(options.body).toBeInstanceOf(FormData)
      return { status: 200, text: async () => JSON.stringify({ code: 200, msg: 'success' }) }
    })
    await expect(uploadIdentityImages('/user/ocr', { source: 'ios-fallback' })).resolves.toEqual({ code: 200, msg: 'success' })
    expect(fetch).toHaveBeenCalledTimes(1)
    delete globalThis.window
    delete globalThis.fetch
  })

  it('uses the iOS native image bridge for the single face image field', async () => {
    const dataUrl = 'data:image/jpeg;base64,AA=='
    globalThis.uni = { getStorageSync: () => 'token-1' }
    globalThis.window = {
      webkit: {
        messageHandlers: {
          galacreditImagePicker: {
            postMessage: ({ callbackName, count }) => {
              expect(count).toBe(1)
              window[callbackName]?.({ images: [dataUrl] })
            }
          }
        }
      }
    }
    globalThis.fetch = vi.fn(async (_url, options) => {
      expect([...options.body.keys()]).toContain('face_image')
      return { status: 200, text: async () => JSON.stringify({ code: 200, msg: 'success' }) }
    })
    await expect(uploadImage('/user/face-auth', { source: 'ios-fallback' }, 'face_image')).resolves.toEqual({ code: 200, msg: 'success' })
    expect(fetch).toHaveBeenCalledTimes(1)
    delete globalThis.window
    delete globalThis.fetch
    delete globalThis.uni
  })

  it('times out a native contact bridge that never returns', async () => {
    vi.useFakeTimers()
    globalThis.window = { GalaCreditContacts: { pick: vi.fn() } }
    const pending = chooseContact()
    const assertion = expect(pending).rejects.toThrow('Contact picker timed out')
    await vi.advanceTimersByTimeAsync(30000)
    await assertion
    vi.useRealTimers()
    delete globalThis.window
  })

  it('passes an abort signal to native-shell uploads', async () => {
    globalThis.uni = { getStorageSync: () => 'token-1' }
    globalThis.window = {
      webkit: {
        messageHandlers: {
          galacreditImagePicker: { postMessage: ({ callbackName }) => window[callbackName]?.({ images: ['data:image/jpeg;base64,AA=='] }) }
        }
      }
    }
    let requestOptions
    globalThis.fetch = vi.fn(async (_url, options) => {
      requestOptions = options
      return { status: 200, text: async () => JSON.stringify({ code: 200, msg: 'success' }) }
    })
    await uploadImage('/user/face-auth', { source: 'timeout-test' }, 'face_image')
    expect(requestOptions.signal).toBeDefined()
    delete globalThis.window
    delete globalThis.fetch
    delete globalThis.uni
  })
})
