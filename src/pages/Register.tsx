import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const RegisterPage: React.FC = () => {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await register(email, password, fullName)
      navigate('/login')
    } catch (err: any) {
      setError(err?.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{display:'grid',placeItems:'center',height:'100vh'}}>
      <div style={{width:480}} className="card">
        <h2>Create your account</h2>
        <form onSubmit={submit} style={{display:'grid',gap:10}}>
          <input className="input" placeholder="Full name" value={fullName} onChange={e=>setFullName(e.target.value)} />
          <input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
          <input className="input" placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          {error && <div style={{color:'var(--danger)'}}>{error}</div>}
          <button className="button" disabled={loading}>{loading? 'Creating...':'Create account'}</button>
        </form>
      </div>
    </div>
  )
}

export default RegisterPage
