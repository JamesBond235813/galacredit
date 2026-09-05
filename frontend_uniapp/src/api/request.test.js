import { describe, expect, it, vi } from 'vitest'
import { request } from './request.js'

describe('uniapp request adapter', () => {
  it('adds client id and bearer token', async () => {
    globalThis.uni = { getStorageSync: () => 'token-1', request: vi.fn(({ success }) => success({ data: { code: 0 }, statusCode: 200 })) }
    await expect(request({ url: '/user/info' })).resolves.toEqual({ code: 0 })
    expect(uni.request).toHaveBeenCalledWith(expect.objectContaining({ header: expect.objectContaining({ Authorization: 'Bearer token-1', 'client-id': 'uniapp' }) }))
  })

  it('retries transient GET failures but does not retry POST by default', async () => {
    vi.useFakeTimers()
    let calls = 0
    globalThis.uni = { getStorageSync: () => '', request: vi.fn(({ success }) => { calls += 1; success({ data: calls === 1 ? {} : { code: 0 }, statusCode: calls === 1 ? 503 : 200 }) }) }
    const result = request({ url: '/user/info', method: 'GET' })
    await vi.advanceTimersByTimeAsync(300)
    await expect(result).resolves.toEqual({ code: 0 })
    expect(calls).toBe(2)

    let postCalls = 0
    globalThis.uni.request = vi.fn(({ fail }) => { postCalls += 1; fail(new Error('offline')) })
    await expect(request({ url: '/user/application', method: 'POST' })).rejects.toThrow('offline')
    expect(postCalls).toBe(1)
    vi.useRealTimers()
  })
})
