import { ExternalLink } from 'lucide-react'
import { isAllowedRedirect } from '../../redirect/model/redirectSafety'

export function ExternalAction({ url, label, primary = false, disabled = false }: {
  url?: string; label?: string; primary?: boolean; disabled?: boolean
}) {
  if (!label) return null
  const className = `button ${primary ? 'button-primary' : 'button-secondary'} external-action`
  if (disabled || !isAllowedRedirect(url)) return <button className={className} disabled>{label}<ExternalLink size={16} /></button>
  return <a className={className} href={url} target="_blank" rel="noopener noreferrer">{label}<ExternalLink size={16} /><span className="sr-only"> (opens in a new tab)</span></a>
}
