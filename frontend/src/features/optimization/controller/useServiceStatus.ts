import { useEffect, useRef, useState } from 'react'
import { getSystemStatus } from '../../../shared/api/systemApi'
import { checkScraperMapping, type ScraperCheck } from '../api/optimizationApi'
import type { SystemStatus } from '../../../shared/types/api'

export function useServiceStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [mapping, setMapping] = useState<ScraperCheck | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const request = useRef<AbortController | null>(null)
  useEffect(() => () => request.current?.abort(), [])

  async function check(includeMapping: boolean) {
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setBusy(true); setError(''); setStatus(null); setMapping(null)
    try {
      const result = await getSystemStatus(controller.signal)
      if (!controller.signal.aborted) setStatus(result)
      if (includeMapping) {
        const preview = await checkScraperMapping({ provider: 'GYFTR', merchant: 'SWIGGY' }, controller.signal)
        if (!controller.signal.aborted) setMapping(preview)
      }
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : 'Connection check failed.')
    } finally {
      if (!controller.signal.aborted) setBusy(false)
    }
  }
  return { status, mapping, busy, error, check }
}
