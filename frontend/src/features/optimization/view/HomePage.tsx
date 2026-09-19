import { Link } from 'react-router-dom'
import { ArrowRight, Check, Route, ShieldCheck } from 'lucide-react'
import { SearchBox } from './SearchBox'
export function Home() {
  return <main className="page home-page"><section className="home-hero live-hero">
    <div className="hero-copy"><span className="hero-eyebrow"><Route size={16} />EVERY RUPEE. A BETTER ROUTE.</span><h1>The lowest price isn’t<br />always the <span>lowest cost.</span></h1><p>Describe your purchase. Compare payment offers with the wallet you already have.</p><div className="hero-benefits"><span><Check size={15} />Pay now. See what you save.</span><span><ShieldCheck size={15} />No card credentials needed.</span></div></div>
    <aside className="panel live-intro"><span className="eyebrow">ONE PURCHASE. ALL THE POSSIBILITIES.</span><h2>A clearer way to pay.</h2><ol><li>Tell us the merchant and amount.</li><li>Select your payment products.</li><li>Compare costs and follow the checkout steps.</li></ol><Link to="/travel" className="text-button">Planning a trip? Compare travel routes<ArrowRight size={16} /></Link></aside>
    </section><SearchBox /><div className="privacy-banner"><ShieldCheck size={24} /><div><h3>Your wallet stays yours.</h3><p>Only payment-product names are saved in this browser. Offers are checked when you search; fixture offers and demo fares are labeled.</p></div></div></main>
}

