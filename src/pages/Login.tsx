import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await login(email, password)
      navigate('/')
    } catch (err: any) {
      setError(err?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{display:'grid',placeItems:'center',height:'100vh'}}>
      <div style={{width:420}} className="card">
        <h2>Sign in to RealEstate OS</h2>
        <form onSubmit={submit} style={{display:'grid',gap:10}}>
          <input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
          <input className="input" placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          {error && <div style={{color:'var(--danger)'}}>{error}</div>}
          <button className="button" disabled={loading}>{loading? 'Signing in...':'Sign in'}</button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
