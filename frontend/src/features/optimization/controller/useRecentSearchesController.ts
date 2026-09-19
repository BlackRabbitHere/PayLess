import { useNavigate } from 'react-router-dom'
import { usePrototype } from '../../../app/providers/PrototypeProvider'
import { useOptimization } from './OptimizationProvider'
import type { Purchase } from '../model/types'
export function useRecentSearchesController() {
  const { recent } = usePrototype()
  const { setQuery, setTravel } = useOptimization()
  const navigate = useNavigate()
  return { recent, runAgain: (purchase: Purchase) => {
    if (purchase.mode === 'travel') {
      setTravel({ origin: purchase.from, destination: purchase.to, departureDate: purchase.departure, passengers: purchase.passengers })
      navigate('/travel')
    } else { setQuery(purchase.merchant + ' ₹' + purchase.amount); navigate('/') }
  } }
}
