import { useNavigate } from 'react-router-dom'
import { usePrototype } from '../../../app/providers/PrototypeProvider'
import { demoSavings } from '../model/demoPresentation'
import type { Purchase } from '../model/types'
export function useRecentSearchesController() {
  const { recent, wallet, recordSearch } = usePrototype()
  const navigate = useNavigate()
  return { recent, runAgain: (purchase: Purchase) => { recordSearch(purchase, demoSavings(purchase, wallet)); navigate('/results') } }
}
