import { merchantById, type MerchantId } from './merchantCatalogue'
import type { UnderstoodPurchase } from './queryUnderstanding'

export function correctPurchase(merchant: string, amount: string): UnderstoodPurchase | string {
  const chosen = merchantById(merchant)
  if (!chosen) return 'Choose a merchant from the supported catalogue.'
  if (!/^\d+(?:\.\d{1,2})?$/.test(amount) || Number(amount) < 1 || Number(amount) > 100000) return 'Enter an amount between ₹1 and ₹1,00,000, with at most two decimal places.'
  return { intent: 'OPTIMIZE_PURCHASE', merchant: merchant as MerchantId, category: chosen.category, amount: Number(amount), confidence: 1, missingFields: [], issues: [] }
}
