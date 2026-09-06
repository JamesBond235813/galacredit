import { afterEach, expect, it, vi } from 'vitest'
import { uploadIdentityImages } from '../src/utils/platform.js'

afterEach(() => vi.unstubAllGlobals())

it('uploads the front and newly captured back after two camera selections', async () => {
  const addFile = vi.fn()
  let complete
  const task = {
    addFile, addData: vi.fn(), setRequestHeader: vi.fn(),
    start: () => complete({ responseText: '{"code":200}' }, 200),
  }
  vi.stubGlobal('window', undefined)
  vi.stubGlobal('plus', { uploader: { createUpload: (_url, _options, callback) => { complete = callback; return task } } })
  const chooseImage = vi.fn()
    .mockImplementationOnce(({ success }) => success({ tempFilePaths: ['front.jpg'] }))
    .mockImplementationOnce(({ success }) => success({ tempFilePaths: ['back.jpg'] }))
  vi.stubGlobal('uni', { chooseImage, getStorageSync: () => 'test-session' })
  await expect(uploadIdentityImages('/user/ocr')).resolves.toEqual({ code: 200 })
  expect(addFile.mock.calls).toEqual([
    ['front.jpg', { key: 'front_image' }], ['back.jpg', { key: 'back_image' }],
  ])
})

it('does not upload when the back capture is cancelled', async () => {
  const createUpload = vi.fn()
  vi.stubGlobal('window', undefined)
  vi.stubGlobal('plus', { uploader: { createUpload } })
  const chooseImage = vi.fn()
    .mockImplementationOnce(({ success }) => success({ tempFilePaths: ['front.jpg'] }))
    .mockImplementationOnce(({ fail }) => fail(new Error('cancelled')))
  vi.stubGlobal('uni', { chooseImage })
  await expect(uploadIdentityImages('/user/ocr')).rejects.toThrow('cancelled')
  expect(createUpload).not.toHaveBeenCalled()
})
