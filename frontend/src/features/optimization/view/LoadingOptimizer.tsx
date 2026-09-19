import { useEffect, useState } from 'react'
import { Check, LoaderCircle, Route } from 'lucide-react'

const steps = ['Comparing merchant prices', 'Checking your wallet', 'Matching eligible offers', 'Comparing vouchers', 'Calculating Pay Now', 'Estimating rewards']
export function LoadingOptimizer({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0)
  useEffect(() => {
    const interval = window.setInterval(() => setStep(current => Math.min(current + 1, steps.length)), 180)
    const timer = window.setTimeout(onComplete, 1350)
    return () => { window.clearInterval(interval); window.clearTimeout(timer) }
  }, [onComplete])
  return <div className="optimizer-overlay" role="status" aria-live="polite"><div className="optimizer-card"><div className="optimizer-icon"><Route size={32} /></div><span className="eyebrow">A LITTLE MATH. A BETTER ROUTE.</span><h2>Finding your cheapest<br />payment route…</h2><p>Checking the complete cost, one step at a time.</p><div className="optimizer-steps">{steps.map((label, index) => <div key={label} className={index < step ? 'complete' : index === step ? 'checking' : ''}>{index < step ? <Check size={17} /> : index === step ? <LoaderCircle size={17} className="spin" /> : <span className="step-dot" />}{label}</div>)}</div><span className="muted text-xs">Using illustrative demo prices and offers</span></div></div>
}
