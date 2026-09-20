import { render, screen } from '@testing-library/react'
import { it, expect } from 'vitest'
import { ExternalAction } from '../../src/features/optimization/view/ExternalAction'
it('opens approved provider links safely', () => {
  render(<ExternalAction url="https://www.gyftr.com/swiggy-money" label="Buy voucher" />)
  expect(screen.getByRole('link')).toHaveAttribute('rel', 'noopener noreferrer')
  expect(screen.getByRole('link')).toHaveAttribute('target', '_blank')
})
it('renders untrusted destinations as disabled actions', () => {
  render(<ExternalAction url="https://evil.example" label="Buy voucher" />)
  expect(screen.queryByRole('link')).toBeNull()
  expect(screen.getByRole('button')).toBeDisabled()
})
