import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useOptimization } from '../controller/OptimizationProvider'
import { WalletSelection, RequestStatus } from './SearchState'
export function SearchBox() {
  const { query, setQuery, submit, loading, error, reset } = useOptimization()
  const navigate = useNavigate()
  return <section className="search-panel panel live-search" aria-label="Find a Payment Route"><form onSubmit={async event => { event.preventDefault(); if (await submit('merchant')) navigate('/results') }}>
    <label className="live-query"><span>What are you paying for?</span><textarea aria-label="What are you paying for?" aria-describedby={`query-hint${error ? ' search-error' : ''}`} aria-invalid={!!error} placeholder="I’m ordering ₹500 of food on Swiggy" value={query} onChange={event => setQuery(event.target.value)} maxLength={1000} rows={2} required /></label>
    <p id="query-hint" className="muted query-hint">Include a merchant and amount. We’ll compare the available routes for your wallet.</p>
    <div className="query-examples" aria-label="Example searches"><span>Try a search:</span>{[500, 1000].map(amount => <button key={amount} type="button" onClick={() => setQuery(`I'm ordering ₹${amount} of food on Swiggy`)}>Swiggy ₹{amount.toLocaleString('en-IN')}</button>)}<Link to="/travel">Delhi → Mumbai flight<ArrowRight size={14} /></Link></div><WalletSelection />
    <div className="live-actions"><button className="button button-primary" disabled={loading} type="submit">{loading ? 'Finding payment routes…' : 'Find Best Payment Route'}<ArrowRight size={18} /></button><button className="button button-secondary" type="button" onClick={reset}>Reset</button></div><RequestStatus />
    </form></section>
}

