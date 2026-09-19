import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { demoWallet, productCatalog } from '../model/demoWallet'
import type { WalletProduct } from '../../optimization/model/types'

// Only wallet metadata survives reloads. API state belongs to feature controllers.
export const useWalletStore = create<{ wallet: WalletProduct[]; setWallet: (wallet: WalletProduct[]) => void }>()(
  persist((set) => ({ wallet: demoWallet.map(item => ({ ...item })), setWallet: wallet => set({ wallet }) }), {
    name: 'routewise-wallet-v2', storage: createJSONStorage(() => ({
      getItem: name => { try { return localStorage.getItem(name) } catch { return null } },
      setItem: (name, value) => { try { localStorage.setItem(name, value) } catch { /* Keep in-memory selections usable. */ } },
      removeItem: name => { try { localStorage.removeItem(name) } catch { /* Storage may be disabled. */ } },
    })),
    partialize: state => ({ wallet: state.wallet }),
    merge: (persisted, current) => {
      const saved = (persisted as { wallet?: unknown } | null)?.wallet
      if (!Array.isArray(saved)) return current
      const wallet = saved.flatMap(item => {
        const product = productCatalog.find(product => product.id === item?.id)
        return product && typeof item.selected === 'boolean' ? [{ ...product, selected: item.selected }] : []
      })
      return { ...current, wallet }
    },
  }),
)
