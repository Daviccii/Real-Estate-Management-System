import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, getRoleDashboardPath } from '../hooks/useAuth'
import { validateAuth } from '../utils/validation'
import { isMfaChallenge, mfaService } from '../services/mfa'
import type { MfaChallenge, MfaMethod, MfaSetup } from '../services/mfa'

const METHOD_LABELS: Record<MfaMethod, string> = {
  totp: 'Authenticator app',
  sms: 'SMS code',
  recovery: 'Recovery code',
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login, getDashboardPath } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors,setFieldErrors]=useState<Record<string,string>>({})
  const [showPassword,setShowPassword]=useState(false)

  // Second-factor state
  const [challenge, setChallenge] = useState<MfaChallenge | null>(null)
  const [step, setStep] = useState<'credentials' | 'enrol' | 'verify'>('credentials')
  const [method, setMethod] = useState<MfaMethod>('totp')
  const [code, setCode] = useState('')
  const [enrolment, setEnrolment] = useState<MfaSetup | null>(null)
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([])
  const [smsHint, setSmsHint] = useState<string | null>(null)

  const finishLogin = async (accessTokenPayload: any) => {
    const role = accessTokenPayload?.user?.role
    const target = accessTokenPayload?.redirect_url || (role ? getRoleDashboardPath(role) : getDashboardPath())
    navigate(target)
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null); setFieldErrors({})
    const errs = validateAuth(email,password)
    if(Object.keys(errs).length>0){ setFieldErrors(errs); setLoading(false); return }
    try {
      const res: any = await login(email, password)
      if (isMfaChallenge(res)) {
        setChallenge(res)
        setMethod(res.allowed_methods?.[0] ?? 'totp')
        if (res.mfa_setup_required) {
          setEnrolment(await mfaService.setup(res.mfa_token))
          setStep('enrol')
        } else {
          setStep('verify')
        }
        return
      }
      await finishLogin(res)
    } catch (err: any) {
      setError(err?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const sendSms = async () => {
    if (!challenge) return
    setError(null)
    try {
      const res = await mfaService.sendSms(challenge.mfa_token)
      // Development servers log the code instead of sending it; surface it in the UI.
      setSmsHint(res.dev_code ? `Development code: ${res.dev_code}` : res.message)
    } catch (err: any) {
      setError(err?.message || 'Could not send an SMS code')
    }
  }

  const submitEnrolment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!challenge) return
    setLoading(true)
    setError(null)
    try {
      const res = await mfaService.enable(code.trim(), challenge.mfa_token)
      setRecoveryCodes(res.recovery_codes)
      setCode('')
      setStep('verify')
    } catch (err: any) {
      setError(err?.message || 'That code did not match. Check your authenticator app.')
    } finally {
      setLoading(false)
    }
  }

  const submitChallenge = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!challenge) return
    setLoading(true)
    setError(null)
    try {
      const res = await mfaService.verify(challenge.mfa_token, method, code.trim())
      await finishLogin(res)
    } catch (err: any) {
      setError(err?.message || 'Verification failed')
      setCode('')
    } finally {
      setLoading(false)
    }
  }

  const cancel = () => {
    setChallenge(null)
    setEnrolment(null)
    setRecoveryCodes([])
    setSmsHint(null)
    setCode('')
    setStep('credentials')
    setError(null)
  }

  if (step === 'enrol' && enrolment) {
    return (
      <div style={{display:'grid',placeItems:'center',minHeight:'100vh',padding:16}}>
        <div style={{width:'min(480px, 100%)'}} className="card">
          <h2>Set up two-factor authentication</h2>
          <p style={{color:'var(--muted)'}}>
            Your role requires a second factor. Add this account to Google Authenticator, Authy, or 1Password
            using the key below, then confirm with the 6-digit code.
          </p>
          <p style={{fontFamily:'monospace',wordBreak:'break-all',background:'var(--surface-2,#f4f4f5)',padding:10,borderRadius:8}}>
            {enrolment.secret}
          </p>
          <a className="button muted" href={enrolment.provisioning_uri}>
            Open in authenticator app
          </a>
          <form onSubmit={submitEnrolment} style={{display:'grid',gap:10,marginTop:12}}>
            <input
              className="input"
              placeholder="6-digit code from your app"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            {error && <div style={{color:'var(--danger)'}}>{error}</div>}
            <button className="button" disabled={loading || code.trim().length < 6}>
              {loading ? 'Verifying...' : 'Enable two-factor'}
            </button>
            <button type="button" className="button muted" onClick={cancel}>Back to sign in</button>
          </form>
        </div>
      </div>
    )
  }

  if (step === 'verify' && challenge) {
    return (
      <div style={{display:'grid',placeItems:'center',minHeight:'100vh',padding:16}}>
        <div style={{width:'min(420px, 100%)'}} className="card">
          <h2>Two-factor verification</h2>
          {recoveryCodes.length > 0 && (
            <div style={{background:'var(--surface-2,#f4f4f5)',padding:10,borderRadius:8,marginBottom:12}}>
              <strong>Save your recovery codes.</strong> Each one works once if you lose your authenticator.
              <ul style={{fontFamily:'monospace', margin:'8px 0 0', paddingLeft:18}}>
                {recoveryCodes.map((recoveryCode) => <li key={recoveryCode}>{recoveryCode}</li>)}
              </ul>
            </div>
          )}
          <form onSubmit={submitChallenge} style={{display:'grid',gap:10}}>
            <label style={{fontSize:12,color:'var(--muted)'}}>
              Method
              <select
                className="input"
                value={method}
                onChange={(e) => { setMethod(e.target.value as MfaMethod); setSmsHint(null) }}
              >
                {(challenge.allowed_methods?.length ? challenge.allowed_methods : (['totp', 'recovery'] as MfaMethod[])).map((option: MfaMethod) => (
                  <option key={option} value={option}>{METHOD_LABELS[option]}</option>
                ))}
              </select>
            </label>
            {method === 'sms' && (
              <div style={{display:'flex',gap:8}}>
                <button type="button" className="button muted" onClick={sendSms}>Send code</button>
                {smsHint && <span style={{alignSelf:'center',fontSize:12}}>{smsHint}</span>}
              </div>
            )}
            <input
              className="input"
              placeholder={method === 'recovery' ? 'Recovery code' : '6-digit code'}
              inputMode={method === 'recovery' ? 'text' : 'numeric'}
              autoComplete="one-time-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            {error && <div style={{color:'var(--danger)'}}>{error}</div>}
            <button className="button" disabled={loading || code.trim().length < 6}>
              {loading ? 'Verifying...' : 'Verify and sign in'}
            </button>
            <button type="button" className="button muted" onClick={cancel}>Use a different account</button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div style={{display:'grid',placeItems:'center',minHeight:'100vh',padding:16}}>
      <div style={{width:'min(420px, 100%)'}} className="card">
        <h2>Sign in to PropNoxa</h2>
        <form onSubmit={submit} style={{display:'grid',gap:10}}>
          <input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
          {fieldErrors.email && <div style={{color:'var(--danger)'}}>{fieldErrors.email}</div>}
          <div style={{display:'flex',gap:8}}>
            <input className="input" placeholder="Password" type={showPassword? 'text':'password'} value={password} onChange={e=>{ setPassword(e.target.value); setFieldErrors(s=>{ const n={...s}; delete n.password; return n }) }} />
            <button type="button" className="button muted" onClick={()=>setShowPassword(s=>!s)}>{showPassword? 'Hide':'Show'}</button>
          </div>
          {fieldErrors.password && <div style={{color:'var(--danger)'}}>{fieldErrors.password}</div>}
          {error && <div style={{color:'var(--danger)'}}>{error}</div>}
          <button className="button" disabled={loading}>{loading? 'Signing in...':'Sign in'}</button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
