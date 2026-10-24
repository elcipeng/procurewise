import { http, unwrap } from './client'

export type Health = {
  status: 'ok'
  version: string
  database: 'ok' | 'unavailable' | 'not_configured'
}

export const getHealth = () => unwrap<Health>(http.get('/health'))
