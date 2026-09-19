import { initial, type SavedState } from '../../features/optimization/model/state'
import { useWalletStore } from '../../features/wallet/controller/walletStore'
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import type { Purchase, WalletProduct } from '../../features/optimization/model/types'

interface PrototypeContextValue extends SavedState {
  setWallet: (products: WalletProduct[]) => void
  setPurchase: (purchase: Purchase) => void
  recordSearch: (purchase: Purchase, savings: number) => void
  reset: () => void
  toast: (message: string) => void
}
const PrototypeContext = createContext<PrototypeContextValue | null>(null)

export function PrototypeProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState(initial)
  const wallet = useWalletStore(state => state.wallet)
  const setWallet = useWalletStore(state => state.setWallet)
  const [notice, setNotice] = useState<{ message: string; id: number } | null>(null)
  const toastRef = useRef<HTMLDivElement>(null)
  useEffect(() => { if (notice) toastRef.current?.showPopover() }, [notice])
  function update(updateState: (current: SavedState) => SavedState) {
    setState(current => {
      const next = updateState(current)
      return next
    })
  }
  function toast(message: string) {
    const id = Date.now()
    setNotice({ message, id })
    window.setTimeout(() => setNotice(current => current?.id === id ? null : current), 4500)
  }
  return <PrototypeContext.Provider value={{ ...state, wallet,
    setWallet,
    setPurchase: purchase => update(current => ({ ...current, purchase })),
    recordSearch: (purchase, savings) => update(current => ({ ...current, purchase, searched: true, recent: [{ id: crypto.randomUUID(), purchase, savings, time: new Date().toISOString() }, ...current.recent.filter(item => JSON.stringify(item.purchase) !== JSON.stringify(purchase))].slice(0, 6) })),
    reset: () => { setWallet(initial().wallet); update(() => initial()); toast('Your starting wallet and searches are restored.') }, toast,
  }}>
    {children}
    {notice && <div ref={toastRef} popover="manual" className="toast" role="status"><span className="toast-check">✓</span>{notice.message}<button aria-label="Dismiss notification" onClick={() => setNotice(null)}>×</button></div>}
  </PrototypeContext.Provider>
}
export function usePrototype() {
  const context = useContext(PrototypeContext)
  if (!context) throw new Error('PrototypeProvider is required')
  return context
}
