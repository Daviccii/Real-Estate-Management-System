import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authService, AgentRegistrationData } from '../../services/auth'
import { useAuth } from '../../hooks/useAuth'

export const AgentRegister: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<AgentRegistrationData>({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    agency_name: '',
    license_number: '',
    operating_areas: '',
    specialties: 'Residential Rentals & Sales',
    years_experience: 3,
    bio: '',
    commission_rate: 5.0
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value ? Number(value) : undefined) : value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    if (!formData.email || !formData.password || !formData.full_name) {
      setError('Please fill in all required fields.')
      setLoading(false)
      return
    }

    try {
      const res = await authService.registerAgent(formData)
      if (res?.access_token) {
        await login(formData.email, formData.password)
        navigate('/agent')
      } else {
        navigate('/login')
      }
    } catch (err: any) {
      setError(err?.message || 'Agent registration failed. Please check your details.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', padding: '40px 20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ maxWidth: '640px', width: '100%', background: 'var(--surface)', borderRadius: '16px', padding: '36px', boxShadow: 'var(--card-shadow)' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '1.5rem' }}>🤝</span>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#7c3aed', background: '#f5f3ff', padding: '2px 8px', borderRadius: '12px' }}>
                Real Estate Agent
              </span>
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent)', margin: 0 }}>
              Agent Registration
            </h1>
          </div>
          <Link to="/register" style={{ color: 'var(--muted)', textDecoration: 'none', fontSize: '0.9rem' }}>
            &larr; Switch Role
          </Link>
        </div>

        {error && (
          <div style={{
            background: '#fee2e2',
            border: '1px solid #f87171',
            color: '#b91c1c',
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '0.9rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
              Full Name *
            </label>
            <input
              className="input"
              name="full_name"
              required
              placeholder="e.g. David Njoroge"
              value={formData.full_name}
              onChange={handleChange}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
              Email Address *
            </label>
            <input
              className="input"
              type="email"
              name="email"
              required
              placeholder="david.agent@example.com"
              value={formData.email}
              onChange={handleChange}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Phone Number *
              </label>
              <input
                className="input"
                name="phone"
                required
                placeholder="+254 711 987 654"
                value={formData.phone || ''}
                onChange={handleChange}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Password *
              </label>
              <input
                className="input"
                type="password"
                name="password"
                required
                placeholder="Min 6 characters"
                value={formData.password}
                onChange={handleChange}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Agency / Brokerage Name
              </label>
              <input
                className="input"
                name="agency_name"
                placeholder="e.g. Knight Frank, Pam Golding, Independent"
                value={formData.agency_name || ''}
                onChange={handleChange}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                EARB License / Reg #
              </label>
              <input
                className="input"
                name="license_number"
                placeholder="e.g. EARB/2024/5891"
                value={formData.license_number || ''}
                onChange={handleChange}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
              Operating Zones / Neighborhoods
            </label>
            <input
              className="input"
              name="operating_areas"
              placeholder="e.g. Westlands, Kilimani, Riverside, Lavington"
              value={formData.operating_areas || ''}
              onChange={handleChange}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Years of Experience
              </label>
              <input
                className="input"
                type="number"
                name="years_experience"
                value={formData.years_experience || 1}
                onChange={handleChange}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Standard Commission Rate (%)
              </label>
              <input
                className="input"
                type="number"
                step="0.5"
                name="commission_rate"
                value={formData.commission_rate || 5.0}
                onChange={handleChange}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
              Professional Bio & Highlights
            </label>
            <textarea
              className="input"
              rows={3}
              name="bio"
              placeholder="Tell property owners and prospective tenants about your track record and areas of expertise..."
              value={formData.bio || ''}
              onChange={handleChange}
            />
          </div>

          <button
            type="submit"
            className="button"
            disabled={loading}
            style={{ marginTop: '12px', background: '#7c3aed', padding: '12px', fontWeight: 700 }}
          >
            {loading ? 'Creating Agent Profile...' : 'Complete Agent Registration 🤝'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', color: 'var(--muted)', fontSize: '0.9rem' }}>
          Already registered?{' '}
          <Link to="/login" style={{ color: '#7c3aed', fontWeight: 700, textDecoration: 'none' }}>
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}

export default AgentRegister
