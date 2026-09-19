import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useOptimization } from '../controller/OptimizationProvider'
import type { PaymentRoute, OptimizeResponse } from '../model/contracts'
import type { FareOption } from '../../travel/model/contracts'
import { ExternalAction } from './ExternalAction'
import { RequestStatus } from './SearchState'
import { money } from '../model/presentation'

const merchantName = (value: string) => ({ SWIGGY: 'Swiggy', YATRA: 'Yatra', EASEMYTRIP: 'EaseMyTrip', GYFTR: 'GyFTR' }[value] ?? value)
const instrumentKey = (route: PaymentRoute) => {
  const i = route.paymentInstrument
  return [i.issuer, i.productName, i.instrumentType, i.network].join('/')
}

function RouteCard({ route, response, fare, best = false }: { route: PaymentRoute; response: OptimizeResponse; fare?: FareOption; best?: boolean }) {
  const merchant = merchantName(fare?.merchant ?? response.context.merchant)
  const reasons = response.eligibility.filter(a => a.result.eligible && a.instrumentKey === instrumentKey(route) && route.sources.some(s => s.externalKey === a.offerKey))
  return <article className={best ? 'panel live-route live-best' : 'panel live-route'} aria-label={best ? 'Best Payment Route' : 'Alternative Payment Route'}>
    <span className="eyebrow">{best ? 'BEST EFFECTIVE COST' : 'PAYMENT OPTION'}</span>
    <h2>{route.kind === 'VOUCHER' ? 'GyFTR → ' + merchant + ' Voucher' : merchant + ' → ' + route.paymentInstrument.productName}</h2>
    <p className="muted">{route.paymentInstrument.productName}{fare && ' · ' + fare.flight}</p>
    <dl className="live-cost">
      <div><dt>Original</dt><dd>{money(route.cost.originalAmount)}</dd></div>
      <div><dt>Pay Now</dt><dd data-testid={best ? 'best-pay-now' : undefined}>{money(route.cost.payNow)}</dd></div>
      <div className="savings-text"><dt>Effective Cost</dt><dd data-testid={best ? 'best-effective' : undefined}>{money(route.cost.effectiveCost)}</dd></div>
      <div><dt>Saving</dt><dd>{money(route.cost.saving)}</dd></div>
    </dl>
    <p className="fine-print">Savings compare this route with the same purchase without an offer. Deferred rewards: {money(route.cost.deferredReward)}. These do not reduce what you pay now.</p>
    <details open={best}><summary>Why this works</summary><ul className="live-reasons">
      <li>✓ {merchant} supported</li><li>✓ Payment product: {route.paymentInstrument.productName}</li>
      {route.kind === 'VOUCHER' && <li>✓ {route.cost.remainingPayment === 0 ? 'Voucher covers purchase' : 'Voucher covers part of the purchase; remaining payment ' + money(route.cost.remainingPayment) + ' is included in Pay Now'}</li>}
      {reasons.length > 0 && <li>✓ Applied offers passed the merchant, wallet, amount, validity, and transaction checks</li>}
      {route.sources.length === 0 && <li>Direct payment: no eligible special offer is applied.</li>}
    </ul></details>
    <details open={best}><summary>How to use</summary><ol className="live-steps">{route.steps.map(step => <li key={step.number}><p>{step.instruction}</p>{step.actionLabel && <ExternalAction url={step.actionUrl ?? undefined} label={step.actionLabel} primary={step.number === 1} />}</li>)}</ol></details>
    {route.sources.length > 0 && <details open={best}><summary>Offer terms & sources</summary>{route.sources.map(source => <div className="live-source" key={source.externalKey}>
      <p><strong>{merchantName(source.provider)}</strong> · {source.fixture ? 'Fixture offer — synthetic, not live' : source.verificationStatus}</p>
      <p className="fine-print">Last verified: {source.lastVerifiedAt ? new Date(source.lastVerifiedAt).toLocaleString('en-IN') : 'Not supplied'}</p>
      <ul>{source.terms.map((term, i) => <li key={i}>{term}</li>)}</ul><ExternalAction url={source.sourceUrl} label="View Offer Terms" />
    </div>)}</details>}
    {route.warnings.length > 0 && <ul className="fine-print">{route.warnings.map(w => <li key={w}>{w}</li>)}</ul>}
  </article>
}

export function ResultsPage() {
  const { response, travelResponse, submitted, mode, query, travel, submit, loading, error, reset } = useOptimization()
  const [sort, setSort] = useState('effective')
  const [compare, setCompare] = useState(false)
  const editPath = mode === 'travel' ? '/travel' : '/'
  const best = response?.bestEffectiveCostRoute
  const fareFor = (route: PaymentRoute) => travelResponse?.fares.find(f => f.id === travelResponse.routeFareIds[route.id])
  if (loading) return <main className="page"><div className="empty-state panel"><h1>Finding your best route…</h1><RequestStatus /><button className="button button-secondary" onClick={reset}>Cancel search</button></div></main>
  if (error) return <main className="page"><div className="empty-state panel"><h1>We couldn’t complete this search.</h1><RequestStatus /><div className="live-actions"><button className="button button-primary" onClick={() => void submit()}>Try again</button><Link className="button button-secondary" to={editPath}>Edit search</Link></div></div></main>
  if (!submitted || !response || !best) return <main className="page"><div className="empty-state panel">
    <h1>{submitted ? 'No routes found.' : 'Let’s find your next route.'}</h1><p>{travelResponse?.warnings.join(' ') ?? 'Start a search, or rerun it after changing your wallet. Results are not saved when you reload.'}</p>
    <Link className="button button-primary" to={editPath}>{submitted ? 'Edit search' : 'Start a search'}</Link></div><RequestStatus /></main>
  const all = [best, response.bestPayNowRoute, ...response.alternatives].filter((r): r is PaymentRoute => r !== null).filter((r, i, routes) => routes.findIndex(other => other.id === r.id) === i)
  const alternatives = all.filter(r => r.id !== best.id).sort((a, b) => sort === 'pay-now' ? a.cost.payNow - b.cost.payNow : a.cost.effectiveCost - b.cost.effectiveCost)
  const failures = response.sources.filter(source => source.status !== 'SUCCESS' || source.errors.length > 0)
  const unavailable = response.sources.length > 0 && response.sources.every(source => source.status === 'UNAVAILABLE')
  return <main className="page results-page"><div className="page-title-row"><div><span className="eyebrow">{all.length} PAYMENT ROUTES COMPARED</span><h1>Best Route Found.</h1><p>{mode === 'travel' ? travel.origin + ' → ' + travel.destination + ' · ' + travel.departureDate + ' · ' + travel.passengers + ' passenger(s)' : query}</p></div>
    <div className="live-actions"><Link className="button button-secondary" to={editPath}>Edit search</Link><button className="button button-secondary" onClick={() => void submit()} disabled={loading}>Refresh offers</button></div></div><RequestStatus />
    {unavailable ? <div role="status" className="notice notice-amber"><p><strong>Live offers are unavailable.</strong> Direct payment routes are still available. Try refreshing offers.</p></div>
      : failures.length > 0 && <div role="status" className="notice notice-amber"><p><strong>Some providers returned incomplete offers.</strong> Available routes are shown; results may be missing better offers.</p></div>}
    {response.sources.some(s => s.fixture) && <div className="notice notice-amber"><p><strong>Fixture offers</strong> · Synthetic offer data for integration testing; these are not live commercial prices.</p></div>}
    {travelResponse && <section className="panel live-fares" aria-label="Fare options"><h2>Fare options</h2>{travelResponse.warnings.map(w => <p key={w}>{w}</p>)}<div className="fare-options">{travelResponse.fares.map(fare => <div key={fare.id}><strong>{merchantName(fare.merchant)}</strong><span>{money(fare.totalAmount)} total · {fare.passengers} passenger(s)</span><small>{fare.demo ? 'Demo fare' : fare.fareSource} · {fare.flight}</small></div>)}</div></section>}
    <RouteCard route={best} response={response} fare={fareFor(best)} best />
    {response.bestPayNowRoute && response.bestPayNowRoute.id !== best.id && <div className="notice notice-primary"><p>Lowest Pay Now: <strong>{money(response.bestPayNowRoute.cost.payNow)}</strong> with {response.bestPayNowRoute.paymentInstrument.productName}. See this option below.</p></div>}
    <section className="live-alternatives"><div className="section-heading"><h2>Other ways to pay</h2><div className="live-actions"><label>Sort routes <select aria-label="Sort routes" value={sort} onChange={e => setSort(e.target.value)}><option value="effective">Effective Cost</option><option value="pay-now">Pay Now</option></select></label><button className="button button-secondary" onClick={() => setCompare(!compare)}>{compare ? 'Hide comparison' : 'Compare routes'}</button></div></div>
      {compare && <div className="live-table"><table><caption>Payment route comparison</caption><thead><tr><th>Route</th><th>Original</th><th>Pay Now</th><th>Effective Cost</th><th>Saving</th></tr></thead><tbody>{all.map(route => <tr key={route.id}><th>{merchantName(fareFor(route)?.merchant ?? response.context.merchant)} · {route.kind} · {route.paymentInstrument.productName}</th><td>{money(route.cost.originalAmount)}</td><td>{money(route.cost.payNow)}</td><td>{money(route.cost.effectiveCost)}</td><td>{money(route.cost.saving)}</td></tr>)}</tbody></table></div>}
      {alternatives.length === 0 ? <p>No additional eligible routes. You can add products in your wallet and search again.</p> : <div className="live-route-grid">{alternatives.map(route => <RouteCard key={route.id} route={route} response={response} fare={fareFor(route)} />)}</div>}
    </section>
    <details className="panel live-diagnostics"><summary>Provider status & eligibility details</summary>
      {response.sources.map(source => <div key={source.requestId}><h3>{merchantName(source.provider)} · {source.status}</h3>{source.warnings.map((w, i) => <p key={i}>{w.code}: {w.message}</p>)}{source.errors.map((e, i) => <p key={i}>{e.code}: {e.message}</p>)}</div>)}
      <ul>{response.eligibility.filter(a => !a.result.eligible).map((a, i) => <li key={i}>{a.offerKey} · {a.instrumentKey}: {a.result.reasons.map(reason => reason.toLowerCase().replaceAll('_', ' ')).join(', ')}</li>)}</ul>
    </details>
    <div className="live-warnings"><h2>Before you pay</h2><ul>{response.warnings.map(w => <li key={w}>{w}</li>)}</ul><p>Confirm current terms and final prices with the provider. Travel links open the booking provider; enter your trip details there.</p></div>
  </main>
}
