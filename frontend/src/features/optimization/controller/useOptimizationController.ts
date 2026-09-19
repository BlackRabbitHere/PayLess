import { useMemo, useState } from 'react'
import { usePrototype } from '../../../app/providers/PrototypeProvider'
import { selectResults, selectedRoutes } from '../model/selectors'
import type { PaymentRoute, Scenario, Sort } from '../model/types'

export function useOptimizationController() {
  const { purchase, wallet, searched, setWallet, toast } = usePrototype()
  const [scenario, setScenario] = useState<Scenario>('normal')
  const [sort, setSort] = useState<Sort>('overall')
  const [selected, setSelected] = useState<string[]>([])
  const [compare, setCompare] = useState(false)
  const [detail, setDetail] = useState<PaymentRoute | null>(null)
  const [showAll, setShowAll] = useState(false)
  const result = useMemo(() => selectResults(purchase, wallet, scenario, sort), [purchase, wallet, scenario, sort])
  function toggleCompare(id: string) {
    if (selected.includes(id)) setSelected(selected.filter(item => item !== id))
    else if (selected.length === 3) toast('Compare up to 3 routes. Remove one to add another.')
    else setSelected([...selected, id])
  }
  function clearWallet() {
    setWallet(wallet.map(item => ({ ...item, selected: false })))
    setSelected([])
    toast('Wallet selections cleared to demonstrate the missing-wallet state.')
  }
  return { ...result, purchase, searched, scenario, setScenario, sort, setSort, selected, setSelected, compare, setCompare, detail, setDetail, showAll, setShowAll, toggleCompare, clearWallet, comparisonRoutes: selectedRoutes(result.routes, selected) }
}
