import { describe, expect, it } from 'vitest'
import { ICON_PATHS } from './iconPaths.js'

describe('GalaCredit icon paths', () => {
  it('contains every icon used by shared navigation and home actions', () => {
    expect(Object.keys(ICON_PATHS)).toEqual(expect.arrayContaining([
      'home', 'applications', 'account', 'shield-check', 'plus', 'help', 'chevron-left', 'chevron-right'
    ]))
  })

  it('keeps paths non-empty so icons remain visible without a font fallback', () => {
    Object.values(ICON_PATHS).forEach((paths) => {
      expect(paths.length).toBeGreaterThan(0)
      paths.forEach((path) => expect(path).toMatch(/[A-Za-z]/))
    })
  })
})
