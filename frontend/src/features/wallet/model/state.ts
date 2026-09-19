import { demoWallet, productCatalog } from './demoWallet'
import type { WalletProduct } from '../../optimization/model/types'

export const selectedCount = (wallet: WalletProduct[]) => wallet.filter(item => item.selected).length
export const toggleProduct = (wallet: WalletProduct[], id: string) => wallet.map(item => item.id === id ? { ...item, selected: !item.selected } : item)
export const selectProducts = (wallet: WalletProduct[], selected: boolean) => wallet.map(item => ({ ...item, selected }))
export const removeProduct = (wallet: WalletProduct[], id: string) => wallet.filter(item => item.id !== id)
export const restoreProducts = () => demoWallet.map(item => ({ ...item }))
export const addProduct = (wallet: WalletProduct[], product: Omit<WalletProduct, 'selected'>) => wallet.some(item => item.id === product.id)
  ? wallet.map(item => item.id === product.id ? { ...item, selected: true } : item)
  : [...wallet, { ...product, selected: true }]
export const issuers = [...new Set(productCatalog.map(product => product.issuer))]
export const productsForIssuer = (issuer: string) => productCatalog.filter(product => product.issuer === issuer)
