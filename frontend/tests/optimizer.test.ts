import { test } from 'node:test'
import assert from 'node:assert/strict'
import { defaultPurchase, swiggyPurchase } from '../src/features/travel/model/demoFlights'
import { demoWallet } from '../src/features/wallet/model/demoWallet'
import { optimize, recommendedRoutes } from '../src/features/optimization/model/demoOptimizer'
import { money } from '../src/features/optimization/model/presentation'

test('higher listed fare wins the default flight demo with explicit checkout and later rewards', () => {
  const routes = optimize(defaultPurchase, demoWallet)
  const winner = recommendedRoutes(routes)[0]
  const cheapestListed = routes.filter(route => !route.offer).sort((a, b) => a.base - b.base)[0]
  assert.equal(cheapestListed.merchant, 'EaseMyTrip')
  assert.equal(winner.merchant, 'Yatra')
  assert.equal(winner.payNow, 4988)
  assert.equal(winner.rewards, 80)
  assert.equal(winner.effective, 4908)
  assert.equal(winner.savings, 742)
  assert.equal(recommendedRoutes(routes, 'pay-now')[0].merchant, 'Cleartrip')
  assert.equal(recommendedRoutes(routes, 'rewards')[0].merchant, 'ixigo')
})

test('wallet selection changes eligibility and recommendations', () => {
  const routes = optimize(defaultPurchase, demoWallet.map(product => ({ ...product, selected: product.id === 'upi' })))
  assert.equal(recommendedRoutes(routes)[0].merchant, 'EaseMyTrip')
  assert.equal(recommendedRoutes(routes)[0].payNow, 5459)
  assert.equal(routes.find(route => route.id === 'yatra-icici')?.eligible, false)
  assert.ok(recommendedRoutes(routes).every(route => !route.offer))
})

test('Swiggy voucher savings are immediate and retain paise precision', () => {
  const routes = optimize(swiggyPurchase, demoWallet)
  const winner = recommendedRoutes(routes)[0]
  assert.equal(winner.id, 'swiggy-voucher')
  assert.equal(winner.base, 500)
  assert.equal(winner.payNow, 487.5)
  assert.equal(winner.effective, 487.5)
  assert.equal(winner.savings, 12.5)
  const hdfc = routes.find(route => route.id === 'swiggy-hdfc')!
  assert.equal(hdfc.payNow, 500)
  assert.equal(hdfc.rewards, 5)
  assert.equal(hdfc.effective, 495)
})

test('deferred cashback never reduces Pay Now; highest reward route can differ', () => {
  const routes = optimize(swiggyPurchase, demoWallet.map(product => ({ ...product, selected: true })))
  assert.equal(recommendedRoutes(routes)[0].id, 'swiggy-sbi')
  assert.equal(recommendedRoutes(routes)[0].payNow, 500)
  assert.equal(recommendedRoutes(routes)[0].effective, 475)
  assert.equal(recommendedRoutes(routes, 'pay-now')[0].id, 'swiggy-voucher')
})

test('caps, booking amount, voucher limits, dates, and all monetary identities are respected', () => {
  const capped = optimize({ ...defaultPurchase, passengers: 6 }, demoWallet).find(route => route.id === 'yatra-icici')!
  assert.equal(capped.base, 33120)
  assert.equal(capped.discount, 1000)
  assert.equal(optimize({ ...defaultPurchase, departure: '2027-01-01' }, demoWallet).find(route => route.id === 'yatra-icici')?.eligible, false)
  assert.equal(optimize({ ...swiggyPurchase, amount: 99 }, demoWallet).find(route => route.id === 'swiggy-voucher')?.eligible, false)
  assert.equal(optimize({ ...swiggyPurchase, amount: 1001 }, demoWallet).find(route => route.id === 'swiggy-voucher')?.eligible, false)
  for (const purchase of [defaultPurchase, swiggyPurchase, { ...swiggyPurchase, amount: 333.33 }]) {
    for (const route of optimize(purchase, demoWallet)) {
      const round = (n: number) => Math.round(n * 100) / 100
      assert.equal(route.payNow, round(route.base + route.fees - route.discount))
      assert.equal(route.effective, round(route.payNow - route.rewards))
      assert.equal(route.savings, round(route.base + route.fees - route.effective))
    }
  }
})

test('ambiguous and stale sources never win; fallback remains available', () => {
  for (const scenario of ['normal', 'no-offer', 'stale', 'ambiguous'] as const) {
    const routes = optimize(defaultPurchase, demoWallet, scenario)
    assert.ok(recommendedRoutes(routes).length > 0)
    assert.ok(recommendedRoutes(routes).every(route => route.eligible && !route.stale && route.status !== 'AMBIGUOUS'))
    if (scenario !== 'normal') assert.ok(recommendedRoutes(routes).every(route => !route.offer))
  }
  for (const purchase of [defaultPurchase, swiggyPurchase]) {
    const routes = optimize(purchase, [])
    assert.ok(recommendedRoutes(routes).length > 0)
    assert.ok(recommendedRoutes(routes).every(route => !route.offer))
  }
})

test('Indian currency formatting retains decimal precision only when needed', () => {
  assert.equal(money(100000), '₹1,00,000')
  assert.equal(money(487.5), '₹487.50')
})

test('other merchants never receive Swiggy offers or unsearched flight offers', () => {
  for (const merchant of ['Zomato', 'Myntra', 'Yatra', 'ixigo', 'EaseMyTrip', 'Cleartrip', 'MakeMyTrip']) {
    const routes = optimize({ ...swiggyPurchase, merchant, amount: 1000 }, demoWallet)
    assert.ok(routes.every(route => route.merchant === merchant && !route.offer))
    assert.equal(recommendedRoutes(routes)[0].payNow, 1000)
    assert.equal(recommendedRoutes(routes)[0].savings, 0)
  }
})
