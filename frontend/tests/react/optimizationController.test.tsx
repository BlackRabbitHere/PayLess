import { act, renderHook } from '@testing-library/react'
import { beforeEach, it, expect, vi } from 'vitest'
import { PrototypeProvider } from '../../src/app/providers/PrototypeProvider'
import { useOptimizationController } from '../../src/features/optimization/controller/useOptimizationController'
import { optimizationApi } from '../../src/features/optimization/api/optimizationApi'
import type { OptimizeResponse } from '../../src/features/optimization/model/contracts'
vi.mock('../../src/features/optimization/api/optimizationApi', () => ({ optimizationApi: { optimize: vi.fn() } }))
const response: OptimizeResponse = {
  context: { merchant: 'SWIGGY', category: 'FOOD_DELIVERY', amount: 500, confidence: 1 },
  currency: 'INR', bestEffectiveCostRoute: null, bestPayNowRoute: null, alternatives: [], eligibility: [], sources: [], warnings: [],
}
beforeEach(() => { vi.mocked(optimizationApi.optimize).mockReset() })
it('shows API errors, clears loading, and supports retry', async () => {
  const { result } = renderHook(useOptimizationController, { wrapper: PrototypeProvider })
  vi.mocked(optimizationApi.optimize).mockRejectedValueOnce(new Error('Storage unavailable')).mockResolvedValueOnce(response)
  await act(async () => { await result.current.submit() })
  expect(result.current.error).toBe('Storage unavailable')
  expect(result.current.loading).toBe(false)
  await act(async () => { await result.current.submit() })
  expect(result.current.response).toEqual(response)
  expect(result.current.error).toBeNull()
  expect(result.current.submitted).toBe(true)
})
it('cancels obsolete requests so late results cannot overwrite edited queries', async () => {
  let resolve!: (value: OptimizeResponse) => void
  vi.mocked(optimizationApi.optimize).mockImplementation(() => new Promise(done => { resolve = done }))
  const { result } = renderHook(useOptimizationController, { wrapper: PrototypeProvider })
  let pending!: Promise<boolean>
  act(() => { pending = result.current.submit() })
  expect(result.current.loading).toBe(true)
  const signal = vi.mocked(optimizationApi.optimize).mock.calls[0][1]
  act(() => result.current.setQuery('600 on Swiggy'))
  expect(signal?.aborted).toBe(true)
  await act(async () => { resolve(response); await pending })
  expect(result.current.response).toBeNull()
  expect(result.current.query).toBe('600 on Swiggy')
  expect(result.current.loading).toBe(false)
})
it('validates queries before network work', async () => {
  const { result } = renderHook(useOptimizationController, { wrapper: PrototypeProvider })
  act(() => result.current.setQuery(''))
  await act(async () => { await result.current.submit() })
  expect(result.current.error).toContain('Describe your merchant')
  expect(optimizationApi.optimize).not.toHaveBeenCalled()
})
