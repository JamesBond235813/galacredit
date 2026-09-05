import { afterEach, describe, expect, it, vi } from 'vitest'
import { installmentStatusLabel, loanStatusLabel, riskTaskStatusLabel, signOut, verificationStatusLabel } from './app.js'

describe('session sign out', () => {
  afterEach(() => {
    delete globalThis.uni
    delete globalThis.window
  })

  it('notifies a native shell so its secure session is cleared too', () => {
    const postMessage = vi.fn()
    globalThis.window = { webkit: { messageHandlers: { galacreditLogout: { postMessage } } } }
    globalThis.uni = {
      setStorageSync: vi.fn(),
      removeStorageSync: vi.fn(),
      reLaunch: vi.fn()
    }

    signOut()

    expect(postMessage).toHaveBeenCalledWith({})
    expect(uni.removeStorageSync).toHaveBeenCalledWith('token')
    expect(uni.removeStorageSync).toHaveBeenCalledWith('galacredit_risk_task')
    expect(uni.reLaunch).toHaveBeenCalledWith({ url: '/pages/login/index' })
  })
})

describe('user-facing status labels', () => {
  it('does not expose backend enum values in the primary status cards', () => {
    expect(loanStatusLabel('REVIEWING')).toBe('Application under review')
    expect(riskTaskStatusLabel('2')).toBe('Completed')
    expect(riskTaskStatusLabel('unknown')).toBe('Pending')
    expect(verificationStatusLabel('REJECTED')).toBe('Needs an update')
    expect(installmentStatusLabel('PAID')).toBe('Paid')
  })
})
