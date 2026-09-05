import { describe, expect, it, vi } from 'vitest'
import * as api from './index.js'
import { normalizeContact } from '../utils/platform.js'
vi.mock('./request.js', () => ({ request: vi.fn((options) => Promise.resolve(options)) }))

describe('business api mapping', () => {
  it('maps verification and loan endpoints', async () => {
    globalThis.uni = { chooseImage: vi.fn(({ success }) => success({ tempFilePaths: ['/tmp/front.jpg', '/tmp/back.jpg'] })), uploadFiles: vi.fn(({ success }) => success({ data: '{}' })), uploadFile: vi.fn(({ success }) => success({ data: '{}' })), getStorageSync: () => 'token' }
    expect((await api.submitOCR({ a: 1 }))).toEqual({})
    expect((await api.submitFaceAuth({ a: 1 }))).toEqual({})
    expect((await api.submitApplication({ amount: 10 })).url).toBe('/user/application')
    expect((await api.submitWithdraw({ amount: 10 })).url).toBe('/loan/withdraw')
    expect((await api.changePassword({})).url).toBe('/user/change-password')
    expect((await api.requestRepayment({})).url).toBe('/loan/repay-attempt')
    expect((await api.applyLimit()).url).toBe('/loan/apply')
    expect((await api.previewPurchaseContract({})).url).toBe('/loan/purchase-contract/preview')
    expect((await api.signPurchaseContract({})).url).toBe('/loan/purchase-contract/sign')
    expect((await api.sendOrderSmsCode()).url).toBe('/loan/order-sms-code')
    expect((await api.getLoanStatus()).url).toBe('/loan/status')
    expect((await api.createSliderCaptcha({})).url).toBe('/auth/slider-captcha/create')
    expect((await api.verifySliderCaptcha({})).url).toBe('/auth/slider-captcha/verify')
  })

  it('normalizes a single selected contact to minimal fields', () => {
    expect(normalizeContact('  Ama Mensah ', '+233 20-123-4567')).toEqual({ name: 'Ama Mensah', phone: '+233201234567' })
    expect(normalizeContact('', '233201234567')).toBeNull()
  })
})
