import { describe, expect, it } from 'vitest'
import { applicationNextPage, needsApplicationStart } from './application-flow.js'

describe('application flow', () => {
  it('uses one entry point for new and resubmitted applications', () => {
    expect(applicationNextPage('INIT')).toBe('/pages/verification/index')
    expect(applicationNextPage('REJECTED')).toBe('/pages/verification/index')
    expect(applicationNextPage('SETTLED')).toBe('/pages/verification/index')
    expect(needsApplicationStart('INIT')).toBe(true)
  })

  it('keeps review, withdrawal and repayment routes consistent', () => {
    expect(applicationNextPage('REVIEWING')).toBe('/pages/review/index')
    expect(applicationNextPage('APPROVED')).toBe('/pages/withdraw/index')
    expect(applicationNextPage('DISBURSED')).toBe('/pages/bill/index')
    expect(applicationNextPage('UNKNOWN')).toBe('/pages/home/index')
  })
})
