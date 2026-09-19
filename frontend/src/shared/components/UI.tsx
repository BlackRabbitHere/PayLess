import { useEffect, useRef, type ReactNode } from 'react'
import { Check, Info, ShieldCheck, X } from 'lucide-react'
import type { SourceStatus } from '../../features/optimization/model/types'
import { BRAND } from '../../app/config/brand'

export function Brand({ small = false }: { small?: boolean }) {
  return <span className={`brand ${small ? 'brand-small' : ''}`}><img src="/favicon.svg" alt="" /><span>{BRAND.wordmark}<span className="brand-period">.</span></span></span>
}
export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'primary' | 'green' | 'amber' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}
export function OfferBadge({ status }: { status: SourceStatus }) {
  return <Badge tone={status === 'VERIFIED' ? 'green' : status === 'AMBIGUOUS' ? 'amber' : 'neutral'}>{status === 'VERIFIED' && <ShieldCheck size={12} />}{status === 'DEMO' ? 'Demo Data' : status === 'VERIFIED' ? 'Source Verified' : 'Ambiguous'}</Badge>
}
export function MerchantMark({ merchant, color, size = '' }: { merchant: string; color: string; size?: string }) {
  return <span className={`merchant-mark ${size}`} style={{ background: `${color}12`, color }}>{merchant === 'Swiggy Money' ? 'S' : merchant.slice(0, 1).toUpperCase()}<span className="merchant-mark-dot" style={{ background: color }} /></span>
}
export function InfoTip({ children }: { children: ReactNode }) {
  return <span className="tooltip-wrap"><button type="button" className="info-tip" aria-label="About estimated rewards"><Info size={14} /></button><span className="tooltip" role="tooltip">{children}</span></span>
}
export function Modal({ title, children, onClose, wide = false, drawer = false }: { title: string; children: ReactNode; onClose: () => void; wide?: boolean; drawer?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null)
  const closeRef = useRef(onClose)
  closeRef.current = onClose
  useEffect(() => {
    const dialog = ref.current
    const previouslyFocused = document.activeElement as HTMLElement | null
    dialog?.showModal()
    const original = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { dialog?.close(); document.body.style.overflow = original; previouslyFocused?.focus() }
  }, [])
  return <dialog ref={ref} className={`modal ${wide ? 'modal-wide' : ''} ${drawer ? 'drawer' : ''}`} aria-labelledby="dialog-title" onCancel={event => { event.preventDefault(); closeRef.current() }} onClick={event => { if (event.target === event.currentTarget) closeRef.current() }}>
    <div className="modal-header"><div><span className="eyebrow">{BRAND.name.toUpperCase()} PROTOTYPE</span><h2 id="dialog-title">{title}</h2></div><button className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={20} /></button></div>
    <div className="modal-body">{children}</div>
  </dialog>
}
export function CheckLine({ children }: { children: ReactNode }) { return <span className="check-line"><Check size={15} />{children}</span> }

