import type { OptimizeResponse, WalletInstrument } from '../../optimization/model/contracts'
export interface TravelSearch { origin: string; destination: string; departureDate: string; passengers: number }
export interface TravelRequest extends TravelSearch { wallet: WalletInstrument[] }
export interface FareOption extends TravelSearch {
  id: string; merchant: string; flight: string; totalAmount: number; currency: string; demo: boolean; fareSource: string
}
export interface TravelResponse {
  fares: FareOption[]; optimization: OptimizeResponse | null; routeFareIds: Record<string, string>; warnings: string[]
}
export const travelCities = ['Delhi', 'Mumbai', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata']
export function today() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}
export const initialTravel = (): TravelSearch => ({ origin: 'Delhi', destination: 'Mumbai', departureDate: today(), passengers: 1 })
