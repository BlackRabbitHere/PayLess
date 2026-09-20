import { test, expect } from '@playwright/test'

test('connection screen reports Spring-to-scraper status and decimal-string mapping', async ({ page }) => {
  await page.route('**/api/v1/system/status', route => route.fulfill({
    json: { backend: 'UP', scraper: { status: 'UP', schemaVersion: 1, mode: 'fixture' } },
  }))
  await page.route('**/api/v1/optimization/scraper-check', async route => {
    expect(route.request().postDataJSON()).toEqual({ provider: 'GYFTR', merchant: 'SWIGGY' })
    await route.fulfill({ json: {
      requestId: 'test', status: 'SUCCESS', provider: 'GYFTR', merchant: 'SWIGGY', fixture: true,
      observations: [{ id: 'one', title: 'Swiggy Money Voucher', verificationStatus: 'VERIFIED',
        voucherFaceValue: '500.00', voucherSellingPrice: '487.50', discountValue: '2.50',
        maximumDiscount: null, sourceUrl: 'https://www.gyftr.com/swiggy-money', observedAt: '2026-09-18T16:30:00Z' }],
      warningCodes: ['FIXTURE_DATA'], errorCodes: [],
    } })
  })
  await page.goto('/system')
  await page.getByRole('button', { name: 'Check offer mapping' }).click()
  await expect(page.getByText('Spring Boot: UP')).toBeVisible()
  await expect(page.getByText('Voucher selling price: ₹487.50')).toBeVisible()
  await expect(page.getByText('Fixture data — no live commercial verification.')).toBeVisible()
})

test('connection screen displays upstream failures and can retry', async ({ page }) => {
  await page.route('**/api/v1/system/status', route => route.fulfill({
    status: 503, json: { detail: 'Scraper is unavailable or the request timed out.', code: 'SCRAPER_UNAVAILABLE' },
  }))
  await page.goto('/system')
  await page.getByRole('button', { name: 'Check connections', exact: true }).click()
  await expect(page.getByRole('alert')).toHaveText('We can’t check offers right now. Please try again shortly.')
  await expect(page.getByRole('button', { name: 'Check connections', exact: true })).toBeEnabled()
})
