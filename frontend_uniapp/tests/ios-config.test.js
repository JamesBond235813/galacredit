import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(__dirname, '..')

describe('iOS app configuration', () => {
  it('declares privacy usage descriptions required by the shared UniApp flows', () => {
    const manifest = JSON.parse(fs.readFileSync(path.join(root, 'src/manifest.json'), 'utf8'))
    const privacy = manifest['app-plus'].distribute.ios.privacyDescription
    expect(privacy.NSCameraUsageDescription).toBeTruthy()
    expect(privacy.NSLocationWhenInUseUsageDescription).toBeTruthy()
    expect(privacy.NSPhotoLibraryUsageDescription).toBeTruthy()
    expect(privacy.NSContactsUsageDescription).toBeTruthy()
  })

  it('keeps iOS on the shared app-plus page graph', () => {
    const pages = JSON.parse(fs.readFileSync(path.join(root, 'src/pages.json'), 'utf8')).pages
    expect(pages.map((item) => item.path)).toContain('pages/home/index')
    expect(pages.map((item) => item.path)).toContain('pages/application/index')
    expect(pages.map((item) => item.path)).toContain('pages/verification/index')
    expect(pages.map((item) => item.path)).toContain('pages/face/index')
  })

  it('resizes shared app-plus pages when the iOS keyboard opens', () => {
    const config = JSON.parse(fs.readFileSync(path.join(root, 'src/pages.json'), 'utf8'))
    expect(config.globalStyle['app-plus'].softinputMode).toBe('adjustResize')
  })

  it('keeps checked-in root and source manifests aligned for iOS release settings', () => {
    const rootManifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'))
    const sourceManifest = JSON.parse(fs.readFileSync(path.join(root, 'src/manifest.json'), 'utf8'))
    expect(rootManifest.versionCode).toBe(sourceManifest.versionCode)
    expect(rootManifest.versionName).toBe(sourceManifest.versionName)
    expect(rootManifest['app-plus'].distribute.ios.privacyDescription)
      .toEqual(sourceManifest['app-plus'].distribute.ios.privacyDescription)
  })
})
