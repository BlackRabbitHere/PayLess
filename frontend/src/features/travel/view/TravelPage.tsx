import { useNavigate } from 'react-router-dom'
import { ArrowRight, Plane } from 'lucide-react'
import { useOptimization } from '../../optimization/controller/OptimizationProvider'
import { WalletSelection, RequestStatus } from '../../optimization/view/SearchState'
import { today, travelCities } from '../model/contracts'
export function TravelPage() {
  const { travel, setTravel, submit, loading, error, reset } = useOptimization()
  const navigate = useNavigate()
  return <main className="page"><div className="page-title-row"><div><span className="eyebrow">SAME TRIP. A BETTER WAY TO PAY.</span><h1>Find your travel route.</h1><p>Compare booking fares, offers, and your wallet in one place.</p></div><Plane size={32} /></div>
    <div className="notice notice-amber"><p><strong>Demo fares</strong> · The initial fare source supports Delhi ↔ Mumbai. Fares are illustrative; offers are acquired separately for each booking provider.</p></div>
    <section className="panel live-search"><form aria-describedby={error ? 'search-error' : undefined} onSubmit={async event => { event.preventDefault(); if (await submit('travel')) navigate('/results') }}>
      <div className="live-travel-fields">
        <label>From<select aria-label="From" aria-invalid={!!error} aria-describedby={error ? 'search-error' : undefined} value={travel.origin} onChange={event => setTravel({ ...travel, origin: event.target.value })}>{travelCities.map(city => <option key={city}>{city}</option>)}</select></label>
        <label>To<select aria-label="To" aria-invalid={!!error} aria-describedby={error ? 'search-error' : undefined} value={travel.destination} onChange={event => setTravel({ ...travel, destination: event.target.value })}>{travelCities.map(city => <option key={city}>{city}</option>)}</select></label>
        <label>Departure date<input aria-label="Departure" aria-invalid={!!error} aria-describedby={error ? 'search-error' : undefined} type="date" min={today()} required value={travel.departureDate} onChange={event => setTravel({ ...travel, departureDate: event.target.value })} /></label>
        <label>Passengers<select aria-label="Passengers" aria-invalid={!!error} aria-describedby={error ? 'search-error' : undefined} value={travel.passengers} onChange={event => setTravel({ ...travel, passengers: Number(event.target.value) })}>{[1, 2, 3, 4, 5, 6].map(n => <option value={n} key={n}>{n}</option>)}</select></label>
      </div><WalletSelection /><div className="live-actions"><button type="submit" className="button button-primary" disabled={loading}>{loading ? 'Comparing travel routes…' : 'Find Best Payment Route'}<ArrowRight size={17} /></button><button type="button" className="button button-secondary" onClick={reset}>Reset</button></div><RequestStatus />
    </form></section></main>
}
