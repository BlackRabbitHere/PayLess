import { environment } from '../../app/config/environment'
import type { ApiProblem } from '../types/api'

export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly code?: string) { super(message) }
}

const problemMessages: Record<string, string> = {
  MERCHANT_UNSUPPORTED: 'This merchant isn’t supported yet. Try Swiggy, Yatra or EaseMyTrip.',
  MERCHANT_AMBIGUOUS: 'Include one merchant per search so we can compare the right offers.',
  AMOUNT_MISSING: 'Include the purchase amount, for example Swiggy ₹500.',
  AMOUNT_AMBIGUOUS: 'Include one total purchase amount in your search.',
  AMOUNT_INVALID: 'Use a positive INR amount with at most two decimal places.',
  INVALID_QUERY: 'Describe your merchant and amount in 1–1,000 characters.',
  INVALID_REQUEST: 'Check your search details and try again.',
  PERSISTENCE_UNAVAILABLE: 'Offers are temporarily unavailable. Please try again shortly.',
  SCRAPER_UNAVAILABLE: 'We can’t check offers right now. Please try again shortly.',
}

export async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const timeout = AbortSignal.timeout(75_000)
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body) headers.set('Content-Type', 'application/json')
  headers.set('X-Request-ID', crypto.randomUUID())
  let response: Response
  try {
    response = await fetch(environment.apiBaseUrl + path, {
      ...options, signal,
      headers,
    })
  } catch (error) {
    if (options.signal?.aborted) throw error
    throw new ApiError(timeout.aborted ? 'Checking offers took too long. Please try again.' : 'We couldn’t connect to the service. Check your connection and try again.', 0)
  }
  if (!response.ok) {
    const problem: ApiProblem = await response.json().catch(() => ({}))
    throw new ApiError(problemMessages[problem.code ?? ''] ?? (response.status >= 500 ? 'Service temporarily unavailable. Please try again shortly.' : 'We couldn’t complete this search. Check your details and try again.'), response.status, problem.code)
  }
  return response.json() as Promise<T>
}
