import { optimize, recommendedRoutes } from './demoOptimizer'
import { defaultPurchase } from '../../travel/model/demoFlights'
import { demoWallet } from '../../wallet/model/demoWallet'
import type { Purchase, WalletProduct } from './types'
export const demoHeroRoute = () => optimize(defaultPurchase, demoWallet).find(item => item.id === 'yatra-icici')!
export const demoSavings = (purchase: Purchase, wallet: WalletProduct[]) => recommendedRoutes(optimize(purchase, wallet))[0]?.savings ?? 0
