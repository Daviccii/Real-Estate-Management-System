import { api } from './api'
import { setToken } from './token'
import type { User } from '../types'

export type MfaMethod = 'totp' | 'sms' | 'recovery'

/** Login returned a second-factor challenge instead of a session. */
export interface MfaChallenge {
  mfa_required: true
  mfa_setup_required: boolean
  mfa_token: string
  allowed_methods: MfaMethod[]
}

export interface MfaStatus {
  mfa_enabled: boolean
  has_secret: boolean
  sms_available: boolean
  recovery_codes_remaining: number
  mandatory_for_admin: boolean
}

export interface MfaSetup {
  secret: string
  provisioning_uri: string
  issuer: string
  account: string
  message: string
}

export interface LoginSession {
  access_token?: string
  user?: User
  redirect_url?: string
  mfa_required?: boolean
  mfa_setup_required?: boolean
  mfa_token?: string
  allowed_methods?: MfaMethod[]
}

export const isMfaChallenge = (data: LoginSession | null): data is MfaChallenge & LoginSession =>
  Boolean(data?.mfa_required && data?.mfa_token)

const json = (body: unknown) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const mfaService = {
  /** Exchange the challenge token + a valid second factor for a real session. */
  async verify(mfaToken: string, method: MfaMethod, code: string) {
    const data = await api.request<LoginSession>('/auth/mfa/verify', json({ mfa_token: mfaToken, method, code }))
    if (data?.access_token) {
      setToken(data.access_token)
    }
    return data
  },

  sendSms(mfaToken: string): Promise<{ message: string; dev_code?: string }> {
    return api.request('/auth/mfa/send-sms', json({ mfa_token: mfaToken }))
  },

  /** Enrolment (management) endpoints use the normal session bearer. */
  status(): Promise<MfaStatus> {
    return api.request('/auth/mfa/status')
  },

  setup(mfaToken?: string): Promise<MfaSetup> {
    return api.request('/auth/mfa/setup', json({ mfa_token: mfaToken ?? null }))
  },

  /** Returns the recovery codes - the only time they are ever revealed. */
  enable(code: string, mfaToken?: string): Promise<{ message: string; recovery_codes: string[]; warning: string }> {
    return api.request('/auth/mfa/enable', json({ code, mfa_token: mfaToken ?? null }))
  },

  disable(code: string): Promise<{ message: string }> {
    return api.request('/auth/mfa/disable', json({ code }))
  },

  regenerateRecoveryCodes(code: string): Promise<{ recovery_codes: string[]; warning: string }> {
    return api.request('/auth/mfa/recovery-codes/regenerate', json({ code }))
  },
}
