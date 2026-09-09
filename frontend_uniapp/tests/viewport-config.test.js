import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(__dirname, '..')

describe('mobile viewport behavior', () => {
  it('disables browser and native WebView zoom', () => {
    const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8')
    const app = fs.readFileSync(path.join(root, 'src/App.vue'), 'utf8')
    const main = fs.readFileSync(path.join(root, 'src/main.h5.js'), 'utf8')
    expect(html).toContain('user-scalable=no')
    expect(main).toContain('maximum-scale=1.0')
    expect(app).toContain('scalable: false')
  })
})
