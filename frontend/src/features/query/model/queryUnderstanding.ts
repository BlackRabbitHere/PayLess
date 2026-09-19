import { merchantCatalogue, type MerchantId, type PurchaseCategory } from './merchantCatalogue'

export interface UnderstoodPurchase {
  intent: 'OPTIMIZE_PURCHASE'
  merchant: MerchantId | null
  category: PurchaseCategory | null
  amount: number | null
  confidence: number
  missingFields: ('merchant' | 'amount')[]
  issues: string[]
}

export function normalizeQuery(text: string): string {
  return text.normalize('NFKC').toLowerCase().replace(/[’‘]/g, "'").replace(/[\u200b-\u200d\ufeff]/g, '').replace(/\s+/g, ' ').trim()
}

function extractAmount(text: string): { amount: number | null; issue?: string } {
  // Match complete number tokens first so malformed grouping/extra decimals cannot
  // silently become a smaller, valid amount. Supports both 1,000 and 1,00,000.
  const candidates: number[] = []
  for (const match of text.matchAll(/-?\d[\d,.]*/g)) {
    const start = match.index!
    const before = text.slice(0, start)
    const after = text.slice(start + match[0].length)
    const currencyBefore = /(?:₹|\b(?:rs\.?|inr|rupees))\s*$/.test(before)
    const currencyAfter = /^\s*(?:rs\.?|inr|rupees)\b/.test(after)
    const spendingBefore = /\b(?:costs?|costing|spending|spend|paying|pay|amount(?: is)?|total(?: is)?)\s*$/.test(before)
    if (!currencyBefore && !currencyAfter && !spendingBefore) continue
    const raw = match[0].replace(/\.$/, '') // Sentence punctuation, not rounding.
    if (!/^(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d{1,2})?$/.test(raw) || (!currencyAfter && /^[\w,]|^\.\d/.test(after)) || /-\s*(?:₹|rs\.?|inr)\s*$/.test(before)) {
      return { amount: null, issue: 'Enter one valid order amount, with at most two decimal places.' }
    }
    const value = Number(raw.replace(/,/g, ''))
    if (!Number.isFinite(value) || value < 1 || value > 100000) return { amount: null, issue: 'Enter an amount between ₹1 and ₹1,00,000.' }
    candidates.push(value)
  }
  const amounts = [...new Set(candidates)]
  if (amounts.length > 1) return { amount: null, issue: 'I found more than one amount. Enter the order total to compare.' }
  return { amount: amounts[0] ?? null }
}

function editDistance(a: string, b: string): number {
  let previous = Array.from({ length: b.length + 1 }, (_, index) => index)
  for (let i = 1; i <= a.length; i++) {
    const next = [i]
    for (let j = 1; j <= b.length; j++) next[j] = Math.min(next[j - 1] + 1, previous[j] + 1, previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1))
    previous = next
  }
  return previous[b.length]
}

function recognizeMerchant(text: string): { merchant: typeof merchantCatalogue[number] | null; confidence: number; issue?: string } {
  const words = text.replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(Boolean)
  const phrase = ` ${words.join(' ')} `
  const exact = merchantCatalogue.filter(merchant => merchant.aliases.some(alias => phrase.includes(` ${alias} `)))
  if (exact.length > 1) return { merchant: null, confidence: 0, issue: 'Choose one merchant for this purchase.' }
  if (exact.length === 1) return { merchant: exact[0], confidence: phrase.includes(` ${exact[0].id.toLowerCase()} `) ? 1 : 0.96 }

  // Only merchant-position terms ("on swigyy", "from myntrra") or a short
  // standalone purchase phrase are candidates. Never scan prose for similar words.
  const candidates = new Set<string>()
  for (let i = 0; i < words.length; i++) {
    if (['on', 'from', 'at', 'for', 'via', 'using', 'merchant'].includes(words[i - 1]) || words.length <= 5) {
      if (/^[a-z]{5,12}$/.test(words[i])) candidates.add(words[i])
    }
  }
  const matches = merchantCatalogue.flatMap(merchant => {
    const canonical = merchant.id.toLowerCase()
    const scores = [...candidates].filter(term => term.slice(0, 2) === canonical.slice(0, 2) && Math.abs(term.length - canonical.length) <= 1)
      .filter(term => editDistance(term, canonical) === 1).map(term => 1 - 1 / Math.max(term.length, canonical.length))
    const confidence = Math.max(0, ...scores)
    return confidence >= 0.8 ? [{ merchant, confidence }] : []
  })
  if (matches.length !== 1) return { merchant: null, confidence: 0, ...(matches.length > 1 ? { issue: 'Choose one merchant for this purchase.' } : {}) }
  return matches[0]
}

export function understandQuery(query: string): UnderstoodPurchase {
  const text = normalizeQuery(query)
  const { merchant, confidence, issue: merchantIssue } = recognizeMerchant(text)
  const { amount, issue: amountIssue } = extractAmount(text)
  const keywordCategories: PurchaseCategory[] = []
  if (/\b(food|meal|lunch|dinner|takeaway)\b/.test(text)) keywordCategories.push('FOOD_DELIVERY')
  if (/\b(fashion|clothes|clothing|shoes|dress)\b/.test(text)) keywordCategories.push('FASHION')
  if (/\b(flight|travel|hotel|booking|trip)\b/.test(text)) keywordCategories.push('TRAVEL')
  return {
    intent: 'OPTIMIZE_PURCHASE', merchant: merchant?.id ?? null,
    category: merchant?.category ?? (keywordCategories.length === 1 ? keywordCategories[0] : null), amount, confidence,
    missingFields: [...(!merchant ? ['merchant' as const] : []), ...(amount === null ? ['amount' as const] : [])],
    issues: [merchantIssue, amountIssue].filter((issue): issue is string => !!issue),
  }
}
