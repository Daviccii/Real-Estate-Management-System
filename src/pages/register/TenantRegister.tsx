import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authService, TenantRegistrationData } from '../../services/auth'
import { useAuth } from '../../hooks/useAuth'

export const TenantRegister: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [step, setStep] = useState<1 | 2>(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<TenantRegistrationData>({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    preferred_locations: '',
    min_budget: 30000,
    max_budget: 90000,
    preferred_bedrooms: 2,
    preferred_property_type: 'apartment',
    desired_move_in_date: '',
    household_size: 1,
    has_pets: 'no',
    employment_status: 'employed',
    monthly_income: 120000,
    employer_name: '',
    job_title: ''
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value ? Number(value) : undefined) : value
    }))
  }

  const handleNextStep = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.email || !formData.password || !formData.full_name) {
      setError('Please fill in all required account fields.')
      return
    }
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setError(null)
    setStep(2)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const res = await authService.registerTenant(formData)
      if (res?.access_token) {
        // Auto-authenticate and redirect
        await login(formData.email, formData.password)
        navigate('/tenant')
      } else {
        navigate('/login')
      }
    } catch (err: any) {
      setError(err?.message || 'Registration failed. Please check your details.')
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
              <span style={{ fontSize: '1.5rem' }}>🏠</span>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#2563eb', background: '#eff6ff', padding: '2px 8px', borderRadius: '12px' }}>
                Tenant Onboarding
              </span>
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent)', margin: 0 }}>
              Create Tenant Account
            </h1>
          </div>
          <Link to="/register" style={{ color: 'var(--muted)', textDecoration: 'none', fontSize: '0.9rem' }}>
            &larr; Switch Role
          </Link>
        </div>

        {/* Progress Bar */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '28px' }}>
          <div style={{ flex: 1, height: '6px', borderRadius: '4px', background: '#2563eb' }} />
          <div style={{ flex: 1, height: '6px', borderRadius: '4px', background: step === 2 ? '#2563eb' : 'var(--line)' }} />
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

        {step === 1 ? (
          <form onSubmit={handleNextStep} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent)', margin: 0 }}>
              Step 1: Account & Credentials
            </h2>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Full Name *
              </label>
              <input
                className="input"
                name="full_name"
                required
                placeholder="e.g. Jane Doe"
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
                placeholder="jane.doe@example.com"
                value={formData.email}
                onChange={handleChange}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Phone Number
                </label>
                <input
                  className="input"
                  name="phone"
                  placeholder="+254 712 345 678"
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

            <button
              type="submit"
              className="button"
              style={{ marginTop: '12px', background: '#2563eb', padding: '12px', fontWeight: 700 }}
            >
              Continue to Preferences &rarr;
            </button>
          </form>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent)', margin: 0 }}>
              Step 2: Rental Preferences & Smart Match
            </h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.85rem', margin: '-8px 0 8px 0' }}>
              These preferences power your Smart Match rental recommendations.
            </p>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Preferred Locations (comma separated)
              </label>
              <input
                className="input"
                name="preferred_locations"
                placeholder="e.g. Westlands, Kilimani, Kileleshwa, Karen"
                value={formData.preferred_locations || ''}
                onChange={handleChange}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Min Monthly Budget (KES)
                </label>
                <input
                  className="input"
                  type="number"
                  name="min_budget"
                  value={formData.min_budget || ''}
                  onChange={handleChange}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Max Monthly Budget (KES)
                </label>
                <input
                  className="input"
                  type="number"
                  name="max_budget"
                  value={formData.max_budget || ''}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Preferred Bedrooms
                </label>
                <select
                  className="input"
                  name="preferred_bedrooms"
                  value={formData.preferred_bedrooms || 2}
                  onChange={handleChange}
                >
                  <option value={1}>1 Bedroom / Studio</option>
                  <option value={2}>2 Bedrooms</option>
                  <option value={3}>3 Bedrooms</option>
                  <option value={4}>4+ Bedrooms</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Property Type
                </label>
                <select
                  className="input"
                  name="preferred_property_type"
                  value={formData.preferred_property_type || 'apartment'}
                  onChange={handleChange}
                >
                  <option value="apartment">Apartment / Flat</option>
                  <option value="house">Townhouse / Villa</option>
                  <option value="studio">Studio</option>
                  <option value="penthouse">Penthouse</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Household Size
                </label>
                <input
                  className="input"
                  type="number"
                  name="household_size"
                  value={formData.household_size || 1}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Do You Have Pets?
                </label>
                <select
                  className="input"
                  name="has_pets"
                  value={formData.has_pets || 'no'}
                  onChange={handleChange}
                >
                  <option value="no">No Pets</option>
                  <option value="cat">Cat(s)</option>
                  <option value="dog">Dog(s)</option>
                  <option value="other">Other Pets</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Employment Status
                </label>
                <select
                  className="input"
                  name="employment_status"
                  value={formData.employment_status || 'employed'}
                  onChange={handleChange}
                >
                  <option value="employed">Employed (Full-time)</option>
                  <option value="self-employed">Self-Employed / Business</option>
                  <option value="student">Student</option>
                  <option value="retired">Retired</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Estimated Monthly Income (KES)
                </label>
                <input
                  className="input"
                  type="number"
                  name="monthly_income"
                  value={formData.monthly_income || ''}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
              <button
                type="button"
                className="button muted"
                onClick={() => setStep(1)}
                style={{ flex: 1, padding: '12px' }}
              >
                &larr; Back
              </button>
              <button
                type="submit"
                className="button"
                disabled={loading}
                style={{ flex: 2, background: '#2563eb', padding: '12px', fontWeight: 700 }}
              >
                {loading ? 'Creating Tenant Account...' : 'Complete Registration 🏠'}
              </button>
            </div>
          </form>
        )}

        <div style={{ textAlign: 'center', marginTop: '24px', color: 'var(--muted)', fontSize: '0.9rem' }}>
          Already registered?{' '}
          <Link to="/login" style={{ color: '#2563eb', fontWeight: 700, textDecoration: 'none' }}>
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}

export default TenantRegister
