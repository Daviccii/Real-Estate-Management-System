import { getToken } from './token'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  data: any
  constructor(message: string, status = 500, data: any = null){
    super(message)
    this.status = status
    this.data = data
  }
}

// FIX: FastAPI validation errors (HTTP 422) return `detail` as an ARRAY of
// error objects (e.g. [{loc, msg, type}]), not a string. The old code did
// `data.detail || data.message` and passed the result straight into
// `super(message)` — when `detail` was a one-item array, JS's array-to-string
// coercion called `.toString()` on the single object inside, producing
// exactly "[object Object]" in the toast. This formats both shapes properly.
function formatErrorMessage(data: any, fallback: string): string {
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((e: any) => e?.msg || (typeof e === 'string' ? e : JSON.stringify(e)))
      .join('; ')
  }
  if (typeof data.message === 'string') return data.message
  return fallback
}

async function request<T = any>(path: string, opts: RequestInit = {}): Promise<T>{
  const url = API_BASE + path
  const headers = new Headers(opts.headers as Record<string,string> || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(url, {credentials: 'include', ...opts, headers})
  const text = await res.text()
  let data: any = null
  try{ data = text ? JSON.parse(text) : null }catch(e){ data = text }
  if (!res.ok) {
    const message = formatErrorMessage(data, res.statusText || 'Request failed')
    throw new ApiError(message, res.status, data)
  }
  return data
}

export const api = { request }
