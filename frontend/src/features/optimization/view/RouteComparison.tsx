import { comparisonMinimums } from '../model/selectors'
import { Check, Minus } from 'lucide-react'
import { money } from '../model/presentation'
import { Badge, MerchantMark, Modal } from '../../../shared/components/UI'
import type { PaymentRoute } from '../model/types'

export function RouteComparison({ routes, onClose }: { routes: PaymentRoute[]; onClose: () => void }) {
  const { lowestPay, lowestEffective } = comparisonMinimums(routes)
  const rows: { name: string; value: (route: PaymentRoute) => string; highlight?: (route: PaymentRoute) => boolean }[] = [
    { name: 'Base price', value: route => money(route.base) },
    { name: 'Convenience Fee', value: route => money(route.fees) },
    { name: 'Instant Discount', value: route => `−${money(route.discount)}` },
    { name: 'Pay Now', value: route => money(route.payNow), highlight: route => route.payNow === lowestPay },
    { name: 'Deferred rewards', value: route => money(route.rewards) },
    { name: 'Effective Cost', value: route => money(route.effective), highlight: route => route.effective === lowestEffective },
    { name: 'Savings vs same merchant, no offer', value: route => money(route.savings) },
    { name: 'Complexity / steps', value: route => `${route.steps.length} steps · ${route.isVoucher ? 'Voucher redemption' : route.offer?.promo ? 'Apply a promo code' : 'Direct checkout'}` },
  ]
  return <Modal title="Compare Payment Routes" onClose={onClose} wide><p className="muted mb-6">Follow every rupee from the listed price to the final cost. <strong>Demo Data</strong></p><div className="comparison-scroll" tabIndex={0} aria-label="Scrollable route comparison"><table className="comparison-table"><thead><tr><th scope="col">The complete picture</th>{routes.map(route => <th scope="col" key={route.id}><MerchantMark merchant={route.merchant} color={route.merchantColor} /><strong>{route.merchant}</strong><small>{route.paymentName}</small>{route.effective === lowestEffective && <Badge tone="green">Lowest Effective Cost</Badge>}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={row.name} className={row.highlight ? 'comparison-total' : ''}><th scope="row">{row.name}</th>{routes.map(route => <td key={route.id} className={row.highlight?.(route) ? 'best-cell' : ''}>{row.highlight?.(route) && <Check size={14} />}{row.value(route)}</td>)}</tr>)}<tr><th scope="row">Reward assumptions</th>{routes.map(route => <td className="comparison-assumption" key={route.id}>{route.offer?.assumption ?? <Minus size={15} />}</td>)}</tr></tbody></table></div><div className="notice notice-primary mt-6"><p>Pay Now is paid at checkout. Effective Cost subtracts estimated benefits received later. Savings use each route’s own base price plus fees as the no-offer baseline.</p></div></Modal>
}
