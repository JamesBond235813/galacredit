import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const source = fs.readFileSync(path.resolve(import.meta.dirname, '../src/pages/login/index.vue'), 'utf8')

describe('login slider interaction contract', () => {
  it('keeps drag events captured and frame-synchronised across mobile webviews', () => {
    expect(source).toContain('setPointerCapture')
    expect(source).toContain('releasePointerCapture')
    expect(source).toContain('requestAnimationFrame')
    expect(source).toContain('@touchcancel.stop.prevent')
    expect(source).toContain('touch-action:none')
  })
})
