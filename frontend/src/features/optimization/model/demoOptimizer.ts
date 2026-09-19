import { money, purchaseLabel, dateLabel } from './presentation'
import { demoFlights, fixtureVerifiedDate } from '../../travel/model/demoFlights'
import { demoOffers } from './demoOffers'
import { providerUrls } from '../../../app/config/providers'
import type { PaymentRoute, Purchase, RouteStep, Scenario, Sort, WalletProduct } from './types'

const round = (value: number) => Math.round((value + Number.EPSILON) * 100) / 100

export function optimize(purchase: Purchase, wallet: WalletProduct[], scenario: Scenario = 'normal'): PaymentRoute[] {
  const selected = wallet.filter(product => product.selected)
  const direct = selected.find(product => product.type === 'UPI') ?? selected[0]
  const merchants = purchase.mode === 'travel' ? demoFlights.map(flight => ({ ...flight, base: flight.base * purchase.passengers })) : [{ merchant: purchase.merchant, base: purchase.amount, fees: 0, color: purchase.merchant === 'Swiggy' ? '#ee7b2b' : '#4940d4' }]
  const routes: Omit<PaymentRoute, 'steps'>[] = merchants.map(merchant => ({
    id: `${merchant.merchant}-direct`, merchant: merchant.merchant, merchantColor: merchant.color,
    productId: direct?.id, paymentName: direct?.name ?? 'Direct payment', paymentIssuer: direct?.issuer ?? 'Choose at checkout', paymentType: direct?.type ?? 'Direct',
    base: merchant.base, fees: merchant.fees, discount: 0, payNow: round(merchant.base + merchant.fees), rewards: 0,
    effective: round(merchant.base + merchant.fees), savings: 0, eligible: true, recommended: true, stale: false,
    status: 'DEMO', rules: [{ label: 'No promotional eligibility required', passes: true }], isVoucher: false,
    sourceUrl: providerUrls[merchant.merchant] ?? '', lastVerifiedAt: fixtureVerifiedDate,
  }))

  const matchingOffers = demoOffers.filter(offer => offer.mode === purchase.mode && merchants.some(merchant => merchant.merchant === (offer.purchaseMerchant ?? offer.merchant)))
  for (const offer of matchingOffers) {
    const isVoucher = offer.kind === 'Voucher'
    const merchant = merchants.find(item => item.merchant === offer.merchant) ?? (isVoucher ? { ...merchants[0], merchant: 'Swiggy Money', color: '#ee7b2b' } : undefined)
    if (!merchant) continue
    const product = offer.productId === 'any' ? direct : wallet.find(item => item.id === offer.productId)
    const selectedProduct = offer.productId === 'any' ? selected.length > 0 : !!product?.selected
    const validDate = purchase.mode !== 'travel' || (purchase.departure >= offer.validFrom && purchase.departure <= offer.validUntil)
    const rules = [
      { label: `Merchant = ${merchant.merchant}`, passes: true },
      { label: `${product?.name ?? (offer.productId === 'any' ? 'A payment product' : 'Required payment product')} selected`, passes: selectedProduct },
      { label: `Eligible amount ${money(merchant.base)} ${offer.minimum ? `≥ ${money(offer.minimum)}` : 'meets the minimum'}`, passes: merchant.base >= offer.minimum },
      { label: isVoucher ? 'Voucher value is between ₹100 and ₹1,000' : 'Offer valid for selected demo date', passes: isVoucher ? merchant.base <= 1000 : validDate },
      { label: 'Non-EMI transaction eligible', passes: offer.status !== 'AMBIGUOUS' },
    ]
    if (scenario === 'no-offer') rules.push({ label: 'No special offers available in this demo state', passes: false })
    if (scenario === 'ambiguous') rules.push({ label: 'Source conditions agree', passes: false })
    const eligible = rules.every(rule => rule.passes)
    // Flight instant discounts use whole rupees in this fictional offer's terms.
    const discount = isVoucher ? round(Math.min(merchant.base * offer.rate, offer.cap)) : Math.floor(Math.min(merchant.base * offer.rate, offer.cap))
    const payNow = round(merchant.base + merchant.fees - discount)
    const rewards = round(offer.rewardKind === 'percentage' ? Math.min(payNow * offer.reward, 500) : offer.reward)
    const stale = scenario === 'stale'
    const status = scenario === 'ambiguous' ? 'AMBIGUOUS' : offer.status
    routes.push({
      id: offer.id, merchant: merchant.merchant, merchantColor: merchant.color,
      productId: product?.id, paymentName: product?.name ?? 'Select a payment product', paymentIssuer: product?.issuer ?? 'Wallet', paymentType: product?.type ?? 'Unselected',
      base: merchant.base, fees: merchant.fees, discount, payNow, rewards, effective: round(payNow - rewards),
      savings: round(discount + rewards), eligible, recommended: eligible && !stale && status !== 'AMBIGUOUS',
      stale, status, offer, rules, isVoucher,
      sourceUrl: offer.sourceUrl, lastVerifiedAt: stale ? '2026-08-01' : offer.lastVerifiedAt,
    })
  }
  return routes.map(route => ({ ...route, steps: buildRouteSteps(route, purchase) }))
}

function buildRouteSteps(route: Omit<PaymentRoute, 'steps'>, purchase: Purchase): RouteStep[] {
  if (route.isVoucher) return [
    {
      order: 1, title: 'Buy Swiggy Money Voucher', provider: 'GyFTR', amount: route.payNow,
      description: `Buy ${money(route.base)} Swiggy Money voucher for ${money(route.payNow)} from GyFTR using ${route.paymentName}. Opens the GyFTR catalogue; choose Swiggy Money and check availability and current terms. The 2.5% price is demo data, not a reserved offer.`,
      actionLabel: route.offer?.actionLabel, actionUrl: route.offer?.actionUrl,
    },
    {
      order: 2, title: 'Redeem on Swiggy', provider: 'Swiggy', amount: route.base,
      description: `Open Swiggy and apply the purchased voucher to the ${money(route.base)} order. In the Swiggy app, go to your account → Swiggy Money → Add voucher, then complete the order using that balance. Redeem the full value to save ${money(route.savings)} in this demo. The link opens the Swiggy homepage; voucher redemption may require the app.`,
      actionLabel: 'Open Swiggy', actionUrl: providerUrls.Swiggy,
    },
  ]
  const steps: Omit<RouteStep, 'order'>[] = [
    { title: `Open ${route.merchant}`, provider: route.merchant,
      description: 'Opens the provider homepage. Search and confirm current prices there; this link does not create a pre-filled booking or checkout.',
      actionLabel: route.offer?.actionLabel ?? `Open ${route.merchant}`, actionUrl: route.offer?.actionUrl ?? providerUrls[route.merchant] },
    { title: purchase.mode === 'travel' ? 'Search for your flight' : 'Review your order', provider: route.merchant, amount: route.base,
      description: purchase.mode === 'travel' ? `${purchaseLabel(purchase)} · ${dateLabel(purchase.departure)} · ${purchase.passengers} adult(s). Compare available flights with the illustrative ${money(route.base)} base fare and ${money(route.fees)} fees.` : `${purchaseLabel(purchase)}. Check the order total before payment.` },
    { title: `Choose ${route.paymentName}`, provider: route.paymentIssuer,
      description: route.offer ? 'Use the eligible product selected in My Wallet. Choose a non-EMI transaction and confirm eligibility on the provider.' : 'Confirm the total and your payment method before paying.' },
    ...(route.offer?.promo ? [{ title: `Apply promo code ${route.offer.promo}`, provider: route.merchant, description: `The demo assumes ${money(route.discount)} instant discount. Confirm a current eligible offer before paying; sample codes are not guaranteed to work.` }] : []),
    { title: `Pay ${money(route.payNow)}`, provider: route.merchant, amount: route.payNow,
      description: `${money(route.payNow)} leaves your account in this demo. ${route.rewards ? `${money(route.rewards)} estimated rewards arrive later, bringing Effective Cost to ${money(route.effective)}.` : 'No deferred rewards are assumed.'}` },
  ]
  return steps.map((step, index) => ({ ...step, order: index + 1 }))
}

export function sortRoutes(routes: PaymentRoute[], sort: Sort): PaymentRoute[] {
  return [...routes].sort((a, b) => sort === 'pay-now' ? a.payNow - b.payNow || a.effective - b.effective : sort === 'rewards' ? b.rewards - a.rewards || a.effective - b.effective : a.effective - b.effective || a.payNow - b.payNow)
}

export function recommendedRoutes(routes: PaymentRoute[], sort: Sort = 'overall') {
  return sortRoutes(routes.filter(route => route.recommended), sort)
}
