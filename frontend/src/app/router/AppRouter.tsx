import { ServiceStatusPage } from '../../features/optimization/view/ServiceStatusPage'
import { useEffect } from 'react'
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { PrototypeProvider } from '../providers/PrototypeProvider'
import { Footer, Header } from '../../shared/components/Header'
import { Home } from '../../features/optimization/view/HomePage'
import { Wallet } from '../../features/wallet/view/WalletPage'
import { ResultsPage } from '../../features/optimization/view/ResultsPage'
import { Recent } from '../../features/optimization/view/RecentSearchesPage'
import { OptimizationProvider } from '../../features/optimization/controller/OptimizationProvider'
import { TravelPage } from '../../features/travel/view/TravelPage'
import { BRAND } from '../config/brand'

function RouteChange() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
    document.title = BRAND.name
    document.getElementById('main-content')?.focus({ preventScroll: true })
  }, [pathname])
  return null
}
export default function App() {
  return <PrototypeProvider><BrowserRouter><OptimizationProvider><RouteChange /><a className="skip-link" href="#main-content">Skip to content</a><Header /><div id="main-content" tabIndex={-1}><Routes><Route path="/" element={<Home />} /><Route path="/travel" element={<TravelPage />} /><Route path="/wallet" element={<Wallet />} /><Route path="/results" element={<ResultsPage />} /><Route path="/recent" element={<Recent />} /><Route path="/system" element={<ServiceStatusPage />} /><Route path="*" element={<main className="page"><div className="empty-state panel"><span className="eyebrow">A QUICK DETOUR</span><h1>This route doesn’t exist.</h1><p>Let’s get back to finding you a better deal.</p><Link className="button button-primary" to="/">Back to Home<ArrowRight size={17} /></Link></div></main>} /></Routes></div><Footer /></OptimizationProvider></BrowserRouter></PrototypeProvider>
}

