import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePrototype } from '../../../app/providers/PrototypeProvider'
import { defaultPurchase, swiggyPurchase } from '../../travel/model/demoFlights'
import { optimize, recommendedRoutes } from '../model/demoOptimizer'
import { confirmEverydayPurchase, validateTravelPurchase } from '../model/search'
import type { UnderstoodPurchase } from '../../query/model/queryUnderstanding'
import type { Purchase } from '../model/types'

export function useSearchController() {
  const { purchase, setPurchase, wallet, recordSearch, toast } = usePrototype()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [queryPreset, setQueryPreset] = useState(() => ({ text: purchase.mode === 'everyday' ? [purchase.amount, 'rupees on', purchase.merchant].join(' ') : '', revision: 0 }))
  const navigate = useNavigate()
  const update = (part: Partial<Purchase>) => { setPurchase({ ...purchase, ...part }); setError('') }
  const complete = useCallback(() => {
    const best = recommendedRoutes(optimize(purchase, wallet))[0]
    recordSearch(purchase, best?.savings ?? 0)
    navigate('/results')
  }, [purchase, wallet, recordSearch, navigate])
  function loadDemo(mode: 'travel' | 'everyday') {
    setPurchase({ ...(mode === 'travel' ? defaultPurchase : swiggyPurchase) })
    setError('')
    setQueryPreset(current => ({ text: mode === 'everyday' ? '₹500 on Swiggy' : '', revision: current.revision + 1 }))
    toast(mode === 'travel' ? 'Flight demo loaded. Ready to find your best Payment Route.' : '₹500 Swiggy demo loaded. Ready to compare payment options.')
    document.getElementById('purchase-search')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  function confirm(parsed: UnderstoodPurchase) {
    const next = confirmEverydayPurchase(purchase, parsed)
    if (next) { setPurchase(next); setLoading(true) }
  }
  function submitTravel() {
    const message = validateTravelPurchase(purchase)
    if (message) { setError(message); return }
    setLoading(true)
  }
  return { purchase, loading, error, queryPreset, update, complete, loadDemo, confirm, submitTravel, navigate, activeWallet: wallet.filter(item => item.selected).length }
}
