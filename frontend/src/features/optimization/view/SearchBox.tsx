import { useSearchController } from '../controller/useSearchController'
import { ArrowLeftRight, ArrowRight, CalendarDays, ChevronRight, CreditCard, Plane, ShoppingBag, Sparkles, Users } from 'lucide-react'
import { cities } from '../../travel/model/demoFlights'
import { PurchaseQuery } from './PurchaseQuery'
import { LoadingOptimizer } from './LoadingOptimizer'

export function SearchBox() {
  const { purchase, loading, error, queryPreset, update, complete, loadDemo, confirm, submitTravel, navigate, activeWallet } = useSearchController()
  return <>
    <section id="purchase-search" className="search-panel panel" aria-label="Find a Payment Route">
      <div className="search-tabs"><div className="tabs" role="tablist" aria-label="Purchase mode"><button role="tab" aria-selected={purchase.mode === 'travel'} className={purchase.mode === 'travel' ? 'active' : ''} onClick={() => update({ mode: 'travel' })}><Plane size={17} />Travel</button><button role="tab" aria-selected={purchase.mode === 'everyday'} className={purchase.mode === 'everyday' ? 'active' : ''} onClick={() => update({ mode: 'everyday' })}><ShoppingBag size={17} />Shopping & Payments</button></div><span className="search-category">{purchase.mode === 'travel' ? 'One way · Economy' : 'Everyday savings'}</span></div>
      <PurchaseQuery preset={queryPreset} active={purchase.mode === 'everyday'} onActivate={() => update({ mode: 'everyday' })} onFlight={() => loadDemo('travel')} onConfirm={confirm} />      {purchase.mode === 'travel' && <form onSubmit={event => { event.preventDefault(); submitTravel() }}>
        <div className="search-fields">            <label className="field"><span>From</span><select aria-label="From" value={purchase.from} onChange={event => update({ from: event.target.value })}>{cities.map(city => <option key={city}>{city}</option>)}</select><small>{purchase.from === 'Delhi' ? 'DEL · Indira Gandhi Intl.' : 'Departure city'}</small></label>
            <button className="swap-button" type="button" aria-label="Swap departure and destination" onClick={() => update({ from: purchase.to, to: purchase.from })}><ArrowLeftRight size={16} /></button>
            <label className="field"><span>To</span><select aria-label="To" value={purchase.to} onChange={event => update({ to: event.target.value })}>{cities.map(city => <option key={city}>{city}</option>)}</select><small>{purchase.to === 'Mumbai' ? 'BOM · Chhatrapati Shivaji Intl.' : 'Arrival city'}</small></label>
            <label className="field"><span><CalendarDays size={13} />Departure</span><input aria-label="Departure" type="date" required min="2026-09-19" max="2027-12-31" value={purchase.departure} onChange={event => update({ departure: event.target.value })} /><small>Sample travel date</small></label>
            <label className="field"><span><Users size={13} />Travellers</span><select aria-label="Travellers" value={purchase.passengers} onChange={event => update({ passengers: Number(event.target.value) })}>{[1, 2, 3, 4, 5, 6].map(number => <option value={number} key={number}>{number} {number === 1 ? 'Adult' : 'Adults'}</option>)}</select><small>Flights · Economy</small></label>
          <button className="button button-primary search-submit" type="submit">Find Best Payment Route<ArrowRight size={18} /></button>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
      </form>}      <div className="search-bottom"><span><CreditCard size={15} /><strong>{activeWallet} payment products</strong> in your wallet <button className="text-button" onClick={() => navigate('/wallet')}>Manage <ChevronRight size={13} /></button></span><span>Demo prices · No booking required</span></div>
    </section>
    <div className="demo-shortcuts"><span className="demo-label"><Sparkles size={15} />TAKE A QUICK TOUR</span><button className="demo-shortcut" onClick={() => loadDemo('travel')}><span className="shortcut-icon"><Plane size={21} /></span><span><strong>Book a Flight</strong><small>Delhi → Mumbai <span>· Load Flight Demo</span></small></span><ArrowUpRightSmall /></button><button className="demo-shortcut" onClick={() => loadDemo('everyday')}><span className="shortcut-icon shortcut-orange"><ShoppingBag size={21} /></span><span><strong>Pay for Swiggy</strong><small>₹500 order <span>· Load Swiggy Demo</span></small></span><ArrowUpRightSmall /></button></div>
    {loading && <LoadingOptimizer onComplete={complete} />}
  </>
}
function ArrowUpRightSmall() { return <ArrowRight size={18} className="shortcut-arrow" /> }

