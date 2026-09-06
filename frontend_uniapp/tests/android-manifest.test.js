import { readFileSync } from 'node:fs'
import { expect, it } from 'vitest'

it('keeps the IDE and CLI manifests aligned for signed Android packaging', () => {
  const root = JSON.parse(readFileSync(new URL('../manifest.json', import.meta.url), 'utf8'))
  const src = JSON.parse(readFileSync(new URL('../src/manifest.json', import.meta.url), 'utf8'))
  expect(root.appid).toBe(src.appid)
  expect(root.appid).not.toBe('__UNI__GALACREDIT')
  expect(root.versionCode).toBe(src.versionCode)
  for (const manifest of [root, src]) {
    const android = manifest['app-plus'].distribute.android
    expect(android.packagename).toBe('com.galacredit.app')
    for (const permission of android.permissions) {
      expect(permission).toMatch(/^<uses-permission android:name="android\.permission\.[A-Z_]+"\s*\/>$/)
    }
  }
})

it('resizes the login webview so the compact layout can keep the button above the keyboard', () => {
  const config = JSON.parse(readFileSync(new URL('../src/pages.json', import.meta.url), 'utf8'))
  const login = config.pages.find(page => page.path === 'pages/login/index')
  expect(login.style['app-plus'].softinputMode).toBe('adjustResize')
})
