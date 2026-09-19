export type PurchaseMode = 'travel' | 'everyday'
export type PaymentType = 'Credit Card' | 'Debit Card' | 'UPI'
export type SourceStatus = 'DEMO' | 'VERIFIED' | 'AMBIGUOUS'
export type Scenario = 'normal' | 'no-offer' | 'stale' | 'ambiguous'
export type Sort = 'overall' | 'pay-now' | 'rewards'

export interface WalletProduct {
  id: string
  issuer: string
  name: string
  type: PaymentType
  network: string
  color: string
  selected: boolean
}

export interface Purchase {
  mode: PurchaseMode
  from: string
  to: string
  departure: string
  passengers: number
  merchant: string
  amount: number
  category: string
}

export interface Offer {
  id: string
  mode: PurchaseMode
  merchant: string
  purchaseMerchant?: string
  sourceUrl: string
  lastVerifiedAt: string
  actionUrl: string
  actionLabel: string
  productId: string | 'any'
  label: string
  rate: number
  cap: number
  minimum: number
  reward: number
  rewardKind: 'fixed' | 'percentage'
  promo?: string
  status: SourceStatus
  validFrom: string
  validUntil: string
  kind: 'Instant Discount' | 'Cashback' | 'Voucher'
  assumption: string
  usage: string
  restrictions: string
}

export interface EligibilityRule { label: string; passes: boolean }
export interface RouteStep {
  order: number
  title: string
  description: string
  provider: string
  amount?: number
  actionLabel?: string
  actionUrl?: string
}
export interface PaymentRoute {
  id: string
  merchant: string
  merchantColor: string
  productId?: string
  paymentName: string
  paymentIssuer: string
  paymentType: string
  base: number
  fees: number
  discount: number
  payNow: number
  rewards: number
  effective: number
  savings: number
  eligible: boolean
  recommended: boolean
  stale: boolean
  status: SourceStatus
  offer?: Offer
  rules: EligibilityRule[]
  sourceUrl: string
  lastVerifiedAt: string
  steps: RouteStep[]
  isVoucher: boolean
}
