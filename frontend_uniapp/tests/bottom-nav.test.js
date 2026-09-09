import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(__dirname, '..')

describe('shared bottom navigation', () => {
  it('keeps app-plus and H5 labels and routes aligned', () => {
    const native = fs.readFileSync(path.join(root, 'src/components/BottomNav.vue'), 'utf8')
    const h5 = fs.readFileSync(path.join(root, 'src/App.h5.vue'), 'utf8')
    const pages = JSON.parse(fs.readFileSync(path.join(root, 'src/pages.json'), 'utf8'))
    for (const label of ['GalaCredit', 'My Account']) {
      expect(native).toContain(`>${label}<`)
    }
    for (const route of ['pages/home/index', 'pages/profile/index']) {
      expect(native).toContain(`'${route}'`)
    }
    expect(native).not.toContain('>My Applications<')
    expect(h5).not.toContain('>My Applications<')
    expect(native).toContain('safe-area-inset-bottom')
    expect(native).toContain('border-radius:34px')
    expect(native).toContain('use-vant')
    expect(h5).toContain('BottomNav')
    expect(pages.tabBar.list).toHaveLength(2)
    expect(pages.tabBar.list.map((item) => item.pagePath)).toEqual(['pages/home/index', 'pages/profile/index'])
  })
})
