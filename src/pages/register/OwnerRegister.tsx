import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authService, OwnerRegistrationData } from '../../services/auth'
import { useAuth } from '../../hooks/useAuth'

export const OwnerRegister: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [step, setStep] = useState<1 | 2>(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<OwnerRegistrationData>({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    owner_type: 'individual',
    company_name: '',
    tax_pin: '',
    national_id_number: '',
    payout_phone: '',
    bank_name: '',
    bank_account_number: '',
    bank_account_name: '',
    emergency_contact: ''
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }))
  }

  const handleNextStep = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.email || !formData.password || !formData.full_name) {
      setError('Please fill in all required account credentials.')
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
      const res = await authService.registerOwner(formData)
      if (res?.access_token) {
        await login(formData.email, formData.password)
        navigate('/owner')
      } else {
        navigate('/login')
      }
    } catch (err: any) {
      setError(err?.message || 'Registration failed. Please check your credentials.')
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
              <span style={{ fontSize: '1.5rem' }}>🏢</span>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#059669', background: '#ecfdf5', padding: '2px 8px', borderRadius: '12px' }}>
                Property Owner / Landlord
              </span>
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent)', margin: 0 }}>
              Owner Registration
            </h1>
          </div>
          <Link to="/register" style={{ color: 'var(--muted)', textDecoration: 'none', fontSize: '0.9rem' }}>
            &larr; Switch Role
          </Link>
        </div>

        {/* Progress Bar */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '28px' }}>
          <div style={{ flex: 1, height: '6px', borderRadius: '4px', background: '#059669' }} />
          <div style={{ flex: 1, height: '6px', borderRadius: '4px', background: step === 2 ? '#059669' : 'var(--line)' }} />
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
              Step 1: Account Credentials
            </h2>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                Full Legal Name *
              </label>
              <input
                className="input"
                name="full_name"
                required
                placeholder="e.g. Samuel K. Mwangi"
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
                placeholder="samuel.mwangi@example.com"
                value={formData.email}
                onChange={handleChange}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Primary Phone Number *
                </label>
                <input
                  className="input"
                  name="phone"
                  required
                  placeholder="+254 700 123 456"
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
              style={{ marginTop: '12px', background: '#059669', padding: '12px', fontWeight: 700 }}
            >
              Continue to Ownership Profile &rarr;
            </button>
          </form>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent)', margin: 0 }}>
              Step 2: Property & Payout Credentials
            </h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.85rem', margin: '-8px 0 8px 0' }}>
              Used for verifying ownership documents and direct rent disbursement.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Ownership Entity
                </label>
                <select
                  className="input"
                  name="owner_type"
                  value={formData.owner_type || 'individual'}
                  onChange={handleChange}
                >
                  <option value="individual">Individual Landlord</option>
                  <option value="company">Limited Company / Enterprise</option>
                  <option value="trust">Family Trust / Estate</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Company Name (if applicable)
                </label>
                <input
                  className="input"
                  name="company_name"
                  placeholder="e.g. Apex Holdings Ltd"
                  value={formData.company_name || ''}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Tax PIN (KRA / Tax ID)
                </label>
                <input
                  className="input"
                  name="tax_pin"
                  placeholder="e.g. A012345678Z"
                  value={formData.tax_pin || ''}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  National ID / Passport #
                </label>
                <input
                  className="input"
                  name="national_id_number"
                  placeholder="e.g. 12345678"
                  value={formData.national_id_number || ''}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Bank Name
                </label>
                <input
                  className="input"
                  name="bank_name"
                  placeholder="e.g. Equity Bank, KCB"
                  value={formData.bank_name || ''}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Bank Account Number
                </label>
                <input
                  className="input"
                  name="bank_account_number"
                  placeholder="e.g. 0123456789"
                  value={formData.bank_account_number || ''}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  M-Pesa / Payout Phone
                </label>
                <input
                  className="input"
                  name="payout_phone"
                  placeholder="+254 700 123 456"
                  value={formData.payout_phone || ''}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '6px' }}>
                  Emergency Contact
                </label>
                <input
                  className="input"
                  name="emergency_contact"
                  placeholder="Name & Contact"
                  value={formData.emergency_contact || ''}
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
                style={{ flex: 2, background: '#059669', padding: '12px', fontWeight: 700 }}
              >
                {loading ? 'Creating Landlord Account...' : 'Complete Registration 🏢'}
              </button>
            </div>
          </form>
        )}

        <div style={{ textAlign: 'center', marginTop: '24px', color: 'var(--muted)', fontSize: '0.9rem' }}>
          Already registered?{' '}
          <Link to="/login" style={{ color: '#059669', fontWeight: 700, textDecoration: 'none' }}>
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}

export default OwnerRegister
