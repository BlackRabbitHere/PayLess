import { Link } from 'react-router-dom'
import { environment } from '../../../app/config/environment'
import { useServiceStatus } from '../controller/useServiceStatus'

export function ServiceStatusPage() {
  const { status, mapping, busy, error, check } = useServiceStatus()
  return <main className="page">
    <Link to="/" className="back-link">Back to search</Link>
    <div className="page-title-row"><div><span className="eyebrow">LOCAL ENVIRONMENT</span>
      <h1>Service connections</h1><p>Check the backend and offer source. Demo search results remain illustrative.</p>
    </div></div>
    <section className="panel p-6 stack" aria-label="Service connections">
      <p>Environment: <strong>{environment.profile}</strong></p>
      <div className="flex flex-wrap gap-3">
        <button className="button button-primary" disabled={busy} onClick={() => void check(false)}>
          {busy ? 'Checking connections…' : 'Check connections'}
        </button>
        {!environment.production && <button className="button button-secondary" disabled={busy} onClick={() => void check(true)}>
          Check offer mapping
        </button>}
      </div>
      {error && <p role="alert" className="form-error">{error}</p>}
      {status && <div role="status"><p>Spring Boot: {status.backend}</p>
        <p>Scraper: {status.scraper.status} · {status.scraper.mode} mode · schema {status.scraper.schemaVersion}</p></div>}
      {mapping && <div>
        <h2>Offer mapping: {mapping.status}</h2>
        <p>{mapping.fixture ? 'Fixture data — no live commercial verification.' : 'Live source observations — eligibility and ranking have not been applied.'}</p>
        {mapping.observations.map(offer => <article key={offer.id} className="panel p-4 mt-4">
          <h3>{offer.title}</h3>
          <p>{offer.verificationStatus}</p>
          {offer.voucherSellingPrice !== null && <p>Voucher selling price: ₹{offer.voucherSellingPrice}</p>}
        </article>)}
        {mapping.warningCodes.length > 0 && <p>Source notices: {mapping.warningCodes.join(', ')}</p>}
        {mapping.errorCodes.length > 0 && <p>Source errors: {mapping.errorCodes.join(', ')}</p>}
      </div>}
    </section>
  </main>
}
