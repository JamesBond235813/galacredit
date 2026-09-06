import { afterEach, describe, expect, it } from 'vitest'
import config from '../vite.config.js'

const platform = process.env.UNI_PLATFORM
afterEach(() => {
  if (platform === undefined) delete process.env.UNI_PLATFORM
  else process.env.UNI_PLATFORM = platform
})

describe('build platform selection', () => {
  it('keeps the existing browser compiler for the H5 entry', async () => {
    delete process.env.UNI_PLATFORM
    const result = await config({ command: 'build' })
    expect(result.plugins.some((plugin) => plugin.name === 'galacredit-rpx-fallback')).toBe(true)
  })
  it('uses the native compiler and inlines IIFE dynamic modules for app-plus', async () => {
    process.env.UNI_PLATFORM = 'app-plus'
    const result = await config({ command: 'build' })
    expect(result.plugins.some((plugin) => plugin.name === 'galacredit-rpx-fallback')).toBe(false)
    const plugin = result.plugins.find((item) => item.name === 'galacredit-app-single-bundle')
    expect(plugin.outputOptions({ format: 'iife', inlineDynamicImports: false, manualChunks: {} })).toEqual({
      format: 'iife', inlineDynamicImports: true, manualChunks: undefined,
    })
  })
})
