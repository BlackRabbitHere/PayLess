import { usePurchaseQueryController } from '../../query/controller/usePurchaseQueryController'
import { ArrowRight, Check, Pencil, Search } from 'lucide-react'
import { categoryLabels, merchantCatalogue } from '../../query/model/merchantCatalogue'
import { type UnderstoodPurchase } from '../../query/model/queryUnderstanding'
import { money } from '../model/presentation'

export function PurchaseQuery({ preset, active, onActivate, onFlight, onConfirm }: {
  preset: { text: string; revision: number }; active: boolean; onActivate: () => void;
  onFlight: () => void; onConfirm: (query: UnderstoodPurchase) => void
}) {
  const { query, setQuery, parsed, setParsed, editing, setEditing, merchant, setMerchant, amount, setAmount, error, setError, review, recognized, correct } = usePurchaseQueryController(preset, onActivate)
  return <div className="purchase-query">
    <form onSubmit={event => { event.preventDefault(); review(query) }}>
      <label className="query-label" htmlFor="purchase-query">What are you buying?</label>
      <p className="query-hint">Describe an everyday purchase, or use the Travel form for flights.</p>
      <div className="query-input-row"><Search size={20} /><textarea id="purchase-query" rows={2} maxLength={500} required value={query} placeholder="Tell us what you're buying — e.g. I'm spending ₹500 on Swiggy. How can I save?" onChange={event => { setQuery(event.target.value); setParsed(null); setEditing(false); setError(''); onActivate() }} /><button className={`button ${parsed && active ? 'button-secondary' : 'button-primary'}`} type="submit">Review purchase<ArrowRight size={17} /></button></div>
    </form>
    <div className="query-examples"><span>Try</span><button type="button" onClick={() => review('₹500 on Swiggy')}>₹500 on Swiggy</button><button type="button" onClick={onFlight}>Delhi → Mumbai flight</button><button type="button" onClick={() => review('₹1,000 on Myntra')}>₹1,000 on Myntra</button></div>
    {active && parsed && <section className="query-interpretation" aria-label="Purchase interpretation" aria-live="polite">
      <div className="interpretation-heading"><h3><Check size={16} />We understood:</h3>{!editing && <button className="text-button" type="button" onClick={() => { setMerchant(parsed.merchant ?? ''); setAmount(parsed.amount === null ? '' : String(parsed.amount)); setEditing(true) }}><Pencil size={13} />Edit</button>}</div>
      <dl className="interpretation-values"><div><dt>Merchant</dt><dd>{recognized?.name ?? 'Choose a merchant'}</dd></div><div><dt>Amount</dt><dd>{parsed.amount === null ? 'Add your order total' : money(parsed.amount)}</dd></div><div><dt>Category</dt><dd>{parsed.category ? categoryLabels[parsed.category] : 'Determined by merchant'}</dd></div></dl>
      {editing ? <form className="query-correction" onSubmit={event => {
        event.preventDefault()
        correct()
      }}>
        <p className="clarification-prompt">{parsed.missingFields.includes('merchant') ? `Where are you making ${parsed.amount === null ? 'this purchase' : `this ${money(parsed.amount)} purchase`}?` : parsed.missingFields.includes('amount') ? `How much is your ${recognized?.name} order?` : 'Update your purchase details.'}</p>
        {parsed.issues.map(issue => <p className="fine-print" key={issue}>{issue}</p>)}
        <div className="correction-fields"><label>Merchant<select required aria-label="Merchant" value={merchant} onChange={event => setMerchant(event.target.value)}><option value="">Choose merchant</option>{merchantCatalogue.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Purchase Amount (₹)<input aria-label="Purchase Amount" inputMode="decimal" autoComplete="off" required value={amount} placeholder="e.g. 500" onChange={event => setAmount(event.target.value)} /></label><button className="button button-secondary" type="submit">Confirm purchase<Check size={16} /></button></div>
        {error && <p className="form-error" role="alert">{error}</p>}
      </form> : <div className="interpretation-footer"><span>Check these details before comparing your payment options.</span><button className="button button-primary" type="button" onClick={() => onConfirm(parsed)}>Find Best Payment Route<ArrowRight size={17} /></button></div>}
      {parsed.category === 'TRAVEL' && <button className="text-button travel-query-link" type="button" onClick={onFlight}>Compare flight fares with the Travel form<ArrowRight size={14} /></button>}
    </section>}
  </div>
}
