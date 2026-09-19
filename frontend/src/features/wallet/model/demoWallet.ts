import type { WalletProduct } from '../../optimization/model/types'

export const demoWallet: WalletProduct[] = [
  { id: 'hdfc-millennia', issuer: 'HDFC Bank', name: 'HDFC Millennia Credit Card', type: 'Credit Card', network: 'Visa', color: '#214e83', selected: true },
  { id: 'icici-credit', issuer: 'ICICI Bank', name: 'ICICI Credit Card', type: 'Credit Card', network: 'Visa', color: '#a44929', selected: true },
  { id: 'sbi-cashback', issuer: 'SBI Card', name: 'SBI Cashback Credit Card', type: 'Credit Card', network: 'Visa', color: '#226e98', selected: false },
  { id: 'sbi-debit', issuer: 'SBI Bank', name: 'SBI Visa Debit Card', type: 'Debit Card', network: 'Visa', color: '#254570', selected: false },
  { id: 'axis-credit', issuer: 'Axis Bank', name: 'Axis Bank Credit Card', type: 'Credit Card', network: 'Mastercard', color: '#8b315b', selected: false },
  { id: 'upi', issuer: 'UPI', name: 'UPI', type: 'UPI', network: 'UPI', color: '#486855', selected: true },
]

export const productCatalog: Omit<WalletProduct, 'selected'>[] = [
  ...demoWallet.map(({ selected: _selected, ...product }) => product),
  { id: 'hdfc-debit', issuer: 'HDFC Bank', name: 'HDFC EasyShop Debit Card', type: 'Debit Card', network: 'Visa', color: '#214e83' },
  { id: 'icici-coral', issuer: 'ICICI Bank', name: 'ICICI Coral Credit Card', type: 'Credit Card', network: 'RuPay', color: '#a44929' },
]
