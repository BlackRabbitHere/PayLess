import { it, expect, vi } from 'vitest'
import { requestJson } from '../../src/shared/api/httpClient'
it('sends distinct correlation IDs and preserves Headers inputs', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response('{}'))
  vi.stubGlobal('fetch', fetcher)
  await requestJson('/api/test', { headers: new Headers({ 'X-Custom': 'ok' }) })
  fetcher.mockResolvedValue(new Response('{}'))
  await requestJson('/api/test')
  const headers = fetcher.mock.calls.map(call => call[1].headers as Headers)
  expect(headers[0].get('X-Request-ID')).toMatch(/^[a-f0-9-]{36}$/)
  expect(headers[0].get('X-Request-ID')).not.toBe(headers[1].get('X-Request-ID'))
  expect(headers[0].get('X-Custom')).toBe('ok')
})
it('exposes controlled API errors and handles non-JSON failures', async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Storage unavailable', code: 'PERSISTENCE_UNAVAILABLE' }), { status: 503 }))
  vi.stubGlobal('fetch', fetcher)
  await expect(requestJson('/api/test')).rejects.toMatchObject({ status: 503, code: 'PERSISTENCE_UNAVAILABLE', message: 'Storage unavailable' })
  fetcher.mockResolvedValue(new Response('<html>private proxy error</html>', { status: 502 }))
  await expect(requestJson('/api/test')).rejects.toMatchObject({ status: 502, message: 'The service could not complete the request.' })
})
it('distinguishes network failures from caller cancellation', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('private connection detail')))
  await expect(requestJson('/api/test')).rejects.toMatchObject({ status: 0 })
  const controller = new AbortController(); controller.abort()
  await expect(requestJson('/api/test', { signal: controller.signal })).rejects.toBeInstanceOf(TypeError)
})
