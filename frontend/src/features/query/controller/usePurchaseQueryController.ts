import { useEffect, useState } from 'react'
import { merchantById } from '../model/merchantCatalogue'
import { understandQuery, type UnderstoodPurchase } from '../model/queryUnderstanding'
import { correctPurchase } from '../model/correction'

export function usePurchaseQueryController(preset: { text: string; revision: number }, onActivate: () => void) {
  const [query, setQuery] = useState(preset.text)
  const [parsed, setParsed] = useState<UnderstoodPurchase | null>(() => preset.text ? understandQuery(preset.text) : null)
  const [editing, setEditing] = useState(false)
  const [merchant, setMerchant] = useState('')
  const [amount, setAmount] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    setQuery(preset.text)
    setParsed(preset.text ? understandQuery(preset.text) : null)
    setEditing(false)
    setError('')
  }, [preset])

  function review(text: string) {
    const result = understandQuery(text)
    setQuery(text)
    setParsed(result)
    setMerchant(result.merchant ?? '')
    setAmount(result.amount === null ? '' : String(result.amount))
    setEditing(result.missingFields.length > 0)
    setError('')
    onActivate()
  }
  const recognized = merchantById(parsed?.merchant ?? null)
  function correct() {
    const result = correctPurchase(merchant, amount)
    if (typeof result === 'string') { setError(result); return }
    setParsed(result); setEditing(false); setError('')
  }
  return { query, setQuery, parsed, setParsed, editing, setEditing, merchant, setMerchant, amount, setAmount, error, setError, review, recognized, correct }
}
