import type { WalletInstrument } from './contracts'
import type { WalletProduct } from './types'
export function selectedInstruments(wallet: WalletProduct[]): WalletInstrument[] {
  return wallet.filter(item => item.selected).map(item => ({
    issuer: ({ 'HDFC Bank': 'HDFC', 'ICICI Bank': 'ICICI', 'SBI Card': 'SBI', 'SBI Bank': 'SBI', 'Axis Bank': 'AXIS' } as Record<string, string>)[item.issuer] ?? item.issuer.toUpperCase(),
    productName: item.name,
    instrumentType: item.type === 'UPI' ? 'UPI' : item.type === 'Credit Card' ? 'CREDIT_CARD' : 'DEBIT_CARD',
    network: item.type === 'UPI' ? 'NONE' : item.network.toUpperCase() as WalletInstrument['network'],
  }))
}
