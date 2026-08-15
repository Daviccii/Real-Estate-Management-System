import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { validateAuth } from '../utils/validation'

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors,setFieldErrors]=useState<Record<string,string>>({})
  const [showPassword,setShowPassword]=useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null); setFieldErrors({})
    const errs = validateAuth(email,password)
    if(Object.keys(errs).length>0){ setFieldErrors(errs); setLoading(false); return }
    try {
      await login(email, password)
      navigate('/app')
    } catch (err: any) {
      setError(err?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{display:'grid',placeItems:'center',height:'100vh'}}>
      <div style={{width:420}} className="card">
        <h2>Sign in to PropNoxa</h2>
        <form onSubmit={submit} style={{display:'grid',gap:10}}>
          <input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
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
