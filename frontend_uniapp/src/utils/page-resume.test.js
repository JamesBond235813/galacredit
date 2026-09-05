import { describe, expect, it, vi } from 'vitest'
import { createResumeRunner } from './page-resume.js'

describe('page resume runner', () => {
  it('deduplicates concurrent resume events', async () => {
    let release
    const pending = new Promise((resolve) => { release = resolve })
    const callback = vi.fn(() => pending)
    const runner = createResumeRunner(callback)

    const first = runner.run()
    const second = runner.run()
    expect(await second).toBe(false)
    expect(callback).toHaveBeenCalledTimes(1)
    release()
    expect(await first).toBe(true)
  })

  it('does not run after disposal', async () => {
    const callback = vi.fn()
    const runner = createResumeRunner(callback)
    runner.dispose()

    expect(await runner.run()).toBe(false)
    expect(callback).not.toHaveBeenCalled()
  })

  it('coalesces native and visibility resume events arriving together', async () => {
    let now = 1000
    const callback = vi.fn()
    const runner = createResumeRunner(callback, { minIntervalMs: 500, now: () => now })

    expect(await runner.run()).toBe(true)
    now = 1200
    expect(await runner.run()).toBe(false)
    now = 1600
    expect(await runner.run()).toBe(true)
    expect(callback).toHaveBeenCalledTimes(2)
  })
})
