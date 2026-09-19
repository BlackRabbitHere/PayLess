import type { Offer } from './types'
import { providerUrls } from '../../../app/config/providers'
import { fixtureVerifiedDate } from '../../travel/model/demoFlights'

const destination = (merchant: string) => ({
  sourceUrl: providerUrls[merchant], actionUrl: providerUrls[merchant], actionLabel: `Open ${merchant}`,
})

const common = {
  mode: 'travel' as const, lastVerifiedAt: fixtureVerifiedDate,
  validFrom: '2026-09-01', validUntil: '2026-12-31', status: 'DEMO' as const,
  usage: 'Once per card during the demo offer period',
  restrictions: 'Cannot be combined with another promo code. Non-EMI payments only.',
}

export const demoOffers: Offer[] = [
  { ...common, id: 'yatra-icici', merchant: 'Yatra', ...destination('Yatra'), productId: 'icici-credit', label: '12% Instant Discount', rate: 0.12, cap: 1000, minimum: 5000, reward: 80, rewardKind: 'fixed', promo: 'ICICI12', kind: 'Instant Discount', assumption: '160 reward points at ₹0.50 per point = ₹80. Estimated credit within 60 days; redemption value is a demo assumption.' },
  { ...common, id: 'emt-hdfc', merchant: 'EaseMyTrip', ...destination('EaseMyTrip'), productId: 'hdfc-millennia', label: '₹300 Instant Discount', rate: 1, cap: 300, minimum: 5000, reward: 100, rewardKind: 'fixed', promo: 'FLY300', kind: 'Instant Discount', assumption: '₹100 estimated cashback after settlement, within 60 days. Assumes no reward exclusions for this demo.' },
  { ...common, id: 'ixigo-hdfc', merchant: 'ixigo', ...destination('ixigo'), productId: 'hdfc-millennia', label: '8% Instant Discount', rate: 0.08, cap: 800, minimum: 5000, reward: 180, rewardKind: 'fixed', promo: 'HDFCFLY', kind: 'Instant Discount', assumption: '₹180 estimated promotional cashback within 60 days, including a demo campaign bonus. This is not a live card benefit.' },
  { ...common, id: 'cleartrip-hdfc', merchant: 'Cleartrip', ...destination('Cleartrip'), productId: 'hdfc-millennia', label: '₹580 Instant Discount', rate: 1, cap: 580, minimum: 5000, reward: 20, rewardKind: 'fixed', promo: 'CT580', kind: 'Instant Discount', assumption: '₹20 estimated cashback within 60 days. No further reward value is included.' },
  { ...common, id: 'cleartrip-axis', merchant: 'Cleartrip', ...destination('Cleartrip'), productId: 'axis-credit', label: '10% Instant Discount', rate: 0.10, cap: 800, minimum: 5000, reward: 100, rewardKind: 'fixed', promo: 'AXIS10', kind: 'Instant Discount', assumption: '₹100 estimated cashback within 60 days. Assumes the demo offer and cashback can be combined.' },
  { ...common, id: 'indigo-sbi', merchant: 'IndiGo', ...destination('IndiGo'), productId: 'sbi-cashback', label: '5% estimated cashback', rate: 0, cap: 0, minimum: 0, reward: 0.05, rewardKind: 'percentage', kind: 'Cashback', assumption: '5% of Pay Now as demo cashback, capped at ₹500. Travel eligibility is assumed for this fictional offer.' },
  { ...common, id: 'cleartrip-conflict', merchant: 'Cleartrip', ...destination('Cleartrip'), productId: 'hdfc-millennia', label: '20% discount · conflicting terms', rate: 0.20, cap: 1500, minimum: 5000, reward: 0, rewardKind: 'fixed', promo: 'FLY20', kind: 'Instant Discount', status: 'AMBIGUOUS', assumption: 'One sample source permits all credit cards; another requires EMI. Excluded from automatic recommendations.' },
  { ...common, id: 'swiggy-voucher', merchant: 'Swiggy Money', purchaseMerchant: 'Swiggy', mode: 'everyday', sourceUrl: 'https://www.gyftr.com/luminous/vouchers/brand/swiggy-money-voucher-gift-vouchers', actionUrl: 'https://www.gyftr.com/', actionLabel: 'Buy Voucher', productId: 'any', label: '2.5% voucher discount', rate: 0.025, cap: 25, minimum: 100, reward: 0, rewardKind: 'fixed', kind: 'Voucher', assumption: 'Voucher value equals your order amount. Assumes the full voucher is redeemed, your account accepts it, and no extra fees apply.', restrictions: 'Demo voucher amounts ₹100–₹1,000. No additional card rewards assumed. Voucher cannot be exchanged for cash.', usage: 'One voucher per order in this demo' },
  { ...common, id: 'swiggy-hdfc', merchant: 'Swiggy', mode: 'everyday', ...destination('Swiggy'), productId: 'hdfc-millennia', label: '1% estimated cashback', rate: 0, cap: 0, minimum: 0, reward: 0.01, rewardKind: 'percentage', kind: 'Cashback', assumption: '1% of Pay Now as estimated cashback within 60 days, capped at ₹500. Swiggy eligibility is a demo assumption.' },
  { ...common, id: 'swiggy-sbi', merchant: 'Swiggy', mode: 'everyday', ...destination('Swiggy'), productId: 'sbi-cashback', label: '5% estimated cashback', rate: 0, cap: 0, minimum: 0, reward: 0.05, rewardKind: 'percentage', kind: 'Cashback', assumption: '5% of Pay Now as estimated cashback within 60 days, capped at ₹500. No instant checkout reduction.' },
]


