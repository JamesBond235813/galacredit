import { describe, expect, it } from 'vitest'
import { canVerifySlider } from './captcha.js'

describe('slider captcha guard', () => {
  it('only allows one completed visible challenge to submit', () => {
    expect(canVerifySlider(99)).toBe(false)
    expect(canVerifySlider(100)).toBe(true)
    expect(canVerifySlider(100, { busy: true })).toBe(false)
    expect(canVerifySlider(100, { visible: false })).toBe(false)
    expect(canVerifySlider(100, { submitted: true })).toBe(false)
    expect(canVerifySlider(100, { hasCaptcha: false })).toBe(false)
  })
})
