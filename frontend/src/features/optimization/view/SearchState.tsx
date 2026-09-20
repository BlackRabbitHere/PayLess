import { Link } from 'react-router-dom'
import { useOptimization } from '../controller/OptimizationProvider'
export function WalletSelection() {
  const { wallet, toggleWallet } = useOptimization()
  return <fieldset className="live-wallet"><legend>Your wallet</legend><div className="wallet-options">{wallet.map(item => <label key={item.id}><input type="checkbox" checked={item.selected} onChange={() => toggleWallet(item.id)} />{item.name}</label>)}</div>
    <p className="wallet-selection-summary">{wallet.length === 0 ? 'No wallet methods yet. Add the cards you own to check eligibility.' : `${wallet.filter(item => item.selected).length} of ${wallet.length} payment methods selected.`}</p>
    {!wallet.some(item => item.selected) && <p>No products selected. Direct UPI routes remain available where assumed by the provider.</p>}<Link className="text-button" to="/wallet">Manage wallet</Link></fieldset>
}
export function RequestStatus() {
  const { error, loading } = useOptimization()
  return <>{loading && <p role="status" className="notice notice-primary">Checking offers and comparing your payment routes…</p>}{error && <p id="search-error" className="form-error" role="alert">{error} You can edit the search and try again.</p>}</>
}
