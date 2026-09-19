import { useState } from 'react'
import { usePrototype } from '../../../app/providers/PrototypeProvider'
import { addProduct, issuers, productsForIssuer, removeProduct, restoreProducts, selectedCount, selectProducts, toggleProduct } from '../model/state'
import type { WalletProduct } from '../../optimization/model/types'

export function useWalletController() {
  const { wallet, setWallet, toast, searched } = usePrototype()
  const [adding, setAdding] = useState(false)
  return {
    wallet, searched, adding, setAdding, active: selectedCount(wallet),
    toggle: (id: string) => setWallet(toggleProduct(wallet, id)),
    selectAll: (selected: boolean) => setWallet(selectProducts(wallet, selected)),
    remove: (product: WalletProduct) => { setWallet(removeProduct(wallet, product.id)); toast(`${product.name} removed from your demo wallet.`) },
    restore: () => { setWallet(restoreProducts()); toast('Demo wallet restored.') },
  }
}

export function useAddProductController(onClose: () => void) {
  const { wallet, setWallet, toast } = usePrototype()
  const [issuer, setIssuer] = useState(issuers[0])
  const [productId, setProductId] = useState('')
  const products = productsForIssuer(issuer)
  const product = products.find(item => item.id === productId) ?? products[0]
  const exists = wallet.some(item => item.id === product.id)
  function submit() {
    setWallet(addProduct(wallet, product))
    toast(`${product.name} ${exists ? 'selected' : 'added to your wallet'}.`)
    onClose()
  }
  return { issuers, issuer, setIssuer, products, product, setProductId, exists, submit }
}
