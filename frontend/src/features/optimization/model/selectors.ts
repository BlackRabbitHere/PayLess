import { optimize, recommendedRoutes } from './demoOptimizer'
import type { Purchase, WalletProduct, Scenario, Sort, PaymentRoute } from './types'

export function selectResults(purchase: Purchase, wallet: WalletProduct[], scenario: Scenario, sort: Sort) {
  const routes = optimize(purchase, wallet, scenario)
  const ranked = recommendedRoutes(routes)
  const best = ranked[0]
  const nextAction = best.steps.find(step => step.actionUrl)
  const lowestPay = recommendedRoutes(routes, 'pay-now')[0]
  const alternatives = recommendedRoutes(routes, sort).filter(route => route.id !== best.id)
  const excluded = routes.filter(route => !route.recommended)
  const activeWallet = wallet.filter(item => item.selected).length
  const cheapestListed = routes.filter(route => !route.offer).sort((a, b) => a.base - b.base)[0]
  return { routes, ranked, best, nextAction, lowestPay, alternatives, excluded, activeWallet, cheapestListed }
}

export const selectedRoutes = (routes: PaymentRoute[], selected: string[]) => selected.map(id => routes.find(route => route.id === id)).filter((route): route is PaymentRoute => Boolean(route))
export const comparisonMinimums = (routes: PaymentRoute[]) => ({ lowestPay: Math.min(...routes.map(route => route.payNow)), lowestEffective: Math.min(...routes.map(route => route.effective)) })
export const orderedSteps = (route: PaymentRoute) => [...route.steps].sort((a, b) => a.order - b.order)
export const excludedReason = (route: PaymentRoute) => route.rules.filter(rule => !rule.passes).map(rule => rule.label.replace(' selected', ' not selected')).join(' · ')
