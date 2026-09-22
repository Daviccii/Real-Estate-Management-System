import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authService, ProviderRegistrationData } from '../../services/auth'
import { useAuth } from '../../hooks/useAuth'

export const ProviderRegister: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<ProviderRegistrationData>({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    business_name: '',
    specialty: 'plumbing',
    license_number: '',
    hourly_rate: '2500',
    years_experience: 2,
    bio: '',
    service_areas: 'Nairobi Metropolitan'
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

    if (!formData.email || !formData.password || !formData.full_name || !formData.business_name) {
      setError('Please fill in all required fields.')
      setLoading(false)
      return
    }

    try {
      const res = await authService.registerProvider(formData)
      if (res?.access_token) {
        await login(formData.email, formData.password)
        navigate('/provider')
      } else {
        navigate('/login')
      }
    } catch (err: any) {
      setError(err?.message || 'Provider registration failed. Please check your details.')
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
              <span style={{ fontSize: '1.5rem' }}>🔧</span>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#d97706', background: '#fef3c7', padding: '2px 8px', borderRadius: '12px' }}>
                Trade Contractor
              </span>
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent)', margin: 0 }}>
              Service Partner Registration
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
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Contact Person Name *
              </label>
              <input
                className="input"
                name="full_name"
                required
                placeholder="e.g. Peter Otieno"
                value={formData.full_name}
                onChange={handleChange}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Business / Company Name *
              </label>
              <input
                className="input"
                name="business_name"
                required
                placeholder="e.g. QuickFix Plumbing Services"
                value={formData.business_name}
                onChange={handleChange}
              />
            </div>
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
              placeholder="peter.fix@example.com"
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
                placeholder="+254 722 000 111"
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
                Primary Trade Specialty *
              </label>
              <select
                className="input"
                name="specialty"
                value={formData.specialty}
                onChange={handleChange}
              >
                <option value="plumbing">Plumbing & Drainage</option>
                <option value="electrical">Electrical & Solar</option>
                <option value="hvac">HVAC & Air Conditioning</option>
                <option value="carpentry">Carpentry & Roofing</option>
                <option value="painting">Painting & Finishes</option>
                <option value="cleaning">Deep Cleaning & Fumigation</option>
                <option value="security">Security & Access Systems</option>
                <option value="general">General Handyman / Maintenance</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                NCA / Business License #
              </label>
              <input
                className="input"
                name="license_number"
                placeholder="e.g. NCA-PL-8921"
                value={formData.license_number || ''}
                onChange={handleChange}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Base Hourly Rate (KES)
              </label>
              <input
                className="input"
                name="hourly_rate"
                placeholder="e.g. 2500"
                value={formData.hourly_rate || ''}
                onChange={handleChange}
              />
            </div>

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
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
              Service Coverage Areas
            </label>
            <input
              className="input"
              name="service_areas"
              placeholder="e.g. Nairobi, Kiambu, Machakos"
              value={formData.service_areas || ''}
              onChange={handleChange}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
              Brief Business Description
            </label>
            <textarea
              className="input"
              rows={3}
              name="bio"
              placeholder="Describe your services, certifications, team size, and equipment..."
              value={formData.bio || ''}
              onChange={handleChange}
            />
          </div>

          <button
            type="submit"
            className="button"
            disabled={loading}
            style={{ marginTop: '12px', background: '#d97706', padding: '12px', fontWeight: 700 }}
          >
            {loading ? 'Creating Partner Account...' : 'Complete Partner Registration 🔧'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', color: 'var(--muted)', fontSize: '0.9rem' }}>
          Already registered?{' '}
          <Link to="/login" style={{ color: '#d97706', fontWeight: 700, textDecoration: 'none' }}>
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}

export default ProviderRegister
