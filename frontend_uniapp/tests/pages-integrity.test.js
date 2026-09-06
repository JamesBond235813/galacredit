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

})
