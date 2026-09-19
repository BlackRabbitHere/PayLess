import { usePrototype } from '../../../app/providers/PrototypeProvider'
import { useEffect, useRef, useState } from 'react'
import { optimizationApi } from '../api/optimizationApi'
import { travelApi } from '../../travel/api/travelApi'
import { useWalletStore } from '../../wallet/controller/walletStore'
import { selectedInstruments } from '../model/walletMapping'
import type { OptimizeResponse } from '../model/contracts'
import { initialTravel, today, type TravelResponse, type TravelSearch } from '../../travel/model/contracts'

export function useOptimizationController() {
  const { recordSearch, purchase } = usePrototype()
  const wallet = useWalletStore(state => state.wallet)
  const setWallet = useWalletStore(state => state.setWallet)
  const [query, setQuery] = useState("I'm ordering on Swiggy for ₹500")
  const [travel, setTravel] = useState(initialTravel)
  const [mode, setMode] = useState<'merchant' | 'travel'>('merchant')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<OptimizeResponse | null>(null)
  const [travelResponse, setTravelResponse] = useState<TravelResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const request = useRef<AbortController | null>(null)
  const previousWallet = useRef(wallet)

  function clear() {
    request.current?.abort(); request.current = null
    setLoading(false); setResponse(null); setTravelResponse(null); setError(null); setSubmitted(false)
  }
  useEffect(() => () => request.current?.abort(), [])
  useEffect(() => {
    if (previousWallet.current !== wallet) { previousWallet.current = wallet; clear() }
  }, [wallet])

  async function submit(nextMode: 'merchant' | 'travel' = mode) {
    clear(); setMode(nextMode)
    if (nextMode === 'merchant' && (!query.trim() || query.length > 1000)) {
      setError('Describe your merchant and amount in 1–1,000 characters.'); return false
    }
    if (nextMode === 'travel' && (travel.origin === travel.destination || !travel.departureDate || travel.departureDate < today() || travel.passengers < 1 || travel.passengers > 6)) {
      setError('Choose different cities, today or a future departure date, and 1–6 passengers.'); return false
    }
    const active = new AbortController(); request.current = active; setLoading(true)
    try {
      const instruments = selectedInstruments(wallet)
      if (nextMode === 'travel') {
        const result = await travelApi.optimize({ ...travel, wallet: instruments }, active.signal)
        if (active.signal.aborted) return false
        setTravelResponse(result); setResponse(result.optimization)
        if (result.optimization) recordSearch({ ...purchase, mode: 'travel', from: travel.origin, to: travel.destination, departure: travel.departureDate, passengers: travel.passengers }, result.optimization.bestEffectiveCostRoute?.cost.saving ?? 0)
      } else {
        const result = await optimizationApi.optimize({ query: query.trim(), wallet: instruments }, active.signal)
        if (active.signal.aborted) return false
        setResponse(result)
        recordSearch({ ...purchase, mode: 'everyday', merchant: result.context.merchant, amount: result.context.amount, category: result.context.category }, result.bestEffectiveCostRoute?.cost.saving ?? 0)
      }
      setSubmitted(true)
      return true
    } catch (failure) {
      if (!active.signal.aborted) setError(failure instanceof Error ? failure.message : 'The request failed. Please try again.')
      return false
    } finally {
      if (request.current === active) { setLoading(false); request.current = null }
    }
  }
  return {
    query, setQuery: (value: string) => { clear(); setQuery(value) },
    travel, setTravel: (value: TravelSearch) => { clear(); setTravel(value) },
    mode, wallet, toggleWallet: (id: string) => { clear(); setWallet(wallet.map(item => item.id === id ? { ...item, selected: !item.selected } : item)) },
    submit, loading, response, travelResponse, error, submitted,
    reset: () => { clear(); setQuery("I'm ordering on Swiggy for ₹500"); setTravel(initialTravel()); setMode('merchant') },
  }
}
