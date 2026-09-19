import { demoHeroRoute } from '../model/demoPresentation'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowDown, ArrowRight, Check, CreditCard, GitCompareArrows, LockKeyhole, Plane, Route, ShieldCheck, Sparkles, Ticket, Wallet } from 'lucide-react'
import { SearchBox } from './SearchBox'
import { Badge, MerchantMark } from '../../../shared/components/UI'
import { usePrototype } from '../../../app/providers/PrototypeProvider'
import { money, purchaseLabel } from '../model/presentation'

const processSteps = [
  { icon: <Plane size={20} />, title: 'Start with a purchase', text: 'A flight, an order, or an everyday payment.' },
  { icon: <Wallet size={20} />, title: 'Bring your wallet', text: 'Select the payment products you already own.' },
  { icon: <GitCompareArrows size={20} />, title: 'See the complete picture', text: 'Prices, fees, offers and rewards, together.' },
  { icon: <Route size={20} />, title: 'Take the better route', text: 'Know what you pay now and what you save later.' },
]
export function Home() {
  const { recent, setPurchase } = usePrototype()
  const [searchRevision, setSearchRevision] = useState(0)
  const route = demoHeroRoute()
  return <main className="page home-page"><section className="home-hero"><div className="hero-copy"><span className="hero-eyebrow"><span className="tiny-route"><Route size={13} /></span>EVERY RUPEE. A BETTER ROUTE.</span><h1>The lowest price isn’t<br />always the <span>lowest cost.</span></h1><p>Describe your purchase. Find a better way to pay.<br className="desktop-break" /> Compare prices, payment offers and rewards —<br className="desktop-break" /> all with the wallet you already have.</p><div className="hero-benefits"><span><Check size={15} />Your wallet. Your savings.</span><span><Check size={15} />No card details needed.</span></div></div><div className="hero-route-card"><div className="hero-route-top"><span><Route size={16} />A SMARTER WAY TO PAY</span><Badge>Demo Data</Badge></div><div className="mini-route"><div className="mini-flight"><Plane size={20} /><div><strong>Delhi <ArrowRight size={14} /> Mumbai</strong><small>Same flight. A better payment route.</small></div></div><div className="mini-route-connector"><ArrowDown size={14} /></div><div className="mini-route-path"><MerchantMark merchant="Yatra" color="#cf3b54" /><strong>Yatra</strong><ArrowRight size={13} /><CreditCard size={17} /><strong>ICICI</strong><ArrowRight size={13} /><Ticket size={17} /><span>12% off</span></div><div className="mini-price-row"><div><span>PAY NOW</span><strong>{money(route.payNow)}</strong></div><ArrowRight size={17} /><div><span>EFFECTIVE COST</span><strong className="savings-text">{money(route.effective)}</strong></div></div><div className="mini-savings"><Sparkles size={14} /><strong>{money(route.savings)} total savings</strong><span>vs. same fare without an offer</span></div></div></div></section>
    <SearchBox key={searchRevision} />
    <section className="how-it-works"><div className="section-heading"><div><span className="eyebrow">LESS GUESSWORK. MORE SAVINGS.</span><h2>One purchase. All the possibilities.</h2></div><span className="section-aside">A little smarter at every step.</span></div><div className="process-grid">{processSteps.map((step, index) => <article key={step.title}><div className="process-icon">{step.icon}<span>0{index + 1}</span></div><h3>{step.title}</h3><p>{step.text}</p></article>)}</div></section>
    {recent.length > 0 && <section className="home-recent"><div className="section-heading"><h2>Pick up where you left off</h2><Link to="/recent" className="text-button">All recent searches<ArrowRight size={15} /></Link></div><div className="recent-mini-grid">{recent.slice(0, 2).map(item => <Link to="/" key={item.id} onClick={() => { setPurchase(item.purchase); setSearchRevision(value => value + 1); document.getElementById('purchase-search')?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }} className="recent-mini"><span>{purchaseLabel(item.purchase)}<small>Previous demo savings: {money(item.savings)}</small></span><ArrowRight size={17} /></Link>)}</div></section>}
    <div className="privacy-banner"><div className="privacy-icon"><LockKeyhole size={22} /></div><div><h3>Your wallet stays yours.</h3><p>This prototype never asks for your card number, CVV, OTP or PIN. Select only the payment products you own.</p></div><span><ShieldCheck size={16} />Private by design</span></div>
  </main>
}

