// Exact hosts only: neither arbitrary subdomains nor look-alike domains qualify.
export const approvedProviderDomains = [
  'swiggy.com', 'zomato.com', 'myntra.com', 'gyftr.com', 'ixigo.com',
  'yatra.com', 'easemytrip.com', 'cleartrip.com', 'makemytrip.com',
  'goindigo.in', 'airindia.com',
] as const

export function isAllowedRedirect(value: unknown): value is string {
  // eslint-disable-next-line no-control-regex -- Reject control characters in untrusted redirect URLs.
  if (typeof value !== 'string' || !/^https:\/\//i.test(value) || /[\s\\\u0000-\u001f]/.test(value)) return false
  try {
    const url = new URL(value)
    const host = url.hostname.toLowerCase().replace(/^www\./, '')
    return url.protocol === 'https:' && !url.username && !url.password && !url.port &&
      approvedProviderDomains.some(domain => host === domain)
  } catch {
    return false
  }
}
