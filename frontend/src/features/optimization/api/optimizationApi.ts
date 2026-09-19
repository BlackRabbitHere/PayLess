import { requestJson } from '../../../shared/api/httpClient'
import type { OptimizationRequest, OptimizeResponse } from '../model/contracts'

export const optimizationApi = {
  optimize: (request: OptimizationRequest, signal?: AbortSignal) => requestJson<OptimizeResponse>('/api/optimize/query', {
    method: 'POST', body: JSON.stringify(request), signal,
  }),
}

export type ScraperPair =
  | { provider: 'GYFTR'; merchant: 'SWIGGY' }
  | { provider: 'YATRA'; merchant: 'YATRA' }
  | { provider: 'EASEMYTRIP'; merchant: 'EASEMYTRIP' }

export interface ScraperCheck {
  requestId: string
  status: 'SUCCESS' | 'PARTIAL'
  provider: string
  merchant: string
  fixture: boolean
  observations: Array<{
    id: string; title: string; verificationStatus: string
    voucherFaceValue: string | null; voucherSellingPrice: string | null
    discountValue: string | null; maximumDiscount: string | null
    sourceUrl: string; observedAt: string
  }>
  warningCodes: string[]
  errorCodes: string[]
}

/** A development connectivity check; never used to rank demo payment routes. */
export const checkScraperMapping = (pair: ScraperPair, signal?: AbortSignal) =>
  requestJson<ScraperCheck>('/api/v1/optimization/scraper-check', {
    method: 'POST', body: JSON.stringify(pair), signal,
  })
