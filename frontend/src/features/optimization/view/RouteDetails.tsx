import { orderedSteps } from '../model/selectors'
import { Check, Copy, Gift, Info } from 'lucide-react'
import { usePrototype } from '../../../app/providers/PrototypeProvider'
import { BRAND } from '../../../app/config/brand'
import { money, purchaseLabel } from '../model/presentation'
import { Badge, MerchantMark, Modal, OfferBadge } from '../../../shared/components/UI'
import { CostBreakdown, EligibilityChecklist, OfferConditions, SourceVerification } from './RouteExplanation'
import { ExternalAction } from './ExternalAction'
import type { PaymentRoute, Purchase } from '../model/types'

export function RouteDetails({ route, purchase, onClose }: { route: PaymentRoute; purchase: Purchase; onClose: () => void }) {
  const { toast } = usePrototype()
  const steps = orderedSteps(route)
  return <Modal title="Your checkout guide" drawer onClose={onClose}>
    <p className="eyebrow mb-6">{purchaseLabel(purchase)}</p>
    <div className="drawer-route"><MerchantMark merchant={route.merchant} color={route.merchantColor} /><div><h3>{route.merchant}</h3><p>{route.paymentName}</p></div><OfferBadge status={route.status} /></div>
    <div className="drawer-metrics"><div><span>PAY NOW</span><strong>{money(route.payNow)}</strong></div><div><span>EFFECTIVE COST</span><strong>{money(route.effective)}</strong></div></div>
    <p className="savings-text"><strong>{money(route.savings)} total Savings</strong> vs. the same merchant without an offer</p>
    {!route.recommended && <div className="notice notice-amber"><Info size={18} /><p>This route is excluded from recommendations. Amounts are illustrative and depend on unmet or unverified conditions.</p></div>}
    <div className="guide-heading"><h3>How to complete this route</h3><Badge>{steps.length} steps</Badge></div>
    <ol className="guide-steps">{steps.map(step => <li key={step.order}>
      <span className="guide-number">{step.order}</span><div>
        <span className="step-provider">STEP {step.order} · {step.provider}</span>
        <h4>{step.title}</h4><p>{step.description}</p>
        {route.offer?.promo && step.title.startsWith('Apply') && <button className="promo-copy" onClick={async () => { try { await navigator.clipboard.writeText(route.offer!.promo!); toast('Promo code copied.') } catch { toast(`Promo code: ${route.offer!.promo}`) } }}><code>{route.offer.promo}</code><Copy size={14} />Copy code</button>}
        <ExternalAction url={step.actionUrl} label={step.actionLabel} primary={step.order === 1} disabled={!route.recommended} />
      </div>
    </li>)}</ol>
    <div className="reward-note"><Gift size={20} /><span><strong>{route.rewards ? `${money(route.rewards)} in Estimated Rewards later` : 'No deferred rewards assumed'}</strong><small>{route.offer?.assumption ?? 'No reward value is deducted from the checkout amount.'}</small></span></div>
    <div className="stack mt-6"><CostBreakdown route={route} /><EligibilityChecklist route={route} /><OfferConditions route={route} /><SourceVerification route={route} /></div>
    <div className="drawer-cta"><p><Check size={14} />You stay in control. {BRAND.name} never makes a payment.</p></div>
  </Modal>
}
