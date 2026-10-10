import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, getRoleDashboardPath } from '../hooks/useAuth'
import { validateAuth } from '../utils/validation'
import { isMfaChallenge, mfaService } from '../services/mfa'
import type { MfaChallenge, MfaMethod, MfaSetup } from '../services/mfa'
import { useTranslation } from '../i18n/LanguageContext'

const METHOD_LABEL_KEYS: Record<MfaMethod, string> = {
  totp: 'login.mfa.totp',
  sms: 'login.mfa.sms',
  recovery: 'login.mfa.recovery',
}

const LoginPage: React.FC = () => {
  const { t } = useTranslation()
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
      setError(err?.message || t('login.failed'))
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
      setSmsHint(res.dev_code ? t('login.mfa.devCode', { code: res.dev_code }) : res.message)
    } catch (err: any) {
      setError(err?.message || t('login.mfa.smsFailed'))
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
      setError(err?.message || t('login.mfa.codeMismatch'))
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
      setError(err?.message || t('login.mfa.verifyFailed'))
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
          <h2>{t('login.mfa.setupTitle')}</h2>
          <p style={{color:'var(--muted)'}}>
            {t('login.mfa.setupBlurb')}
          </p>
          <p style={{fontFamily:'monospace',wordBreak:'break-all',background:'var(--surface-2,#f4f4f5)',padding:10,borderRadius:8}}>
            {enrolment.secret}
          </p>
          <a className="button muted" href={enrolment.provisioning_uri}>
            {t('login.mfa.openApp')}
          </a>
          <form onSubmit={submitEnrolment} style={{display:'grid',gap:10,marginTop:12}}>
            <input
              className="input"
              placeholder={t('login.mfa.codePlaceholder')}
              inputMode="numeric"
              autoComplete="one-time-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            {error && <div style={{color:'var(--danger)'}}>{error}</div>}
            <button className="button" disabled={loading || code.trim().length < 6}>
              {loading ? t('login.mfa.verifying') : t('login.mfa.enable')}
            </button>
            <button type="button" className="button muted" onClick={cancel}>{t('login.mfa.backToSignIn')}</button>
          </form>
        </div>
      </div>
    )
  }

  if (step === 'verify' && challenge) {
    return (
      <div style={{display:'grid',placeItems:'center',minHeight:'100vh',padding:16}}>
        <div style={{width:'min(420px, 100%)'}} className="card">
          <h2>{t('login.mfa.verifyTitle')}</h2>
          {recoveryCodes.length > 0 && (
            <div style={{background:'var(--surface-2,#f4f4f5)',padding:10,borderRadius:8,marginBottom:12}}>
              <strong>{t('login.mfa.saveCodes')}</strong> {t('login.mfa.saveCodesHint')}
              <ul style={{fontFamily:'monospace', margin:'8px 0 0', paddingLeft:18}}>
                {recoveryCodes.map((recoveryCode) => <li key={recoveryCode}>{recoveryCode}</li>)}
              </ul>
            </div>
          )}
          <form onSubmit={submitChallenge} style={{display:'grid',gap:10}}>
            <label style={{fontSize:12,color:'var(--muted)'}}>
              {t('login.mfa.method')}
              <select
                className="input"
                value={method}
                onChange={(e) => { setMethod(e.target.value as MfaMethod); setSmsHint(null) }}
              >
                {(challenge.allowed_methods?.length ? challenge.allowed_methods : (['totp', 'recovery'] as MfaMethod[])).map((option: MfaMethod) => (
                  <option key={option} value={option}>{t(METHOD_LABEL_KEYS[option])}</option>
                ))}
              </select>
            </label>
            {method === 'sms' && (
              <div style={{display:'flex',gap:8}}>
                <button type="button" className="button muted" onClick={sendSms}>{t('login.mfa.sendCode')}</button>
                {smsHint && <span style={{alignSelf:'center',fontSize:12}}>{smsHint}</span>}
              </div>
            )}
            <input
              className="input"
              placeholder={method === 'recovery' ? t('login.mfa.recovery') : t('login.mfa.sixDigit')}
              inputMode={method === 'recovery' ? 'text' : 'numeric'}
              autoComplete="one-time-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            {error && <div style={{color:'var(--danger)'}}>{error}</div>}
            <button className="button" disabled={loading || code.trim().length < 6}>
              {loading ? t('login.mfa.verifying') : t('login.mfa.verifySignIn')}
            </button>
            <button type="button" className="button muted" onClick={cancel}>{t('login.mfa.useDifferent')}</button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div style={{display:'grid',placeItems:'center',minHeight:'100vh',padding:16}}>
      <div style={{width:'min(420px, 100%)'}} className="card">
        <h2>{t('login.title')}</h2>
        <form onSubmit={submit} style={{display:'grid',gap:10}}>
          <input className="input" placeholder={t('login.emailPlaceholder')} value={email} onChange={e=>setEmail(e.target.value)} />
          {fieldErrors.email && <div style={{color:'var(--danger)'}}>{fieldErrors.email}</div>}
          <div style={{display:'flex',gap:8}}>
            <input className="input" placeholder={t('login.passwordPlaceholder')} type={showPassword? 'text':'password'} value={password} onChange={e=>{ setPassword(e.target.value); setFieldErrors(s=>{ const n={...s}; delete n.password; return n }) }} />
            <button type="button" className="button muted" onClick={()=>setShowPassword(s=>!s)}>{showPassword? t('common.hide'):t('common.show')}</button>
          </div>
          {fieldErrors.password && <div style={{color:'var(--danger)'}}>{fieldErrors.password}</div>}
          {error && <div style={{color:'var(--danger)'}}>{error}</div>}
          <button className="button" disabled={loading}>{loading? t('login.signingIn'):t('login.signIn')}</button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
