import { ArrowRight, Check, CreditCard, Plane, ShoppingBag, Ticket } from 'lucide-react'
import { MerchantMark } from '../../../shared/components/UI'
import { money } from '../model/presentation'
import type { PaymentRoute, Purchase } from '../model/types'

export function RouteFlow({ route, purchase }: { route: PaymentRoute; purchase: Purchase }) {
  const steps = route.isVoucher ? [
    { title: `${money(route.base)} Swiggy order`, subtitle: 'Your purchase', icon: <ShoppingBag size={21} /> },
    { title: `Buy ${money(route.base)} voucher`, subtitle: `Pay ${money(route.payNow)} on GyFTR`, icon: <Ticket size={21} /> },
    { title: 'Open Swiggy', subtitle: 'Redeem voucher in the app', icon: <MerchantMark merchant="Swiggy" color={route.merchantColor} /> },
    { title: `Save ${money(route.savings)}`, subtitle: 'Complete your order', icon: <Check size={21} /> },
  ] : [
    { title: purchase.mode === 'travel' ? 'Your flight' : 'Your order', subtitle: purchase.mode === 'travel' ? `${purchase.from} → ${purchase.to}` : purchase.merchant, icon: purchase.mode === 'travel' ? <Plane size={21} /> : <ShoppingBag size={21} /> },
    { title: route.merchant, subtitle: purchase.mode === 'travel' ? 'Book with merchant' : 'Pay merchant directly', icon: <MerchantMark merchant={route.merchant} color={route.merchantColor} /> },
    { title: route.paymentName.replace(' Credit Card', '').replace(' Bank', ''), subtitle: route.paymentType, icon: <CreditCard size={21} /> },
    { title: route.discount ? route.offer?.label : 'Direct payment', subtitle: route.offer?.promo ? `Code: ${route.offer.promo}` : route.isVoucher ? 'Redeem in Swiggy' : 'No promo needed', icon: route.discount ? <Ticket size={21} /> : <Check size={21} /> },
  ]
  return <div className="route-flow">{steps.map((step, index) => <div className="flow-item" key={index}><div className={`flow-icon ${index === steps.length - 1 ? 'flow-success' : ''}`}>{step.icon}</div><div className="flow-label"><strong>{step.title}</strong><small>{step.subtitle}</small></div>{index !== steps.length - 1 && <ArrowRight className="flow-arrow" size={16} />}</div>)}</div>
}
