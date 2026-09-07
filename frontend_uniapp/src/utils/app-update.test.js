import { describe, expect, it } from 'vitest'
import { shouldUpdate } from './app-update.js'

describe('app update version comparison', () => {
  it('only updates when the remote versionCode is higher', () => {
    expect(shouldUpdate(104, 105)).toBe(true)
    expect(shouldUpdate(104, 104)).toBe(false)
    expect(shouldUpdate(105, 104)).toBe(false)
  })
})
