import React from 'react'
import { Link, useNavigate } from 'react-router-dom'

interface RoleOption {
  id: string
  title: string
  badge: string
  description: string
  path: string
  icon: string
  highlights: string[]
  color: string
}

const ROLES: RoleOption[] = [
  {
    id: 'tenant',
    title: 'Tenant / Renter',
    badge: 'Fast & Free',
    description: 'Find your dream home, schedule verified in-person viewings, apply with Smart Match, and pay rent seamlessly.',
    path: '/register/tenant',
    icon: '🏠',
    highlights: [
      'Smart Match algorithm for rental budget & location',
      'Instant viewing bookings with calendar sync',
      'Digital lease signing & automated rent tracking'
    ],
    color: '#2563eb'
  },
  {
    id: 'owner',
    title: 'Property Owner / Landlord',
    badge: 'Full Control',
    description: 'List residential & commercial units, screen tenant applications, automate rent payouts, and manage multi-unit buildings.',
    path: '/register/owner',
    icon: '🏢',
    highlights: [
      'Building & unit portfolio management',
      'Tenant screening & one-click lease generation',
      'Real-time rent collection & financial insights'
    ],
    color: '#059669'
  },
  {
    id: 'agent',
    title: 'Real Estate Agent',
    badge: 'Grow Deals',
    description: 'Manage verified client listings, capture leads with smart CRM pipelines, coordinate showings, and close deals faster.',
    path: '/register/agent',
    icon: '🤝',
    highlights: [
      'Lead capture & automated follow-up CRM',
      'Dedicated agent profile & verified badge',
      'Commission tracking & client deal pipeline'
    ],
    color: '#7c3aed'
  },
  {
    id: 'provider',
    title: 'Service Contractor / Trade Partner',
    badge: 'Get Jobs',
    description: 'Receive assigned maintenance work orders, dispatch field technicians, submit quotes, and receive direct payments.',
    path: '/register/provider',
    icon: '🔧',
    highlights: [
      'Direct work order dispatches from owners/tenants',
      'Emergency maintenance requests & scheduling',
      'Service catalog & verified trade credentials'
    ],
    color: '#d97706'
  }
]

export const RoleSelector: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', padding: '40px 20px' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <Link to="/" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{
              background: 'linear-gradient(135deg, var(--accent), var(--accent-2))',
              color: '#fff',
              padding: '6px 12px',
              borderRadius: '8px',
              fontWeight: 800,
              fontSize: '16px'
            }}>
              PropNoxa
            </span>
          </Link>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent)', margin: '8px 0' }}>
            Join the PropNoxa Ecosystem
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: '1.05rem', maxWidth: '600px', margin: '0 auto' }}>
            Choose the account type that best matches your goals to access dedicated tools and specialized onboarding.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '24px',
          marginBottom: '40px'
        }}>
          {ROLES.map((role) => (
            <div
              key={role.id}
              onClick={() => navigate(role.path)}
              style={{
                background: 'var(--surface)',
                borderRadius: '16px',
                padding: '28px',
                boxShadow: 'var(--card-shadow)',
                border: '2px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)'
                e.currentTarget.style.borderColor = role.color
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'none'
                e.currentTarget.style.borderColor = 'transparent'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <span style={{ fontSize: '2.4rem' }}>{role.icon}</span>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '4px 10px',
                    borderRadius: '20px',
                    background: `${role.color}15`,
                    color: role.color
                  }}>
                    {role.badge}
                  </span>
                </div>

                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '8px' }}>
                  {role.title}
                </h2>
                <p style={{ color: 'var(--muted)', fontSize: '0.9rem', lineHeight: 1.5, marginBottom: '20px' }}>
                  {role.description}
                </p>

                <div style={{ borderTop: '1px solid var(--line)', paddingTop: '16px', marginBottom: '20px' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    What's Included:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {role.highlights.map((h, i) => (
                      <li key={i} style={{ fontSize: '0.85rem', color: '#334155' }}>
                        {h}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(role.path)
                }}
                style={{
                  width: '100%',
                  background: role.color,
                  color: '#fff',
                  border: 'none',
                  borderRadius: '10px',
                  padding: '12px',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  cursor: 'pointer',
                  transition: 'opacity 0.2s ease'
                }}
              >
                Register as {role.title.split('/')[0].trim()} &rarr;
              </button>
            </div>
          ))}
        </div>

        <div style={{ textAlign: 'center', color: 'var(--muted)', fontSize: '0.95rem' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--accent-2)', fontWeight: 700, textDecoration: 'none' }}>
            Sign In here
          </Link>
        </div>
      </div>
    </div>
  )
}

export default RoleSelector
