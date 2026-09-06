import { expect, it } from 'vitest'
import { loginFormLift } from '../src/utils/login-layout.js'
it('moves only enough to expose the button with a small gap', () => {
  expect(loginFormLift(615, 586)).toBe(37)
  expect(loginFormLift(578, 586, 37)).toBe(37)
})
it('restores the form after the keyboard closes and does not move an already visible button', () => {
  expect(loginFormLift(578, 960, 37)).toBe(0)
  expect(loginFormLift(500, 586)).toBe(0)
})
