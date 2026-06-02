import { describe, expect, it } from 'vitest'
import configFactory from '../../vite.config.js'

describe('vite gzip config', () => {
  it('should enable gzip compression plugin', () => {
    const config = configFactory({ mode: 'production' })
    const pluginNames = (config.plugins || []).map((plugin) => plugin?.name)

    expect(pluginNames).toContain('vite:compression')
  })
})
