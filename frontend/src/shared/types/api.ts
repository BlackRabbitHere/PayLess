export interface ApiProblem { title?: string; detail?: string; status?: number; code?: string }
export interface SystemStatus {
  backend: 'UP'
  scraper: { status: 'UP'; schemaVersion: number; mode: 'fixture' | 'live' }
}
