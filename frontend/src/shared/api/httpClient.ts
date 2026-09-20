import { environment } from '../../app/config/environment'
import type { ApiProblem } from '../types/api'

export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly code?: string) { super(message) }
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
    throw new ApiError(timeout.aborted ? 'The service request timed out.' : 'Cannot reach Spring Boot. Check that the backend is running.', 0)
  }
  if (!response.ok) {
    const problem: ApiProblem = await response.json().catch(() => ({}))
    throw new ApiError(problem.detail ?? 'The service could not complete the request.', response.status, problem.code)
  }
  return response.json() as Promise<T>
}
