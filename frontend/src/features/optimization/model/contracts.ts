/** Manually synchronized with Spring OptimizeRequest/OptimizeResponse and domain records.
 * BigDecimal is serialized as JSON numbers. React displays, never recalculates, money.
 */
export interface WalletInstrument {
  issuer: string; productName: string; instrumentType: 'UPI' | 'CREDIT_CARD' | 'DEBIT_CARD'
  network: 'NONE' | 'UNKNOWN' | 'VISA' | 'MASTERCARD' | 'RUPAY' | 'AMEX' | 'DINERS'
}
export interface OptimizationRequest { query: string; wallet: WalletInstrument[] }
export interface CostBreakdown {
  originalAmount: number; eligibleAmount: number; immediateDiscount: number; payNow: number
  deferredReward: number; effectiveCost: number; saving: number; remainingPayment: number
}
export interface RouteStep { number: number; instruction: string; actionLabel: string | null; actionUrl: string | null }
export interface ProviderWarning { code: string; message: string; externalKey: string | null }
export interface ProviderFailure { code: string; message: string; provider: string; retryable: boolean }
export interface SourceMetadata {
  externalKey: string; provider: string; sourceUrl: string; verificationStatus: string
  lastVerifiedAt: string | null; observedAt: string; contentHash: string; fixture: boolean; terms: string[]
}
export interface PaymentRoute {
  id: string; kind: string; paymentInstrument: WalletInstrument; cost: CostBreakdown
  verificationConfidence: number; complexity: number; steps: RouteStep[]; sources: SourceMetadata[]; warnings: string[]
}
export interface OptimizeResponse {
  context: { merchant: 'SWIGGY' | 'YATRA' | 'EASEMYTRIP'; category: 'FOOD_DELIVERY' | 'TRAVEL'; amount: number; confidence: number }
  currency: string; bestEffectiveCostRoute: PaymentRoute | null; bestPayNowRoute: PaymentRoute | null
  alternatives: PaymentRoute[]
  eligibility: { offerKey: string; instrumentKey: string; result: { eligible: boolean; reasons: string[] } }[]
  sources: { requestId: string; provider: string; status: string; fixture: boolean; warnings: ProviderWarning[]; errors: ProviderFailure[] }[]
  warnings: string[]
}
