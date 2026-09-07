import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(__dirname, '..')

describe('shared bottom navigation', () => {
  it('keeps app-plus and H5 labels and routes aligned', () => {
    const native = fs.readFileSync(path.join(root, 'src/components/BottomNav.vue'), 'utf8')
    const h5 = fs.readFileSync(path.join(root, 'src/App.h5.vue'), 'utf8')
    for (const label of ['GalaCredit', 'My Account']) {
      expect(native).toContain(`>${label}<`)
      expect(h5).toContain(`>${label}<`)
    }
    for (const route of ['pages/home/index', 'pages/profile/index']) {
      expect(native).toContain(`'${route}'`)
      expect(h5).toContain(`/pages/${route.split('/').slice(1).join('/')}`)
    }
    expect(native).not.toContain('>My Applications<')
    expect(h5).not.toContain('>My Applications<')
    expect(native).toContain('safe-area-inset-bottom')
    expect(h5).toContain('safe-area-inset-bottom')
  })
})
