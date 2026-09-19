import { demoWallet } from '../../wallet/model/demoWallet'
import { defaultPurchase } from '../../travel/model/demoFlights'
import type { Purchase, WalletProduct } from './types'

export interface RecentSearch { id: string; purchase: Purchase; savings: number; time: string }
export interface SavedState { wallet: WalletProduct[]; purchase: Purchase; recent: RecentSearch[]; searched: boolean }
export const initial = (): SavedState => ({ wallet: demoWallet.map(product => ({ ...product })), purchase: { ...defaultPurchase }, recent: [], searched: false })
export const storageKey = 'routewise-demo-v1'
export function readState(): SavedState {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) ?? 'null') as SavedState | null
    if (saved && Array.isArray(saved.wallet) && saved.wallet.every(item => typeof item.id === 'string' && typeof item.name === 'string' && typeof item.selected === 'boolean') && saved.purchase && ['travel', 'everyday'].includes(saved.purchase.mode) && Number.isFinite(saved.purchase.amount) && Number.isFinite(saved.purchase.passengers) && Array.isArray(saved.recent)) return saved
  } catch { /* A clean demo is usable even when storage is unavailable. */ }
  return initial()
}
