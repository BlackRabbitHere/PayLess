import { createContext, useContext, type ReactNode } from 'react'
import { useOptimizationController } from './useOptimizationController'
const Context = createContext<ReturnType<typeof useOptimizationController> | null>(null)
/** Feature scope spans its form and results routes; no API state is persisted. */
export function OptimizationProvider({ children }: { children: ReactNode }) {
  const controller = useOptimizationController()
  return <Context.Provider value={controller}>{children}</Context.Provider>
}
export function useOptimization() {
  const controller = useContext(Context)
  if (!controller) throw new Error('OptimizationProvider is required')
  return controller
}
