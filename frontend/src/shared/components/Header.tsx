import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ChevronDown, RotateCcw, ShieldCheck, Wallet } from 'lucide-react'
import { usePrototype } from '../../app/providers/PrototypeProvider'
import { Badge, Brand, Modal } from './UI'
import { useOptimization } from '../../features/optimization/controller/OptimizationProvider'
import { BRAND } from '../../app/config/brand'

export function Header() {
  const { wallet, reset } = usePrototype()
  const optimization = useOptimization()
  const [profile, setProfile] = useState(false)
  const navigate = useNavigate()
  return <>
    <header className="app-header"><div className="header-inner">
      <Link to="/" aria-label={`${BRAND.name} home`}><Brand /></Link>
      <nav className="main-nav" aria-label="Main navigation"><NavLink to="/" end>Home</NavLink><NavLink to="/travel">Travel</NavLink><NavLink to="/wallet">My Wallet <span className="nav-count">{wallet.filter(item => item.selected).length}</span></NavLink><NavLink to="/recent">Recent Searches</NavLink></nav>
      <div className="header-end"><Badge>Payment explorer</Badge><button className="profile-button" onClick={() => setProfile(true)} aria-label="Open demo profile"><span>AK</span><ChevronDown size={14} /></button></div>
    </div></header>
    {profile && <Modal title="Your demo space" onClose={() => setProfile(false)}><div className="profile-summary"><span className="profile-avatar">AK</span><div><h3>Alex Kumar</h3><p>Demo profile · no sign-in required</p></div></div><div className="notice notice-primary"><ShieldCheck size={20} /><p>Only payment-method metadata is saved on this device. Recent searches last for this session. No card credentials are collected.</p></div><div className="stack mt-6"><button className="button button-primary" onClick={() => { setProfile(false); navigate('/wallet') }}><Wallet size={17} />Manage My Wallet</button><button className="button button-secondary" onClick={() => { reset(); optimization.reset(); setProfile(false); navigate('/') }}><RotateCcw size={16} />Reset all demo data</button></div></Modal>}
  </>
}

export function Footer() {
  return <footer className="app-footer"><Brand small /><span>{BRAND.tagline}</span><span className="footer-disclaimer"><ShieldCheck size={14} />Explore routes · Pay with the provider</span><Link to="/system" className="text-button">Service status</Link></footer>
}
