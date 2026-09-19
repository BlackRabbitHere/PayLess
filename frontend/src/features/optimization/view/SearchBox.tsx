import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useOptimization } from '../controller/OptimizationProvider'
import { WalletSelection, RequestStatus } from './SearchState'
export function SearchBox() {
  const { query, setQuery, submit, loading, reset } = useOptimization()
  const navigate = useNavigate()
  return <section className="search-panel panel live-search" aria-label="Find a Payment Route"><form onSubmit={async event => { event.preventDefault(); if (await submit('merchant')) navigate('/results') }}>
    <label className="live-query"><span className="eyebrow">What are you paying for?</span><textarea aria-label="What are you paying for?" value={query} onChange={event => setQuery(event.target.value)} maxLength={1000} rows={2} required /></label>
    <p className="muted">Include a merchant and amount, for example “Swiggy ₹500”.</p><WalletSelection />
    <div className="live-actions"><button className="button button-primary" disabled={loading} type="submit">{loading ? 'Finding payment routes…' : 'Find Best Payment Route'}<ArrowRight size={18} /></button><button className="button button-secondary" type="button" onClick={reset}>Reset</button></div><RequestStatus />
    </form></section>
}

