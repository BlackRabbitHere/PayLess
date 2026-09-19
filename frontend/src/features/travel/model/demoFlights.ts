import type { Purchase } from '../../optimization/model/types'

export const demoFlights = [
  { merchant: 'Yatra', base: 5520, fees: 130, color: '#cf3b54' },
  { merchant: 'EaseMyTrip', base: 5260, fees: 199, color: '#1482bc' },
  { merchant: 'ixigo', base: 5410, fees: 149, color: '#e77b23' },
  { merchant: 'Cleartrip', base: 5360, fees: 180, color: '#e97534' },
  { merchant: 'IndiGo', base: 5590, fees: 99, color: '#38419c' },
]

export const cities = ['Delhi', 'Mumbai', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata']
export const fixtureVerifiedDate = '2026-09-18'
export const defaultPurchase: Purchase = {
  mode: 'travel', from: 'Delhi', to: 'Mumbai', departure: '2026-10-24',
  passengers: 1, merchant: 'Swiggy', amount: 500, category: 'Food Delivery',
}
export const swiggyPurchase: Purchase = { ...defaultPurchase, mode: 'everyday' }
