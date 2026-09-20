import { Link } from 'react-router-dom'
import { ArrowRight, Check, Route, ShieldCheck } from 'lucide-react'
import { SearchBox } from './SearchBox'
import { BRAND } from '../../../app/config/brand'
export function Home() {
  return <main className="page home-page"><section className="home-hero live-hero">
    <div className="hero-copy"><span className="hero-eyebrow"><Route size={16} />{BRAND.description}</span><h1>Pay smarter.<br /><span>Spend less.</span></h1><p>Tell us what you’re buying. {BRAND.name} compares available payment routes and offers to help you find a better way to pay.</p><div className="hero-benefits"><span><Check size={15} />Compare costs before checkout</span><span><ShieldCheck size={15} />No card credentials needed</span></div></div>
    <aside className="panel live-intro" aria-label={`How ${BRAND.name} works`}><span className="eyebrow">SEARCH → COMPARE → CHOOSE</span><h2>How {BRAND.name} works</h2><ol><li>Tell us the merchant and amount.</li><li>Select the payment methods you own.</li><li>Compare costs and follow the payment steps.</li></ol><Link to="/travel" className="text-button">Planning a trip? Compare travel routes<ArrowRight size={16} /></Link></aside>
    </section><SearchBox /><section className="supported-categories" aria-label="Available searches"><strong>Available in this demo</strong><span>Food · Swiggy via GyFTR</span><span>Travel · Yatra & EaseMyTrip</span><Link to="/travel" className="text-button">Delhi ↔ Mumbai<ArrowRight size={15} /></Link></section><div className="privacy-banner"><ShieldCheck size={24} /><div><h2>Your wallet stays yours.</h2><p>{BRAND.name} never needs your card number, CVV or PIN. Only payment-method metadata is saved in this browser. Demo offers and fares are clearly labeled.</p></div></div></main>
}

