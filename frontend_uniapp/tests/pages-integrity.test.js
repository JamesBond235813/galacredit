import { describe, expect, it } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const pages = JSON.parse(readFileSync(resolve(root, 'src/pages.json'), 'utf8')).pages

describe('UniApp route integrity', () => {
  it('has a Vue page file for every declared route', () => {
    expect(pages.length).toBeGreaterThan(0)
    for (const page of pages) {
      expect(existsSync(resolve(root, 'src', `${page.path}.vue`)), page.path).toBe(true)
    }
  })

  it('keeps the profile service shortcuts on the shared application flow', () => {
    const profile = readFileSync(resolve(root, 'src/pages/profile/index.vue'), 'utf8')
    expect(profile).toContain('applicationNextPage')
    expect(profile).toContain('openApplicationFlow')
    expect(profile).not.toContain('url="/pages/withdraw/index" class="service-item"')
    expect(profile).not.toContain('url="/pages/review/index" class="service-item"')
    expect(profile).not.toContain('url="/pages/bill/index" class="service-item"')
    expect(profile).toContain('Promise.allSettled')
  })

  it('lets previously verified users continue to emergency contacts', () => {
    const face = readFileSync(resolve(root, 'src/pages/face/index.vue'), 'utf8')
    expect(face).toContain("if (success.value) {")
    expect(face).toContain("/pages/application/index")
    expect(face).toContain('Continue Application')
    expect(face).not.toContain(':disabled="scanning || success"')
  })

  it('keeps back navigation on secondary pages and off root tab pages', () => {
    const expectedBackPages = ['about', 'agreement', 'application', 'bill', 'channel', 'face-mismatch', 'face', 'location', 'orders', 'password', 'personal-info-authorization', 'review', 'risk', 'support', 'verification', 'withdraw']
    const noBackPages = ['home', 'login', 'profile']
    for (const page of expectedBackPages) {
      const source = readFileSync(resolve(root, 'src/pages', page, 'index.vue'), 'utf8')
      expect(source).toContain('<PageHeader')
      expect(source).toContain(':back="true"')
    }
    for (const page of noBackPages) {
      const source = readFileSync(resolve(root, 'src/pages', page, 'index.vue'), 'utf8')
      expect(source).not.toContain('<PageHeader')
    }
  })

})
