import { ArrowRight } from 'lucide-react'
import { Badge, MerchantMark } from '../../../shared/components/UI'
import { money } from '../model/presentation'
import type { PaymentRoute } from '../model/types'

export function PaymentRouteCard({ route, index, selected, onSelect, onView, lowestPay }: { route: PaymentRoute; index: number; selected: boolean; onSelect: () => void; onView: () => void; lowestPay: boolean }) {
  return <article className={`route-row ${selected ? 'route-row-selected' : ''}`}><div className="route-row-merchant"><input type="checkbox" checked={selected} onChange={onSelect} aria-label={`Compare ${route.merchant} with ${route.paymentName} ${route.offer?.label ?? 'direct payment'}`} /><span className="route-rank">{String(index).padStart(2, '0')}</span><MerchantMark merchant={route.merchant} color={route.merchantColor} /><div><h3>{route.merchant} {lowestPay && <Badge tone="primary">Lowest Pay Now</Badge>}</h3><p>{route.paymentName}</p><small>{route.offer?.label ?? 'Direct payment · no offer'}</small></div></div><div className="route-row-price"><span className="mobile-label">Pay Now</span><strong>{money(route.payNow)}</strong>{route.rewards > 0 && <small>+ {money(route.rewards)} rewards later</small>}</div><div className="route-row-price effective"><span className="mobile-label">Effective Cost</span><strong>{money(route.effective)}</strong></div><div className="route-row-savings"><span className="mobile-label">Savings</span><strong>{money(route.savings)}</strong><small>{route.offer?.kind ?? 'No offer'}</small></div><button className="route-view-button" aria-label={`View ${route.merchant} route with ${route.paymentName} ${route.offer?.label ?? 'direct payment'}`} onClick={onView}>View Route<ArrowRight size={15} /></button></article>
}

