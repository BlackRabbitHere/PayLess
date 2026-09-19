import { requestJson } from './httpClient'
import type { SystemStatus } from '../types/api'
export const getSystemStatus = (signal?: AbortSignal) => requestJson<SystemStatus>('/api/v1/system/status', { signal })
