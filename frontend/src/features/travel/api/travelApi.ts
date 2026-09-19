import { requestJson } from '../../../shared/api/httpClient'
import type { TravelRequest, TravelResponse } from '../model/contracts'
export const travelApi = {
  optimize: (request: TravelRequest, signal?: AbortSignal) => requestJson<TravelResponse>('/api/travel/optimize', {
    method: 'POST', body: JSON.stringify(request), signal,
  }),
}
