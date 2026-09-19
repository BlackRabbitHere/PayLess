import type { Purchase } from './types'
export const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2, minimumFractionDigits: Number.isInteger(value) ? 0 : 2 }).format(value)
export const purchaseLabel = (purchase: Purchase) => purchase.mode === 'travel' ? `${purchase.from} → ${purchase.to}` : `${purchase.merchant} · ${money(purchase.amount)}`
export const dateLabel = (date: string) => new Date(`${date}T12:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
