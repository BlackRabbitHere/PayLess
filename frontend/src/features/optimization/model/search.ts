import type { Purchase } from './types'
import type { UnderstoodPurchase } from '../../query/model/queryUnderstanding'
import { categoryLabels, merchantById } from '../../query/model/merchantCatalogue'

export function confirmEverydayPurchase(purchase: Purchase, parsed: UnderstoodPurchase): Purchase | null {
  const merchant = merchantById(parsed.merchant)
  if (!merchant || parsed.amount === null || parsed.missingFields.length) return null
  return { ...purchase, mode: 'everyday', merchant: merchant.name, amount: parsed.amount, category: categoryLabels[merchant.category] }
}
export const validateTravelPurchase = (purchase: Purchase) => purchase.from === purchase.to ? 'Choose different departure and arrival cities.' : ''
