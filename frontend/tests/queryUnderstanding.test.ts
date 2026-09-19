import { test } from 'node:test'
import assert from 'node:assert/strict'
import { normalizeQuery, understandQuery } from '../src/features/query/model/queryUnderstanding'

test('the requested natural-language journey preserves exact purchase details', () => {
  for (const text of ["I'm ordering food on swigy and it costs 500 rs", 'I am ordering food on swigy and it costs 500 rs', 'I am spending 500 rs on swigy', 'I am ordering food on Swiggy and it is costing ₹500. Can I reduce this cost?']) {
    const parsed = understandQuery(text)
    assert.equal(parsed.intent, 'OPTIMIZE_PURCHASE')
    assert.equal(parsed.merchant, 'SWIGGY')
    assert.equal(parsed.amount, 500)
    assert.equal(parsed.category, 'FOOD_DELIVERY')
    assert.deepEqual(parsed.missingFields, [])
  }
})

test('all Indian currency notations and paise are extracted without rounding', () => {
  for (const text of ['₹500', 'Rs 500', 'Rs. 500', '500 rs', '500 rupees', 'INR 500', '500 INR', '500rs', 'Rs.500', '₹５００']) {
    assert.equal(understandQuery(`${text} on Swiggy`).amount, 500, text)
  }
  for (const text of ['₹1,000', '1000 INR', 'Rs. 1,000.00']) assert.equal(understandQuery(`${text} Myntra`).amount, 1000)
  assert.equal(understandQuery('₹1,00,000 on Myntra').amount, 100000)
  assert.equal(understandQuery('₹500.75 on Swiggy').amount, 500.75)
  assert.equal(understandQuery('I am spending 500 on Swiggy').amount, 500)
})

test('missing values never inherit old defaults', () => {
  assert.deepEqual(understandQuery('Can I save on Swiggy?').missingFields, ['amount'])
  assert.equal(understandQuery('Can I save on Swiggy?').amount, null)
  assert.deepEqual(understandQuery('How can I save on ₹500?').missingFields, ['merchant'])
  assert.equal(understandQuery('How can I pay less for Zomato?').amount, null)
  assert.deepEqual(understandQuery('').missingFields, ['merchant', 'amount'])
})

test('controlled aliases and merchant-first categories work for the entire catalogue', () => {
  for (const alias of ['swiggy', 'swigy', 'swigi', 'swiggi', 'SWIGGY']) assert.equal(understandQuery(`₹500 on ${alias}`).merchant, 'SWIGGY')
  for (const [alias, id] of [['zomatto', 'ZOMATO'], ['mintra', 'MYNTRA'], ['ixigo', 'IXIGO'], ['yathra', 'YATRA'], ['ease my trip', 'EASEMYTRIP'], ['clear trip', 'CLEARTRIP'], ['make my trip', 'MAKEMYTRIP'], ['MMT', 'MAKEMYTRIP']]) assert.equal(understandQuery(`₹500 on ${alias}`).merchant, id)
  assert.equal(understandQuery('Can I save on a ₹1000 Myntra order?').category, 'FASHION')
  assert.equal(understandQuery('₹500 food on Myntra').category, 'FASHION')
  assert.equal(understandQuery('₹500 flight').category, 'TRAVEL')
  assert.equal(understandQuery('₹500 dinner').category, 'FOOD_DELIVERY')
})

test('fuzzy matching is restricted by position, edit distance, prefix and confidence', () => {
  const fuzzy = understandQuery('I am spending ₹500 on swiggyy')
  assert.equal(fuzzy.merchant, 'SWIGGY')
  assert.ok(fuzzy.confidence >= 0.8 && fuzzy.confidence < 1)
  for (const text of ['₹500 on randomstore', '₹500 on swg', '₹500 on attra', 'I saw a swiggyy sign while walking home and spent ₹500', '₹500 on notswiggy', '₹500 on zomatoworld']) assert.equal(understandQuery(text).merchant, null, text)
  assert.equal(normalizeQuery('  I’M   buying on SWIGGY  '), "i'm buying on swiggy")
})

test('ambiguous and malformed amounts require clarification instead of approximate math', () => {
  for (const value of ['₹1,00', '₹1,0000', '₹500.123', '₹500.00.2', '₹-500', '-₹500', '₹0', '₹100001', '₹1e3', '₹1k']) {
    assert.equal(understandQuery(`${value} on Swiggy`).amount, null, value)
  }
  const multiple = understandQuery('₹500 order on Swiggy plus ₹30 delivery')
  assert.equal(multiple.amount, null)
  assert.ok(multiple.issues.length)
  assert.equal(understandQuery('₹500 on Swiggy or Zomato').merchant, null)
  assert.equal(understandQuery('2 meals on Swiggy tomorrow').amount, null)
  assert.equal(understandQuery('₹500 on Swiggy, order total 500 rupees').amount, 500)
})
