import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { RouteCard } from '../../src/features/optimization/view/ResultsPage'
import type { OptimizeResponse, PaymentRoute } from '../../src/features/optimization/model/contracts'

const route: PaymentRoute = {
  id: 'deferred-example', kind: 'DIRECT', paymentInstrument: { issuer: 'HDFC', productName: 'HDFC Millennia Credit Card', instrumentType: 'CREDIT_CARD', network: 'VISA' },
  cost: { originalAmount: 500, eligibleAmount: 500, immediateDiscount: 0, payNow: 500, deferredReward: 25, effectiveCost: 475, saving: 25, remainingPayment: 0 },
  complexity: 1, verificationConfidence: 1, warnings: [],
  sources: [{ externalKey: 'offer', provider: 'GYFTR', sourceUrl: 'https://www.gyftr.com/', verificationStatus: 'STALE', lastVerifiedAt: null, observedAt: '2026-09-18T00:00:00Z', contentHash: 'test', fixture: false, terms: ['Rewards arrive later.'] }],
  steps: [{ number: 1, instruction: 'Open the merchant and confirm your purchase.', actionLabel: 'Open SWIGGY', actionUrl: 'https://www.swiggy.com/' }],
}
const response: OptimizeResponse = {
  context: { merchant: 'SWIGGY', category: 'FOOD_DELIVERY', amount: 500, confidence: 1 }, currency: 'INR',
  bestEffectiveCostRoute: route, bestPayNowRoute: route, alternatives: [], eligibility: [], sources: [], warnings: [],
}

describe('route presentation', () => {
  it('keeps deferred rewards separate from the exact checkout amount and shows uncertainty', () => {
    render(<RouteCard route={route} response={response} best />)
    expect(screen.getByTestId('best-pay-now')).toHaveTextContent('₹500')
    expect(screen.getByTestId('best-effective')).toHaveTextContent('₹475')
    expect(screen.getByText(/Expected effective cost includes ₹25 in deferred rewards/)).toHaveTextContent('You still pay ₹500 at checkout')
    expect(screen.getByText(/stale/)).toBeVisible()
    expect(screen.getByText('Last checked: Not supplied')).toBeVisible()
    expect(screen.getByRole('link', { name: /Continue to Swiggy/ })).toHaveAttribute('href', 'https://www.swiggy.com/')
  })

  it('never implies later rewards for an immediate-only route', () => {
    const immediate = { ...route, cost: { ...route.cost, immediateDiscount: 25, payNow: 475, deferredReward: 0 } }
    render(<RouteCard route={immediate} response={response} best />)
    expect(screen.getByTestId('best-pay-now')).toHaveTextContent('₹475')
    expect(screen.getByText(/No deferred rewards are included/)).toBeVisible()
  })
})
