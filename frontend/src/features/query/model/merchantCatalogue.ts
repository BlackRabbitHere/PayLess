export const categoryLabels = { FOOD_DELIVERY: 'Food Delivery', FASHION: 'Fashion', TRAVEL: 'Travel' } as const
export type PurchaseCategory = keyof typeof categoryLabels

export const merchantCatalogue = [
  { id: 'SWIGGY', name: 'Swiggy', category: 'FOOD_DELIVERY', aliases: ['swiggy', 'swigy', 'swigi', 'swiggi'] },
  { id: 'ZOMATO', name: 'Zomato', category: 'FOOD_DELIVERY', aliases: ['zomato', 'zomatto', 'zomto'] },
  { id: 'MYNTRA', name: 'Myntra', category: 'FASHION', aliases: ['myntra', 'mintra', 'myntraa'] },
  { id: 'IXIGO', name: 'ixigo', category: 'TRAVEL', aliases: ['ixigo', 'ixgo', 'ixigoo'] },
  { id: 'YATRA', name: 'Yatra', category: 'TRAVEL', aliases: ['yatra', 'yathra', 'yatraa'] },
  { id: 'EASEMYTRIP', name: 'EaseMyTrip', category: 'TRAVEL', aliases: ['easemytrip', 'ease my trip', 'ease mytrip', 'easemy trip', 'emt', 'easemytrp'] },
  { id: 'CLEARTRIP', name: 'Cleartrip', category: 'TRAVEL', aliases: ['cleartrip', 'clear trip', 'cleartrp'] },
  { id: 'MAKEMYTRIP', name: 'MakeMyTrip', category: 'TRAVEL', aliases: ['makemytrip', 'make my trip', 'make mytrip', 'makemy trip', 'mmt', 'makemytrp'] },
] as const satisfies readonly { id: string; name: string; category: PurchaseCategory; aliases: readonly string[] }[]

export type MerchantId = typeof merchantCatalogue[number]['id']
export const merchantById = (id: string | null) => merchantCatalogue.find(merchant => merchant.id === id)
