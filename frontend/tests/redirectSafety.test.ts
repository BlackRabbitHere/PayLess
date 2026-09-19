import { test } from 'node:test'
import assert from 'node:assert/strict'
import { isAllowedRedirect } from '../src/features/redirect/model/redirectSafety'
import { demoOffers } from '../src/features/optimization/model/demoOffers'
import { defaultPurchase, swiggyPurchase } from '../src/features/travel/model/demoFlights'
import { demoWallet } from '../src/features/wallet/model/demoWallet'
import { optimize, recommendedRoutes } from '../src/features/optimization/model/demoOptimizer'

test('redirects allow only HTTPS and exact approved provider hosts', () => {
  for (const url of ['https://swiggy.com/', 'https://www.swiggy.com/', 'https://WWW.YATRA.COM/', 'https://www.gyftr.com/', 'https://www.myntra.com/']) assert.ok(isAllowedRedirect(url), url)
  for (const url of [undefined, '', 'javascript:alert(1)', 'data:text/html,x', 'http://swiggy.com', '//swiggy.com', '/swiggy.com', 'https://swiggy.com.evil.test', 'https://swiggy-com.test', 'https://evil.test/swiggy.com', 'https://swiggy.com@evil.test', 'https://evil.test@swiggy.com', 'https://login.swiggy.com', 'https://swiggу.com', 'https://swiggy.com:1234', 'https://swiggy.com./', 'https://swiggy.com\\@evil.test', 'https://swiggy.com\n.evil.test']) assert.equal(isAllowedRedirect(url), false, String(url))
})

test('all fixtures supply distinct provenance metadata and safe step actions', () => {
  for (const offer of demoOffers) {
    assert.ok(isAllowedRedirect(offer.sourceUrl))
    assert.ok(isAllowedRedirect(offer.actionUrl))
    assert.ok(offer.lastVerifiedAt)
    assert.ok(offer.actionLabel)
  }
  for (const purchase of [defaultPurchase, swiggyPurchase]) {
    for (const route of optimize(purchase, demoWallet)) {
      assert.ok(isAllowedRedirect(route.sourceUrl))
      assert.deepEqual(route.steps.map(step => step.order), route.steps.map((_, index) => index + 1))
      assert.ok(route.steps.every(step => step.provider && step.description))
      assert.ok(route.steps.filter(step => step.actionUrl).every(step => isAllowedRedirect(step.actionUrl) && step.actionLabel))
    }
  }
  const voucher = recommendedRoutes(optimize(swiggyPurchase, demoWallet))[0]
  assert.equal(voucher.steps.length, 2)
  assert.equal(voucher.steps[0].amount, 487.5)
  assert.equal(voucher.steps[1].amount, 500)
  assert.notEqual(voucher.sourceUrl, voucher.steps[0].actionUrl)
  assert.equal(voucher.steps[0].actionLabel, 'Buy Voucher')
  assert.equal(voucher.steps[1].actionLabel, 'Open Swiggy')
})
