const configuredUrl = import.meta.env.VITE_API_BASE_URL
if (configuredUrl === undefined) throw new Error('VITE_API_BASE_URL must be configured')
if (configuredUrl && !/^https?:\/\//.test(configuredUrl)) {
  throw new Error('VITE_API_BASE_URL must be an absolute HTTP(S) URL or empty for same-origin')
}
export const environment = Object.freeze({
  apiBaseUrl: configuredUrl.replace(/\/$/, ''),
  profile: import.meta.env.VITE_APP_PROFILE ?? import.meta.env.MODE,
  production: import.meta.env.MODE === 'production',
})
