import { useRecentSearchesController } from '../controller/useRecentSearchesController'
import { Link } from 'react-router-dom'
import { ArrowRight, Clock3, Plane, RotateCcw, ShoppingBag } from 'lucide-react'
import { money, purchaseLabel } from '../model/presentation'
import { Badge } from '../../../shared/components/UI'

export function Recent() {
  const { recent, runAgain } = useRecentSearchesController()
  return <main className="page recent-page"><div className="page-title-row"><div><span className="eyebrow">YOUR LAST FEW POSSIBILITIES</span><h1>Recent Searches<span className="title-dot">.</span></h1><p>Revisit a purchase. Review it and search again with your current wallet.</p></div><Badge>This session</Badge></div>{recent.length ? <div className="recent-list">{recent.map(item => <article className="recent-card panel" key={item.id}><span className="recent-icon">{item.purchase.mode === 'travel' ? <Plane size={22} /> : <ShoppingBag size={22} />}</span><div><h3>{purchaseLabel(item.purchase)}</h3><p><Clock3 size={13} />{new Date(item.time).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</p></div><div className="recent-saving"><small>Previous estimated savings</small><strong>{money(item.savings)}</strong></div><button className="button button-secondary" onClick={() => runAgain(item.purchase)}><RotateCcw size={15} />Review search</button></article>)}</div> : <div className="empty-state panel"><Clock3 size={38} /><h2>Your next great route starts here.</h2><p>Try a flight or Swiggy search to see it here.</p><Link className="button button-primary" to="/">Find a Payment Route<ArrowRight size={17} /></Link></div>}</main>
}
